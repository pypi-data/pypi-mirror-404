from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal, Union

import numpy as np
import pandas as pd
import scanpy as sc

from scodaviz import get_sample_to_group_map, get_gene_expression_mean, test_group_diff, plot_violin


# ============================================================
# Small structured inputs (shared pattern)
# ============================================================
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="celltype_minor", value="Macrophage")
    """
    obs_col: str
    value: Any


@dataclass
class SignifTestConfig:
    """
    Configuration for group-difference significance testing.

    Notes
    -----
    This config is passed to `test_group_diff(df, ref_group=..., pval_cutoff=...)`.
    """
    ref_group: Optional[str] = None
    pval_cutoff: float = 0.1


@dataclass
class GeneSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `genes_to_plot` is provided (non-empty): plot those genes (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression, keyword_match="exact" is usually best.
    """
    max_n_genes_to_plot: int = 8
    genes_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "exact"


@dataclass
class ViolinPlotStyle:
    """
    Style options forwarded to `plot_violin` (scodaviz).

    Notes
    -----
    Keep this compact for tool-calling. Prefer presets if you later want more styles.
    """
    # core layout
    ncols: int = 3
    figsize: Tuple[float, float] = (2.5, 2.0)
    dpi: int = 100
    wspace: float = 0.2
    hspace: float = 0.3

    # violin aesthetics
    scale: Literal["area", "count", "width"] = "width"
    inner: Optional[str] = "box"
    width: float = 0.9
    linewidth: float = 0.3
    bw: Union[str, float] = "scott"

    # labeling
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_fontsize: int = 14
    title_y_pos: float = 1.0
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 45
    xtick_ha: Literal["right", "left", "center"] = "right"

    # coloring
    cmap: str = "tab10"


# ============================================================
# Small helpers
# ============================================================
'''
def _coerce_test_cfg(x: Any) -> SignifTestConfig:
    """Accept None / dict / SignifTestConfig and return SignifTestConfig."""
    if x is None:
        return SignifTestConfig()
    if isinstance(x, SignifTestConfig):
        return x
    if isinstance(x, dict):
        return SignifTestConfig(
            ref_group=x.get("ref_group", None),
            pval_cutoff=float(x.get("pval_cutoff", 0.1)),
        )
    raise TypeError(f"test_cfg must be None, dict, or SignifTestConfig. Got: {type(x)}")
'''
def _coerce_test_cfg(x: Any):
    if x is None:
        return SignifTestConfig()

    if isinstance(x, SignifTestConfig):
        return x

    if isinstance(x, dict):
        return SignifTestConfig(
            ref_group=x.get("ref_group", None),
            pval_cutoff=float(x.get("pval_cutoff", 0.1)),
        )

    # ✅ duck-typing: 다른 모듈의 SignifTestConfig도 허용
    if hasattr(x, "ref_group") and hasattr(x, "pval_cutoff"):
        return SignifTestConfig(
            ref_group=getattr(x, "ref_group", None),
            pval_cutoff=float(getattr(x, "pval_cutoff", 0.1)),
        )

    raise TypeError(f"test_cfg must be None, dict, or SignifTestConfig-like. Got: {type(x)}")

    
def _subset_by_obs_filter(adata_t, obs_filter: Optional[ObsFilter]):
    if obs_filter is None:
        return adata_t[:, :].copy()
    if obs_filter.obs_col not in adata_t.obs:
        return None
    vals = adata_t.obs[obs_filter.obs_col].unique().tolist()
    if obs_filter.value not in vals:
        return None
    b = adata_t.obs[obs_filter.obs_col] == obs_filter.value
    return adata_t[b, :].copy()


