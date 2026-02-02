from __future__ import annotations

import io
import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal, Union, List

import numpy as np
import pandas as pd
import scanpy as sc
import matplotlib.pyplot as plt

from scodaviz import get_abbreviations, get_abbreviations_uni

# ============================================================
# Tool-friendly configs
# ============================================================
@dataclass
class UMAPEmbedConfig:
    """
    Compute-side parameters (Scanpy pipeline).

    Notes
    -----
    - cnv=True means: use separate key namespace (X_cnv_pca, X_cnv_umap, cnv_neighbors_info, ...)
      but the PCA/neighbors/UMAP computation still follows the same Scanpy pipeline as RNA branch.
    """
    use_coord: Literal["umap", "tsne"] = "umap"
    n_pcs: int = 15
    n_neighbors: int = 11
    clustering_res: float = 1.0
    cnv: bool = False
    n_top_genes: int = 2000


@dataclass
class UMAPPlotConfig:
    """Plot styling options."""
    ncols: int = 2
    figsize: Tuple[float, float] = (4, 4)
    wspace: float = 0.3
    hspace: float = 0.3
    legend_fontsize: int = 10
    palette: str = "Spectral"
    add_outline: bool = True
    vmax: Union[str, float] = "p99"
    vmin: Union[str, float] = 0


# ============================================================
# Internal helpers (keep original semantics)
# ============================================================
def _keys_for(cnv: bool, use_coord: str) -> Dict[str, str]:
    """Same key naming as your original code."""
    if cnv:
        return dict(
            pca_key="X_cnv_pca",
            embed_key=f"X_cnv_{use_coord}",
            neighbors_key="cnv_neighbors_info",
            distances_key="cnv_neighbor_graph_distance",
            connectivities_key="cnv_neighbor_graph_connectivity",
            cluster_key="cnv_cluster",
            sdi_col="cnv_cluster_diversity_index",
        )
    return dict(
        pca_key="X_pca",
        embed_key=f"X_{use_coord}",
        neighbors_key="neighbors_info",
        distances_key="neighbor_graph_distance",
        connectivities_key="neighbor_graph_connectivity",
        cluster_key="cluster",
        sdi_col="cluster_diversity_index",
    )


def _ensure_log1p_state(adata) -> None:
    """Original: if 'log1p' absent, normalize_total + log1p."""
    if "log1p" not in adata.uns:
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)


