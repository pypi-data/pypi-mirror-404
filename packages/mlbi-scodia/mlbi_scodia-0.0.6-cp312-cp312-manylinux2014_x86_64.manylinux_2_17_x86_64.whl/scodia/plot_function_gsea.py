from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal

from scodaviz import plot_gsa_bar, plot_gsa_dot


# ============================================================
# Tool-friendly configs
# ============================================================
GSAMode = Literal["gsea", "go", "gsa"]
GSAPlotType = Literal["bar", "dot"]
GSASource = Literal["GSEA", "GSEA_vs_ref", "GSA_up", "GSA_vs_ref_up"]

@dataclass
class GSAComputeConfig:
    """
    Data-source selection for GSEA/GO plots stored in `adata.uns`.

    Parameters
    ----------
    gsa_mode : {"gsea","go"}
        - "gsea": use adata.uns["GSEA"] (or "GSEA_vs_ref" if use_ref=True and exists)
        - "go"  : use adata.uns["GSA_up"] (or "GSA_vs_ref_up" if use_ref=True and exists)
    use_ref : bool
        If True, prefer *_vs_ref variants when present; otherwise fall back.
    taxo_level : str, optional
        Obs column for validating target celltypes. If None, try:
        adata.uns["analysis_parameters"]["CCI_DEG_BASE"].
    comp_item : str, optional
        Comparison key for nested results (e.g., adata.uns[GSA_item][cell][comp_item]).
        If None, use adata.uns[GSA_item][cell] directly.
    """
    gsa_mode: GSAMode = "gsea"
    use_ref: bool = False
    taxo_level: Optional[str] = None
    comp_item: Optional[str] = None


@dataclass
class GSABarPlotConfig:
    """Style options forwarded to `plot_gsa_bar`."""
    pval_cutoff: float = 0.05
    n_pws_to_show: int = 20

    title: Optional[str] = None
    bar_width: float = 0.8
    title_pos: Tuple[float, float] = (0.5, 1.0)
    title_fontsize: int = 12
    title_ha: str = "center"
    label_fontsize: int = 11
    tick_fontsize: int = 9
    wspace: float = 0.1
    hspace: float = 0.25

    ax: Any = None
    facecolor: str = "tab:blue"
    edgecolor: str = "black"


@dataclass
class GSADotPlotConfig:
    """Style options forwarded to `plot_gsa_dot`."""
    pval_cutoff: float = 1e-4

    title: Optional[str] = None  # if None -> auto "GSA_item for cell"
    title_fontsize: int = 12
    tick_fontsize: int = 9
    xtick_rotation: int = 90
    xtick_ha: str = "center"
    label_fontsize: int = 11
    legend_fontsize: int = 9

    swap_ax: bool = False
    figsize: Optional[Tuple[float, float]] = None
    dpi: int = 100
    dot_size: int = 50
    cbar_frac: float = 0.1
    cbar_aspect: int = 10
    cmap: str = "Reds"


# ============================================================
# Helpers
# ============================================================
def _infer_taxo_level(adata, taxo_level: Optional[str]) -> Optional[str]:
    if taxo_level is not None:
        return taxo_level
    try:
        return adata.uns["analysis_parameters"]["CCI_DEG_BASE"]
    except Exception:
        return None


def _select_gsa_item(adata, *, gsa_mode: GSAMode, use_ref: bool) -> GSASource:
    if gsa_mode == "gsea":
        if use_ref and ("GSEA_vs_ref" in adata.uns):
            return "GSEA_vs_ref"
        return "GSEA"
    # go
    if use_ref and ("GSA_vs_ref_up" in adata.uns):
        return "GSA_vs_ref_up"
    return "GSA_up"


def _safe_get_nested(obj: Any, comp_item: Optional[str]) -> Any:
    if comp_item is None:
        return obj
    try:
        return obj[comp_item]
    except Exception:
        return obj