def _select_features_from_dfres(
    df_res: pd.DataFrame,
    *,
    select_cfg: GeneSelectConfig,
) -> Sequence[str]:
    """
    df_res index must be feature ids (genes).
    """
    all_items = df_res.index.astype(str).tolist()

    # 1) explicit genes_to_plot
    if select_cfg.genes_to_plot:
        return [x for x in select_cfg.genes_to_plot if x in all_items]

    # 2) keywords
    if select_cfg.target_keywords:
        out: list[str] = []
        if select_cfg.keyword_match == "exact":
            s = set(all_items)
            for k in select_cfg.target_keywords:
                if k in s:
                    out.append(k)
        else:
            # contains
            for item in all_items:
                for k in select_cfg.target_keywords:
                    if k in item:
                        out.append(item)
                        break
        # keep original order but unique
        seen = set()
        uniq = []
        for x in out:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
        return uniq

    # 3) top-N
    n = min(select_cfg.max_n_genes_to_plot, len(all_items))
    return all_items[:n]


# ============================================================
# Tool-friendly wrapper: violin for gene expression
# ============================================================
def plot_violin_for_gene_expression_with_signif_difference(
    adata_t,
    *,
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    obs_group_col: str = "condition",
    group_col_out: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[GeneSelectConfig] = None,
    style: Optional[ViolinPlotStyle] = None,
) -> Dict[str, Any]:
    """
    Plot violin plots of (log1p-normalized) gene expression across groups, focusing on
    statistically different genes (based on sample-mean testing) or user-selected genes.

    This follows the same “tool-schema friendly” structure as your box-plot wrappers:
    - optional subset filtering via `targets={"obs_col":..., "value":...}`
    - normalize_total + log1p on the working copy (subset always recomputed)
    - compute sample-mean table via `get_gene_expression_mean(..., group_col="sample")`
    - run `test_group_diff` on that table to get p-values
    - select features (genes) via `GeneSelectConfig`
    - plot single-cell expression violins (adata[:, genes].to_df()) grouped by `obs_group_col`

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData. Must contain `obs["sample"]` and `obs[obs_group_col]` (default "condition").
    target_genes : Sequence[str], optional
        Convenience keyword list. If `select_cfg.genes_to_plot` is empty, these are used as
        `select_cfg.target_keywords` with keyword_match="exact" by default.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"celltype_minor","value":"Macrophage"}.
    obs_group_col : str, default "condition"
        Group label column in `adata.obs` for the violin plot x-axis.
    group_col_out : str, default "Group"
        Group label column name used in the temporary plotting DataFrame.
    test_cfg : SignifTestConfig, optional
        Config for significance testing on sample-mean table.
    select_cfg : GeneSelectConfig, optional
        Config to decide which genes to plot.
    style : ViolinPlotStyle, optional
        Plot style forwarded to `plot_violin`.

    Returns
    -------
    dict
        {
          "subset": {"obs_col":..., "value":...} or None,
          "genes_plotted": [...],
          "df_test": <DataFrame from test_group_diff>,
          "warnings": [...],
        }

    Examples
    --------
    # 1) 지정 유전자만 정확히 violin 확인 (subset 없이)
    out = plot_violin_for_gene_expression_with_signif_difference(
        adata,
        target_genes=["ERBB2", "ESR1", "MKI67"],
        test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    )

    # 2) subset(대식세포)에서 p-value 기준 상위 6개 자동 선택
    out = plot_violin_for_gene_expression_with_signif_difference(
        adata,
        targets={"obs_col":"celltype_minor","value":"Macrophage"},
        test_cfg=SignifTestConfig(ref_group=None, pval_cutoff=0.1),
        select_cfg=GeneSelectConfig(max_n_genes_to_plot=6),
    )
    """
    test_cfg = test_cfg or SignifTestConfig()
    style = style or ViolinPlotStyle()

    # If user passed target_genes but didn't pass select_cfg, use as keywords (exact)
    if select_cfg is None:
        select_cfg = GeneSelectConfig(
            max_n_genes_to_plot=8,
            genes_to_plot=(),
            target_keywords=tuple(target_genes) if target_genes else (),
            keyword_match="exact",
        )
    else:
        # if select_cfg has no genes_to_plot/keywords, fall back to target_genes
        if (not select_cfg.genes_to_plot) and (not select_cfg.target_keywords) and target_genes:
            select_cfg.target_keywords = tuple(target_genes)
            # keep user keyword_match as-is

    warnings: list[str] = []

    # Parse targets dict -> ObsFilter
    obs_filter = None
    if targets is not None:
        if isinstance(targets, dict) and ("obs_col" in targets) and ("value" in targets):
            obs_filter = ObsFilter(obs_col=str(targets["obs_col"]), value=targets["value"])
        else:
            warnings.append(f"targets must be dict with keys {{'obs_col','value'}}. Got: {targets}")
            return {"subset": None, "genes_plotted": [], "df_test": None, "warnings": warnings}

    # Subset
    adata_s = _subset_by_obs_filter(adata_t, obs_filter)
    if adata_s is None:
        warnings.append(f"Invalid targets: {targets}")
        return {"subset": None, "genes_plotted": [], "df_test": None, "warnings": warnings}

    # Ensure required obs cols
    if "sample" not in adata_s.obs:
        warnings.append("adata.obs['sample'] not found.")
        return {"subset": None, "genes_plotted": [], "df_test": None, "warnings": warnings}
    if obs_group_col not in adata_s.obs:
        warnings.append(f"adata.obs['{obs_group_col}'] not found.")
        return {"subset": None, "genes_plotted": [], "df_test": None, "warnings": warnings}

    # Normalize + log1p on subset copy (important since adata.X is raw count)
    sc.pp.normalize_total(adata_s, target_sum=1e4)
    sc.pp.log1p(adata_s)

    # Compute sample-mean table for testing (like your original)
    genes_all = adata_s.var.index.values.tolist()
    exists = []
    not_exists = []
    for g in list(target_genes):
        if g in genes_all:
            exists.append(g)
        else:
            not_exists.append(g)
    target_genes = exists

    if (len(not_exists) > 0):
        print(f'⚠️ WARNING: Gene(s) {not_exists} not present in the data.')
    
    df_mean = get_gene_expression_mean(
        adata_s,
        genes=list(target_genes) if target_genes else [],
        group_col="sample",
        nz_pct=True,
    )

    # test_group_diff expects group labels; ensure group column exists as `Group`
    # Your pipeline typically already includes df['Group'], but just in case:
    if "Group" not in df_mean.columns:
        try:
            sample_to_group = get_sample_to_group_map(adata_s, group_col=obs_group_col, sample_col="sample")
            df_mean["Group"] = df_mean["sample"].map(sample_to_group) if "sample" in df_mean.columns else df_mean.index.map(sample_to_group)
        except Exception:
            # last resort: use first obs per sample
            tmp = adata_s.obs[["sample", obs_group_col]].drop_duplicates("sample")
            mp = dict(zip(tmp["sample"].astype(str), tmp[obs_group_col].astype(str)))
            if "sample" in df_mean.columns:
                df_mean["Group"] = df_mean["sample"].astype(str).map(mp)
            else:
                df_mean["Group"] = pd.Series(df_mean.index.astype(str)).map(mp).values

    test_cfg = _coerce_test_cfg(test_cfg)
    
    # Significance test table
    df_res = test_group_diff(df_mean, ref_group=test_cfg.ref_group, pval_cutoff=test_cfg.pval_cutoff)
    
    if df_res is None or getattr(df_res, "shape", (0, 0))[0] == 0:
        warnings.append("test_group_diff returned empty result.")
        return {
            "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
            "genes_plotted": [],
            "df_test": df_res,
            "warnings": warnings,
        }

    # Select genes to plot (based on df_res index)
    genes_to_plot = list(_select_features_from_dfres(df_res, select_cfg=select_cfg))
    # Intersect with actual genes present in adata
    genes_present = set(map(str, adata_s.var_names))
    genes_to_plot = [g for g in genes_to_plot if g in genes_present]

    if not genes_to_plot:
        warnings.append("No genes selected for plotting after intersection with adata.var_names.")
        return {
            "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
            "genes_plotted": [],
            "df_test": df_res,
            "warnings": warnings,
        }

    # Build single-cell expression dataframe for violins
    df_plot = adata_s[:, genes_to_plot].to_df()
    df_plot[group_col_out] = adata_s.obs[obs_group_col].astype(str).values

    # Plot
    ax = plot_violin(
        df_plot,
        genes_lst=genes_to_plot,
        group_col=group_col_out,
        scale=style.scale,
        group_order=style.group_order,
        inner=style.inner,
        width=style.width,
        linewidth=style.linewidth,
        bw=style.bw,
        figsize=style.figsize,
        dpi=style.dpi,
        text_fs=style.tick_fontsize,  # scodaviz uses text_fs; align with tick size
        title=style.title,
        title_fs=style.title_fontsize,
        title_y_pos=style.title_y_pos,
        label_fs=style.label_fontsize,
        tick_fs=style.tick_fontsize,
        xtick_rot=style.xtick_rotation,
        xtick_ha=style.xtick_ha,
        ncols=style.ncols,
        wspace=style.wspace,
        hspace=style.hspace,
        cmap=style.cmap,
    )

    return {
        "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
        "genes_plotted": genes_to_plot,
        "df_test": df_res,
        "warnings": warnings,
        "img_base64": ax,
        "images": ax,  
    }