def _auto_tune_subset_params(
    n_obs: int,
    *,
    n_pcs: int,
    n_neighbors: int,
    mode: Literal["off", "safe", "aggressive"] = "safe",
) -> Tuple[int, int]:
    """
    Auto-tune compute params only when subset is requested.

    - off: keep user values
    - safe: mild adjustment
    - aggressive: more local structure
    """
    if mode == "off":
        return n_pcs, n_neighbors

    # clamp helpers
    def clip_int(x, lo, hi):
        return int(np.clip(int(round(x)), lo, hi))

    if mode == "safe":
        tuned_neighbors = clip_int(np.sqrt(n_obs), 6, 18)
        tuned_pcs = clip_int(max(10, n_obs // 60), 10, 35)
        return tuned_pcs, tuned_neighbors

    # aggressive
    tuned_neighbors = clip_int(np.sqrt(n_obs) * 0.8, 5, 15)
    tuned_pcs = clip_int(max(12, n_obs // 80), 12, 30)
    return tuned_pcs, tuned_neighbors


def _subset_adata(adata_t, targets: Optional[Dict[str, Any]]) -> Optional[Any]:
    """
    targets schema: {"obs_col": str, "value": Any}
    """
    if targets is None:
        return adata_t[:, :].copy()

    if not (isinstance(targets, dict) and "obs_col" in targets and "value" in targets):
        return None

    obs_col = str(targets["obs_col"])
    value = targets["value"]

    if obs_col not in adata_t.obs:
        return None
    if value not in list(adata_t.obs[obs_col].unique()):
        return None

    b = adata_t.obs[obs_col] == value
    return adata_t[b, :].copy()


def _abbrev_celltypes_inplace(adata, full_name: bool) -> None:
    if full_name:
        return
    ren = get_abbreviations_uni()
    for col in ["celltype_major", "celltype_minor", "celltype_subset"]:
        if col in adata.obs:
            adata.obs[col] = adata.obs[col].astype(str)
            # adata.obs[col].replace(ren.get(col, {}), inplace=True)
            adata.obs[col].replace(ren, inplace=True)


def _final_items_to_plot(adata, items_to_plot: Sequence[str]) -> List[str]:
    """Match original behavior: genes first, then obs items; ensure log1p if genes exist."""
    genes_all = set(map(str, adata.var_names))
    obs_all = set(map(str, adata.obs.columns))

    genes, obs_items = [], []
    for item in items_to_plot:
        if item in obs_all:
            obs_items.append(item)
            if pd.api.types.is_bool_dtype(adata.obs[item]):
                adata.obs[item] = adata.obs[item].astype(str)
        elif item in genes_all:
            genes.append(item)

    if genes:
        _ensure_log1p_state(adata)

    return genes + obs_items


def _maybe_cast_numeric_str(x):
    if x is None:
        return None
    if isinstance(x, str):
        s = x.strip()
        try:
            return float(s)
        except ValueError:
            return s
    return x

# ============================================================
# Main function (preserve original compute flow)
# ============================================================
def plot_umap(
    adata_t,
    *,
    items_to_plot: Sequence[str] = ("condition", "celltype_major", "celltype_minor", "celltype_subset", "ploidy_dec", "sample"),
    targets: Optional[Dict[str, Any]] = None,
    full_name: bool = False,
    embed_cfg: Optional[UMAPEmbedConfig] = None,
    plot_cfg: Optional[UMAPPlotConfig] = None,
    auto_tune_subset: Literal["off", "safe", "aggressive"] = "off",
    cache_full_to_parent: bool = True,
    force_recompute_full: bool = False,
):
    """
    Tool-friendly rewrite of your original plot_umap, preserving Scanpy compute semantics.

    HARD RULES (matches your intent)
    -------------------------------
    - Full data (targets=None):
        * If embedding exists in adata_t.obsm[embed_key] and force_recompute_full=False -> reuse.
        * Else compute PCA->neighbors->UMAP/TSNE using Scanpy on a working copy,
          then (optionally) cache pca/graphs/embedding back into adata_t.

    - Subset (targets!=None):
        * ALWAYS recompute from normalize/log1p -> HVG -> PCA -> neighbors -> embedding (fresh coordinates).
        * NEVER cache subset graphs/embeddings back into adata_t (shape mismatch).

    cnv flag behavior
    -----------------
    cnv=True only changes the key namespace (X_cnv_pca, X_cnv_umap, cnv_neighbors_info, ...).
    The compute pipeline is still Scanpy on adata.X (normalize/log1p + HVG + PCA + neighbors + UMAP/TSNE),
    exactly like your original function.

    Parameters
    ----------
    targets : dict, optional
        {"obs_col": <obs col>, "value": <value>} for subsetting.
    auto_tune_subset : {"off","safe","aggressive"}
        If subset is used, optionally auto-adjust n_pcs/n_neighbors based on subset size.

    Returns
    -------
    dict or None
        Metadata dict for downstream logging/tests; None if invalid targets.
    """
    embed_cfg = embed_cfg or UMAPEmbedConfig()
    plot_cfg = plot_cfg or UMAPPlotConfig()

    keys = _keys_for(embed_cfg.cnv, embed_cfg.use_coord)
    pca_key = keys["pca_key"]
    embed_key = keys["embed_key"]
    neighbors_key = keys["neighbors_key"]
    distances_key = keys["distances_key"]
    connectivities_key = keys["connectivities_key"]
    cluster_key = keys["cluster_key"]

    # CNV branch: match original res scaling
    clustering_res = float(embed_cfg.clustering_res * (4.0 if embed_cfg.cnv else 1.0))

    # -------------------------
    # SUBSET OR FULL WORK DATA
    # -------------------------
    adata = _subset_adata(adata_t, targets)
    if adata is None:
        err_msg = (f"❌ERROR: targets {targets} seems not properly defined.")
        return err_msg

    is_subset = targets is not None

    # =========================================================
    # FULL DATA PATH: reuse/cache like original
    # =========================================================
    if not is_subset:
        # if embedding exists and no force -> reuse
        if (embed_key in adata_t.obsm) and (not force_recompute_full):
            pass
        else:
            # compute on a working copy (adata already is a copy of full)
            # PCA (only if missing on working)
            if pca_key not in adata.obsm:
                _ensure_log1p_state(adata)
                sc.pp.highly_variable_genes(adata, n_top_genes=int(embed_cfg.n_top_genes))
                try:
                    sc.tl.pca(adata, n_comps=int(embed_cfg.n_pcs), mask_var="variable_genes")
                except Exception:
                    sc.tl.pca(adata, n_comps=int(embed_cfg.n_pcs), use_highly_variable=True)

                # Cache PCA back to parent (as original)
                if cache_full_to_parent:
                    adata_t.obsm[pca_key] = adata.obsm[pca_key]

            # neighbors: reuse if parent has valid graph, else compute
            b_pass = False
            if neighbors_key in adata_t.uns:
                u = adata_t.uns[neighbors_key]
                ck = u.get("connectivities_key", None)
                dk = u.get("distances_key", None)
                if (ck in adata_t.obsp) and (dk in adata_t.obsp):
                    b_pass = True

            if not b_pass:
                n_pcs_eff = adata.obsm[pca_key].shape[1]
                sc.pp.neighbors(
                    adata,
                    n_neighbors=int(embed_cfg.n_neighbors),
                    n_pcs=n_pcs_eff,
                    use_rep=pca_key,
                    key_added=neighbors_key,
                )

                d_key = adata.uns[neighbors_key]["distances_key"]
                c_key = adata.uns[neighbors_key]["connectivities_key"]

                if distances_key != d_key:
                    adata.obsp[distances_key] = adata.obsp[d_key]
                    adata.uns[neighbors_key]["distances_key"] = distances_key
                    del adata.obsp[d_key]

                if connectivities_key != c_key:
                    adata.obsp[connectivities_key] = adata.obsp[c_key]
                    adata.uns[neighbors_key]["connectivities_key"] = connectivities_key  # ✅ bugfix
                    del adata.obsp[c_key]

                if cache_full_to_parent:
                    adata_t.obsp[distances_key] = adata.obsp[distances_key]
                    adata_t.obsp[connectivities_key] = adata.obsp[connectivities_key]
                    adata_t.uns[neighbors_key] = adata.uns[neighbors_key]

            # embedding (always compute then cache)
            if embed_cfg.use_coord == "tsne":
                adata_tmp = sc.tl.tsne(adata, neighbors_key=neighbors_key, copy=True)
                if cache_full_to_parent:
                    adata_t.obsm[embed_key] = adata_tmp.obsm["X_tsne"]
            else:
                adata_tmp = sc.tl.umap(adata, neighbors_key=neighbors_key, copy=True)
                if cache_full_to_parent:
                    adata_t.obsm[embed_key] = adata_tmp.obsm["X_umap"]

        # leiden on parent if missing (original behavior)
        if cluster_key not in adata_t.obs:
            sc.tl.leiden(
                adata_t,
                resolution=clustering_res,
                key_added=cluster_key,
                neighbors_key=neighbors_key,
            )

        # plotting uses fresh full copy (original end-of-full)
        adata = adata_t[:, :].copy()

    # =========================================================
    # SUBSET PATH: ALWAYS recompute from log1p->PCA->neighbors->UMAP
    # =========================================================
    else:
        # auto-tune only on subset
        n_pcs, n_neighbors = _auto_tune_subset_params(
            adata.n_obs,
            n_pcs=int(embed_cfg.n_pcs),
            n_neighbors=int(embed_cfg.n_neighbors),
            mode=auto_tune_subset,
        )

        # recompute pipeline (exactly your subset branch)
        _ensure_log1p_state(adata)
        sc.pp.highly_variable_genes(adata, n_top_genes=int(embed_cfg.n_top_genes))
        try:
            sc.tl.pca(adata, n_comps=int(n_pcs), mask_var="variable_genes")
        except Exception:
            sc.tl.pca(adata, n_comps=int(n_pcs), use_highly_variable=True)

        n_pcs_eff = adata.obsm[pca_key].shape[1]
        sc.pp.neighbors(
            adata,
            n_neighbors=int(n_neighbors),
            n_pcs=n_pcs_eff,
            use_rep=pca_key,
            key_added=neighbors_key,
        )

        # (subset branch: no renaming/caching needed; still keep canonical rename for consistency)
        d_key = adata.uns[neighbors_key]["distances_key"]
        c_key = adata.uns[neighbors_key]["connectivities_key"]

        if distances_key != d_key:
            adata.obsp[distances_key] = adata.obsp[d_key]
            adata.uns[neighbors_key]["distances_key"] = distances_key
            del adata.obsp[d_key]

        if connectivities_key != c_key:
            adata.obsp[connectivities_key] = adata.obsp[c_key]
            adata.uns[neighbors_key]["connectivities_key"] = connectivities_key
            del adata.obsp[c_key]

        if embed_cfg.use_coord == "tsne":
            adata_tmp = sc.tl.tsne(adata, neighbors_key=neighbors_key, copy=True)
            adata.obsm[embed_key] = adata_tmp.obsm["X_tsne"]
        else:
            adata_tmp = sc.tl.umap(adata, neighbors_key=neighbors_key, copy=True)
            adata.obsm[embed_key] = adata_tmp.obsm["X_umap"]

        sc.tl.leiden(
            adata,
            resolution=clustering_res,
            key_added=cluster_key,
            neighbors_key=neighbors_key,
        )

    # -------------------------
    # Cosmetics + plot
    # -------------------------
    _abbrev_celltypes_inplace(adata, full_name=full_name)
    items_final = _final_items_to_plot(adata, items_to_plot)

    if plot_cfg is not None:
        if hasattr(plot_cfg, "vmin"):
            plot_cfg.vmin = _maybe_cast_numeric_str(plot_cfg.vmin)
        if hasattr(plot_cfg, "vmax"):
            plot_cfg.vmax = _maybe_cast_numeric_str(plot_cfg.vmax)
        
    plt.rcParams["figure.figsize"] = plot_cfg.figsize
    ax = sc.pl.embedding(
        adata,
        basis=embed_key,
        neighbors_key=neighbors_key,
        color=items_final,
        wspace=plot_cfg.wspace,
        hspace=plot_cfg.hspace,
        legend_fontsize=plot_cfg.legend_fontsize,
        ncols=plot_cfg.ncols,
        palette=plot_cfg.palette,
        add_outline=plot_cfg.add_outline,
        vmax=plot_cfg.vmax,
        vmin=plot_cfg.vmin,
        show=False,
    )
    
    # 1. 현재 활성화된 전체 Figure 객체를 가져옵니다.
    fig = plt.gcf() 
    
    # 2. 메모리에 저장할 버퍼 생성
    buf = io.BytesIO()
    
    # 3. 버퍼에 저장 (scanpy heatmap은 bbox_inches='tight'가 거의 필수입니다)
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    
    # 4. Base64 인코딩
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    # 5. 화면에 그림 출력 (plt.close 하기 전에 수행)
    plt.show() 
    
    # 6. (선택사항) 화면 출력 후 메모리 정리
    # 주피터 환경이라면 보통 plt.show()가 끝나면 자동으로 정리되지만, 
    # 명시적으로 닫고 싶다면 여기서 닫습니다.
    plt.close(fig) 

    return dict(
        subset=None if not is_subset else dict(obs_col=targets["obs_col"], value=targets["value"]),
        cnv=embed_cfg.cnv,
        embed_key=embed_key,
        pca_key=pca_key,
        neighbors_key=neighbors_key,
        items_plotted=items_final,
        auto_tune_subset=auto_tune_subset,
        used_params=dict(
            n_pcs=int(embed_cfg.n_pcs) if not is_subset else int(n_pcs),
            n_neighbors=int(embed_cfg.n_neighbors) if not is_subset else int(n_neighbors),
            clustering_res=clustering_res,
        ),
        cached_full_to_parent=bool((not is_subset) and cache_full_to_parent),
        img_base64=img_base64,
        images=img_base64
    )

def_plot_umap = '''
@dataclass
class UMAPEmbedConfig:
    """
    Compute-side parameters (Scanpy pipeline).

    Notes
    -----
    - cnv=True means: use separate key namespace (X_cnv_pca, X_cnv_umap, cnv_neighbors_info, ...)
      but the PCA/neighbors/UMAP computation still follows the same Scanpy pipeline as RNA branch.
    """
    use_coord: Literal["umap", "tsne"] = "umap"
    n_pcs: int = 15
    n_neighbors: int = 11
    clustering_res: float = 1.0
    cnv: bool = False
    n_top_genes: int = 2000


@dataclass
class UMAPPlotConfig:
    """Plot styling options."""
    ncols: int = 2
    figsize: Tuple[float, float] = (4, 4)
    wspace: float = 0.3
    hspace: float = 0.3
    legend_fontsize: int = 10
    palette: str = "Spectral"
    add_outline: bool = True
    vmax: Union[str, float] = "p99"
    vmin: Union[str, float] = 0

# ============================================================
# Main function (preserve original compute flow)
# ============================================================
def plot_umap(
    adata_t,
    *,
    items_to_plot: Sequence[str] = ("condition", "celltype_major", "celltype_minor", "celltype_subset", "ploidy_dec", "sample"),
    targets: Optional[Dict[str, Any]] = None,
    full_name: bool = False,
    embed_cfg: Optional[UMAPEmbedConfig] = None,
    plot_cfg: Optional[UMAPPlotConfig] = None,
    auto_tune_subset: Literal["off", "safe", "aggressive"] = "off",
    cache_full_to_parent: bool = True,
    force_recompute_full: bool = False,
):
    """
    Short description: UMAP/t-SNE visualization, either based on gene-expression (X, default) or based on CNV (X_cnv).
    
    Tool-friendly rewrite of your original plot_umap, preserving Scanpy compute semantics.

    HARD RULES (matches your intent)
    -------------------------------
    - Full data (targets=None):
        * If embedding exists in adata_t.obsm[embed_key] and force_recompute_full=False -> reuse.
        * Else compute PCA->neighbors->UMAP/TSNE using Scanpy on a working copy,
          then (optionally) cache pca/graphs/embedding back into adata_t.

    - Subset (targets!=None):
        * ALWAYS recompute from normalize/log1p -> HVG -> PCA -> neighbors -> embedding (fresh coordinates).
        * NEVER cache subset graphs/embeddings back into adata_t (shape mismatch).

    cnv flag behavior
    -----------------
    cnv=True only changes the key namespace (X_cnv_pca, X_cnv_umap, cnv_neighbors_info, ...).
    The compute pipeline is still Scanpy on adata.X (normalize/log1p + HVG + PCA + neighbors + UMAP/TSNE),
    exactly like your original function.

    Parameters
    ----------
    targets : dict, optional
        {"obs_col": <obs col>, "value": <value>} for subsetting.
    auto_tune_subset : {"off","safe","aggressive"}
        If subset is used, optionally auto-adjust n_pcs/n_neighbors based on subset size.

    Returns
    -------
    dict or None
        Metadata dict for downstream logging/tests; None if invalid targets.
    """
    
    """ Some Code"""
    
    return dict(
        subset=None if not is_subset else dict(obs_col=targets["obs_col"], value=targets["value"]),
        cnv=embed_cfg.cnv,
        embed_key=embed_key,
        pca_key=pca_key,
        neighbors_key=neighbors_key,
        items_plotted=items_final,
        auto_tune_subset=auto_tune_subset,
        used_params=dict(
            n_pcs=int(embed_cfg.n_pcs) if not is_subset else int(n_pcs),
            n_neighbors=int(embed_cfg.n_neighbors) if not is_subset else int(n_neighbors),
            clustering_res=clustering_res,
        ),
        cached_full_to_parent=bool((not is_subset) and cache_full_to_parent),
        img_base64=img_base64,
        images=img_base64
    )
'''


# ============================================================
# UMAP JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_UMAP = {
    "type": "object",
    "properties": {
        "items_to_plot": {
            "type": "array",
            "items": {"type": "string"},
            "description": "UMAP/TSNE 상에 시각화할 항목들. adata.obs 컬럼명 또는 adata.var gene symbol.",
        },
        "targets": {
            "type": "object",
            "properties": {
                "obs_col": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["obs_col", "value"],
            "description": "특정 obs 조건으로 subset 후 임베딩을 새로 계산할 때 사용. 필요 없으면 키를 생략.",
        },
        "embed_cfg": {
            "type": "object",
            "properties": {
                "use_coord": {"type": "string", "enum": ["umap", "tsne"]},
                "n_pcs": {"type": "integer"},
                "n_neighbors": {"type": "integer"},
                "clustering_res": {"type": "number"},
                "cnv": {"type": "boolean"},
                "n_top_genes": {"type": "integer"},
            },
            "description": "Compute 파라미터. 생략하면 @dataclass 기본값 사용.",
        },
        "plot_cfg": {
            "type": "object",
            "properties": {
                "ncols": {"type": "integer"},
                "figsize": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                "wspace": {"type": "number"},
                "hspace": {"type": "number"},
                "legend_fontsize": {"type": "integer"},
                "palette": {"type": "string"},
                "add_outline": {"type": "boolean"},
                "vmax": {
                    "type": "string",
                    "description": "scanpy vmax. 예: 'p99' 또는 숫자 문자열 '1.5'. 필요 없으면 생략.",
                },
                "vmin": {
                    "type": "string",
                    "description": "scanpy vmin. 예: '0' 또는 'p1'. 필요 없으면 생략.",
                },
            },
            "description": "Plot 파라미터. 생략하면 @dataclass 기본값 사용.",
        },
        "full_name": {"type": "boolean"},
        "auto_tune_subset": {"type": "string", "enum": ["off", "safe", "aggressive"]},
        "cache_full_to_parent": {"type": "boolean"},
        "force_recompute_full": {"type": "boolean"},
    },
}