# ============================================================
# Main
# ============================================================
def plot_gsea_go(
    adata,
    *,
    target_cells: Sequence[str],
    plot_type: GSAPlotType = "bar",
    compute_cfg: Optional[GSAComputeConfig] = None,
    bar_cfg: Optional[GSABarPlotConfig] = None,
    dot_cfg: Optional[GSADotPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Plot GSEA/GO(GSA_up) results for one or more target cell types.

    This is a tool-schema-friendly wrapper for your snippet:
    - `compute_cfg` picks which adata.uns key to use (GSEA vs GSA_up, vs_ref, comp_item)
    - `plot_type` chooses bar or dot
    - `bar_cfg` / `dot_cfg` control plotting parameters

    Notes
    -----
    - `spec` is optional and only used as a fallback for `plot_type`:
      if plot_type is None, tries spec.get("plot_type").
      For tool calls, passing `plot_type` explicitly is recommended.

    Parameters
    ----------
    adata : AnnData
        Input AnnData containing GSEA/GSA results in `.uns`.
    target_cells : Sequence[str]
        Cell types to plot.
    plot_type : {"bar","dot"}, default "bar"
        Plot style to render.
    compute_cfg : GSAComputeConfig, optional
        Data-source selection and validation settings.
    bar_cfg : GSABarPlotConfig, optional
        Bar plot parameters.
    dot_cfg : GSADotPlotConfig, optional
        Dot plot parameters.

    Returns
    -------
    dict
        {
          "gsa_item": <str>,
          "gsa_mode": "gsea"|"go",
          "use_ref": bool,
          "taxo_level": <str or None>,
          "comp_item": <str or None>,
          "plot_type": "bar"|"dot",
          "requested_cells": [...],
          "plotted_cells": [...],
          "missing_cells": [...],
          "cells_without_gsa": [...],
          "warnings": [...],
        }

    Examples
    --------
    # 1) GSEA bar
    plot_gsas(
        adata,
        target_cells=["Macrophage"],
        plot_type="bar",
        compute_cfg=GSAComputeConfig(gsa_mode="gsea", use_ref=False, comp_item=None),
        bar_cfg=GSABarPlotConfig(n_pws_to_show=25, pval_cutoff=0.05),
    )

    # 2) GO (GSA_up) dot, vs_ref if exists, with nested comparison
    plot_gsas(
        adata,
        target_cells=["Macrophage", "T cell"],
        plot_type="dot",
        compute_cfg=GSAComputeConfig(gsa_mode="go", use_ref=True, comp_item="Tumor_vs_Normal"),
        dot_cfg=GSADotPlotConfig(pval_cutoff=1e-4, cmap="Reds"),
    )
    """
    compute_cfg = compute_cfg or GSAComputeConfig()
    bar_cfg = bar_cfg or GSABarPlotConfig()
    dot_cfg = dot_cfg or GSADotPlotConfig()

    warnings: list[str] = []

    taxo_level = _infer_taxo_level(adata, compute_cfg.taxo_level)
    if taxo_level is None:
        warnings.append("Cannot determine taxo_level. Set compute_cfg.taxo_level explicitly.")

    gsa_item = _select_gsa_item(adata, gsa_mode=compute_cfg.gsa_mode, use_ref=compute_cfg.use_ref)

    gsa_dct = adata.uns.get(gsa_item, None)
    if not isinstance(gsa_dct, dict):
        warnings.append(f"adata.uns['{gsa_item}'] not found or not a dict.")
        return {
            "gsa_item": gsa_item,
            "gsa_mode": compute_cfg.gsa_mode,
            "use_ref": compute_cfg.use_ref,
            "taxo_level": taxo_level,
            "comp_item": compute_cfg.comp_item,
            "plot_type": plot_type,
            "requested_cells": list(target_cells),
            "plotted_cells": [],
            "missing_cells": list(target_cells),
            "cells_without_gsa": list(target_cells),
            "warnings": warnings,
        }

    # Validate available cells if possible
    avail = None
    if taxo_level is not None and taxo_level in adata.obs:
        avail = set(adata.obs[taxo_level].unique())

    plotted_cells: list[str] = []
    missing_cells: list[str] = []
    cells_without_gsa: list[str] = []

    for c in target_cells:
        if avail is not None and (c not in avail):
            missing_cells.append(c)
            warnings.append(f"⚠️ WARNING: cannot identify {c}.")
            continue

        if c not in gsa_dct:
            cells_without_gsa.append(c)
            warnings.append(f"⚠️ WARNING: {c} has no entry in adata.uns['{gsa_item}'].")
            continue

        # pick nested comparison if requested
        adata_uns_gsa = _safe_get_nested(gsa_dct[c], compute_cfg.comp_item)

        if plot_type == "bar":
            axes = plot_gsa_bar(
                adata_uns_gsa,
                pval_cutoff=bar_cfg.pval_cutoff,
                N_max_to_show=bar_cfg.n_pws_to_show,
                title=bar_cfg.title,
                bar_width=bar_cfg.bar_width,
                title_pos=bar_cfg.title_pos,
                title_fs=bar_cfg.title_fontsize,
                title_ha=bar_cfg.title_ha,
                label_fs=bar_cfg.label_fontsize,
                tick_fs=bar_cfg.tick_fontsize,
                wspace=bar_cfg.wspace,
                hspace=bar_cfg.hspace,
                Ax=bar_cfg.ax,
                facecolor=bar_cfg.facecolor,
                edgecolor=bar_cfg.edgecolor,
            )
        else:
            # NOTE: your snippet used adata.uns[GSA_item][target_cell] for dot
            # but logically it should be the same selected object (nested comp) as bar.
            # We'll use `adata_uns_gsa` to keep behavior consistent.
            axes = plot_gsa_dot(
                adata_uns_gsa,
                pval_cutoff=dot_cfg.pval_cutoff,
                title=dot_cfg.title if dot_cfg.title is not None else f"{gsa_item} for {c}",
                title_fs=dot_cfg.title_fontsize,
                tick_fs=dot_cfg.tick_fontsize,
                xtick_rot=dot_cfg.xtick_rotation,
                xtick_ha=dot_cfg.xtick_ha,
                label_fs=dot_cfg.label_fontsize,
                legend_fs=dot_cfg.legend_fontsize,
                swap_ax=dot_cfg.swap_ax,
                figsize=dot_cfg.figsize,
                dpi=dot_cfg.dpi,
                dot_size=dot_cfg.dot_size,
                cbar_frac=dot_cfg.cbar_frac,
                cbar_aspect=dot_cfg.cbar_aspect,
                cmap=dot_cfg.cmap,
            )

        plotted_cells.append(c)

    return {
        "gsa_item": gsa_item,
        "gsa_mode": compute_cfg.gsa_mode,
        "use_ref": compute_cfg.use_ref,
        "taxo_level": taxo_level,
        "comp_item": compute_cfg.comp_item,
        "plot_type": plot_type,
        "requested_cells": list(target_cells),
        "plotted_cells": plotted_cells,
        "missing_cells": missing_cells,
        "cells_without_gsa": cells_without_gsa,
        "warnings": warnings,
        "img_base64": axes,
        "images": axes,  
    }

def_plot_gsea_go = '''
GSAMode = Literal["gsea", "go", "gsa"]
GSAPlotType = Literal["bar", "dot"]
GSASource = Literal["GSEA", "GSEA_vs_ref", "GSA_up", "GSA_vs_ref_up"]

@dataclass
class GSAComputeConfig:
    """
    Data-source selection for GSEA/GO plots stored in `adata.uns`.

    Parameters
    ----------
    gsa_mode : {"gsea","go"}
        - "gsea": use adata.uns["GSEA"] (or "GSEA_vs_ref" if use_ref=True and exists)
        - "go"  : use adata.uns["GSA_up"] (or "GSA_vs_ref_up" if use_ref=True and exists)
    use_ref : bool
        If True, prefer *_vs_ref variants when present; otherwise fall back.
    taxo_level : str, optional
        Obs column for validating target celltypes. If None, try:
        adata.uns["analysis_parameters"]["CCI_DEG_BASE"].
    comp_item : str, optional
        Comparison key for nested results (e.g., adata.uns[GSA_item][cell][comp_item]).
        If None, use adata.uns[GSA_item][cell] directly.
    """
    gsa_mode: GSAMode = "gsea"
    use_ref: bool = False
    taxo_level: Optional[str] = None
    comp_item: Optional[str] = None


@dataclass
class GSABarPlotConfig:
    """Style options forwarded to `plot_gsa_bar`."""
    pval_cutoff: float = 0.05
    n_pws_to_show: int = 20

    title: Optional[str] = None
    bar_width: float = 0.8
    title_pos: Tuple[float, float] = (0.5, 1.0)
    title_fontsize: int = 12
    title_ha: str = "center"
    label_fontsize: int = 11
    tick_fontsize: int = 9
    wspace: float = 0.1
    hspace: float = 0.25

    ax: Any = None
    facecolor: str = "tab:blue"
    edgecolor: str = "black"


@dataclass
class GSADotPlotConfig:
    """Style options forwarded to `plot_gsa_dot`."""
    pval_cutoff: float = 1e-4

    title: Optional[str] = None  # if None -> auto "GSA_item for cell"
    title_fontsize: int = 12
    tick_fontsize: int = 9
    xtick_rotation: int = 90
    xtick_ha: str = "center"
    label_fontsize: int = 11
    legend_fontsize: int = 9

    swap_ax: bool = False
    figsize: Optional[Tuple[float, float]] = None
    dpi: int = 100
    dot_size: int = 50
    cbar_frac: float = 0.1
    cbar_aspect: int = 10
    cmap: str = "Reds"

### Main function
def plot_gsea_go(
    adata,
    *,
    target_cells: Sequence[str],
    plot_type: GSAPlotType = "bar",
    compute_cfg: Optional[GSAComputeConfig] = None,
    bar_cfg: Optional[GSABarPlotConfig] = None,
    dot_cfg: Optional[GSADotPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Short description: Plot GSEA/GO(GSA) results (in bar plots or dot plot) for one or more target cell types.

    This is a tool-schema-friendly wrapper for your snippet:
    - `compute_cfg` picks which adata.uns key to use (GSEA vs GSA_up, vs_ref, comp_item)
    - `plot_type` chooses bar or dot
    - `bar_cfg` / `dot_cfg` control plotting parameters

    Notes
    -----
    - `spec` is optional and only used as a fallback for `plot_type`:
      if plot_type is None, tries spec.get("plot_type").
      For tool calls, passing `plot_type` explicitly is recommended.

    Parameters
    ----------
    adata : AnnData
        Input AnnData containing GSEA/GSA results in `.uns`.
    target_cells : Sequence[str]
        Cell types to plot.
    plot_type : {"bar","dot"}, default "bar"
        Plot style to render.
    compute_cfg : GSAComputeConfig, optional
        Data-source selection and validation settings.
    bar_cfg : GSABarPlotConfig, optional
        Bar plot parameters.
    dot_cfg : GSADotPlotConfig, optional
        Dot plot parameters.

    Returns
    -------
    dict
        {
          "gsa_item": <str>,
          "gsa_mode": "gsea"|"go",
          "use_ref": bool,
          "taxo_level": <str or None>,
          "comp_item": <str or None>,
          "plot_type": "bar"|"dot",
          "requested_cells": [...],
          "plotted_cells": [...],
          "missing_cells": [...],
          "cells_without_gsa": [...],
          "warnings": [...],
        }

    Examples
    --------
    # 1) GSEA bar
    plot_gsas(
        adata,
        target_cells=["Macrophage"],
        plot_type="bar",
        compute_cfg=GSAComputeConfig(gsa_mode="gsea", use_ref=False, comp_item=None),
        bar_cfg=GSABarPlotConfig(n_pws_to_show=25, pval_cutoff=0.05),
    )

    # 2) GO (GSA_up) dot, vs_ref if exists, with nested comparison
    plot_gsas(
        adata,
        target_cells=["Macrophage", "T cell"],
        plot_type="dot",
        compute_cfg=GSAComputeConfig(gsa_mode="go", use_ref=True, comp_item="Tumor_vs_Normal"),
        dot_cfg=GSADotPlotConfig(pval_cutoff=1e-4, cmap="Reds"),
    )
    """
    
    """ Some Code"""
    
    return {
        "gsa_item": gsa_item,
        "gsa_mode": compute_cfg.gsa_mode,
        "use_ref": compute_cfg.use_ref,
        "taxo_level": taxo_level,
        "comp_item": compute_cfg.comp_item,
        "plot_type": plot_type,
        "requested_cells": list(target_cells),
        "plotted_cells": plotted_cells,
        "missing_cells": missing_cells,
        "cells_without_gsa": cells_without_gsa,
        "warnings": warnings,
        "img_base64": axes,
        "ax": axes,
    }
'''

# ============================================================
# GSA JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_GSA = {
    "type": "object",
    "properties": {
        "target_cells": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "분석 결과를 확인할 세포 타입 리스트"
        },
        "plot_type": {
            "type": "string", 
            "enum": ["bar", "dot"], 
            "default": "bar"
        },
        "compute_cfg": {
            "type": "object",
            "properties": {
                "gsa_mode": {
                    "type": "string", 
                    "enum": ["gsea", "go", "gsa"], 
                    "default": "gsea"
                },
                "use_ref": {"type": "boolean", "default": False},
                "taxo_level": {"type": "string", "nullable": True, "default": None},
                "comp_item": {"type": "string", "nullable": True, "default": None}
            },
        },
        "bar_cfg": {
            "type": "object",
            "properties": {
                "pval_cutoff": {"type": "number", "default": 0.05},
                "n_pws_to_show": {"type": "integer", "default": 20},
                "title": {"type": "string", "nullable": True, "default": None},
                "bar_width": {"type": "number", "default": 0.8},
                "title_pos": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2, "default": [0.5, 1.0]},
                "title_fontsize": {"type": "integer", "default": 12},
                "title_ha": {"type": "string", "default": "center"},
                "label_fontsize": {"type": "integer", "default": 11},
                "tick_fontsize": {"type": "integer", "default": 9},
                "wspace": {"type": "number", "default": 0.1},
                "hspace": {"type": "number", "default": 0.25},
                "facecolor": {"type": "string", "default": "tab:blue"},
                "edgecolor": {"type": "string", "default": "black"}
            },
        },
        "dot_cfg": {
            "type": "object",
            "properties": {
                "pval_cutoff": {"type": "number", "default": 1e-4},
                "title": {"type": "string", "nullable": True, "default": None},
                "title_fontsize": {"type": "integer", "default": 12},
                "tick_fontsize": {"type": "integer", "default": 9},
                "xtick_rotation": {"type": "integer", "default": 90},
                "xtick_ha": {"type": "string", "default": "center"},
                "label_fontsize": {"type": "integer", "default": 11},
                "legend_fontsize": {"type": "integer", "default": 9},
                "swap_ax": {"type": "boolean", "default": False},
                "figsize": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2, "nullable": True, "default": None},
                "dpi": {"type": "integer", "default": 100},
                "dot_size": {"type": "integer", "default": 50},
                "cbar_frac": {"type": "number", "default": 0.1},
                "cbar_aspect": {"type": "integer", "default": 10},
                "cmap": {"type": "string", "default": "Reds"}
            },
        }
    },
}
ACTION_SCHEMA_GSEA = ACTION_SCHEMA_GSA