# ============================================================
# Function definition 
# ============================================================
def_plot_violin_for_gene_expression_with_signif_difference = '''
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="celltype_minor", value="Macrophage")
    """
    obs_col: str
    value: Any


@dataclass
class SignifTestConfig:
    """
    Configuration for group-difference significance testing.

    Notes
    -----
    This config is passed to `test_group_diff(df, ref_group=..., pval_cutoff=...)`.
    """
    ref_group: Optional[str] = None
    pval_cutoff: float = 0.1


@dataclass
class GeneSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `genes_to_plot` is provided (non-empty): plot those genes (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression, keyword_match="exact" is usually best.
    """
    max_n_genes_to_plot: int = 8
    genes_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "exact"


@dataclass
class ViolinPlotStyle:
    """
    Style options forwarded to `plot_violin` (scodaviz).

    Notes
    -----
    Keep this compact for tool-calling. Prefer presets if you later want more styles.
    """
    # core layout
    ncols: int = 3
    figsize: Tuple[float, float] = (2.5, 2.0)
    dpi: int = 100
    wspace: float = 0.2
    hspace: float = 0.3

    # violin aesthetics
    scale: Literal["area", "count", "width"] = "width"
    inner: Optional[str] = "box"
    width: float = 0.9
    linewidth: float = 0.3
    bw: Union[str, float] = "scott"

    # labeling
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_fontsize: int = 14
    title_y_pos: float = 1.0
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 45
    xtick_ha: Literal["right", "left", "center"] = "right"

    # coloring
    cmap: str = "tab10"


def plot_violin_for_gene_expression_with_signif_difference(
    adata_t,
    *,
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    obs_group_col: str = "condition",
    group_col_out: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[GeneSelectConfig] = None,
    style: Optional[ViolinPlotStyle] = None,
) -> Dict[str, Any]:
    """
    Short description: Violin plots of gene expression across groups, for user-selected genes (target_genes) or statistically different genes (based on sample-mean testing).

    This follows the same “tool-schema friendly” structure as your box-plot wrappers:
    - optional subset filtering via `targets={"obs_col":..., "value":...}`
    - normalize_total + log1p on the working copy (subset always recomputed)
    - compute sample-mean table via `get_gene_expression_mean(..., group_col="sample")`
    - run `test_group_diff` on that table to get p-values
    - select features (genes) via `GeneSelectConfig`
    - plot single-cell expression violins (adata[:, genes].to_df()) grouped by `obs_group_col`

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData. Must contain `obs["sample"]` and `obs[obs_group_col]` (default "condition").
    target_genes : Sequence[str], optional
        Convenience keyword list. If `select_cfg.genes_to_plot` is empty, these are used as
        `select_cfg.target_keywords` with keyword_match="exact" by default.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"celltype_minor","value":"Macrophage"}.
    obs_group_col : str, default "condition"
        Group label column in `adata.obs` for the violin plot x-axis.
    group_col_out : str, default "Group"
        Group label column name used in the temporary plotting DataFrame.
    test_cfg : SignifTestConfig, optional
        Config for significance testing on sample-mean table.
    select_cfg : GeneSelectConfig, optional
        Config to decide which genes to plot.
    style : ViolinPlotStyle, optional
        Plot style forwarded to `plot_violin`.

    Returns
    -------
    dict
        {
          "subset": {"obs_col":..., "value":...} or None,
          "genes_plotted": [...],
          "df_test": <DataFrame from test_group_diff>,
          "warnings": [...],
        }

    Examples
    --------
    # 1) 지정 유전자만 정확히 violin 확인 (subset 없이)
    out = plot_violin_for_gene_expression_with_signif_difference(
        adata,
        target_genes=["ERBB2", "ESR1", "MKI67"],
        test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    )

    # 2) subset(대식세포)에서 p-value 기준 상위 6개 자동 선택
    out = plot_violin_for_gene_expression_with_signif_difference(
        adata,
        targets={"obs_col":"celltype_minor","value":"Macrophage"},
        test_cfg=SignifTestConfig(ref_group=None, pval_cutoff=0.1),
        select_cfg=GeneSelectConfig(max_n_genes_to_plot=6),
    )
    """
    
    """ Some Code"""
    
    return {
        "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
        "genes_plotted": genes_to_plot,
        "df_test": df_res,
        "warnings": warnings,
        "img_base64": ax,
    }
'''

# ============================================================
# Violin JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_VIOLIN = {
    "type": "object",
    "properties": {
        # 1. 함수 인자에 직접 있는 변수들 추가
        "target_genes": {
            "type": "array", 
            "items": {"type": "string"}, 
            "default": [],
            "description": "분석하고자 하는 유전자 리스트 (예: ['GAPDH', 'CD3E'])"
        },
        "obs_group_col": {
            "type": "string", 
            "default": "condition",
            "description": "Violin x축 기준이 되는 obs 컬럼"
        },
        "targets": {
            "type": "object",
            "nullable": True,
            "properties": {
                "obs_col": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["obs_col", "value"],
            "description": "데이터 서브셋 필터"
        },
        # 2. Config 객체들 (Nested Objects)
        "test_cfg": {
            "type": "object",
            "properties": {
                "ref_group": {"type": "string", "nullable": True, "default": None},
                "pval_cutoff": {"type": "number", "default": 0.1},
            }
        },
        "select_cfg": {
            "type": "object",
            "properties": {
                "max_n_genes_to_plot": {"type": "integer", "default": 8},
                "genes_to_plot": {"type": "array", "items": {"type": "string"}, "default": []},
                "target_keywords": {"type": "array", "items": {"type": "string"}, "default": []},
                "keyword_match": {"type": "string", "enum": ["contains", "exact"], "default": "exact"},
            }
        },
        "style": {
            "type": "object",
            "properties": {
                "ncols": {"type": "integer", "default": 3},
                "figsize": {"type": "array", "items": {"type": "number"}, "default": [2.5, 2.0]},
                "dpi": {"type": "integer", "default": 100},
                "scale": {"type": "string", "enum": ["area", "count", "width"], "default": "width"},
                "inner": {"type": ["string", "null"], "default": "box"},
                "cmap": {"type": "string", "default": "tab10"},
                # 나머지 스타일 필드들은 AI가 헷갈리지 않게 꼭 필요한 것만 남기거나 생략 가능하게 둠
            }
        }
    },
}
