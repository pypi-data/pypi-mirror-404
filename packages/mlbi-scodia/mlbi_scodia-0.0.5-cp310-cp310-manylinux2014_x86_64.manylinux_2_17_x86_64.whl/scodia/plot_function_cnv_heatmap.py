from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal, Union

import numpy as np
import pandas as pd

from scodaviz import plot_cnv, get_abbreviations, get_abbreviations_uni

# ============================================================
# Tool-friendly configs
# ============================================================
TaxoLevel = Literal["major", "minor", "subset", "ploidy", "auto"]
GroupByMode = Literal[
    "not specified",
    "celltype_major",
    "celltype_minor",
    "celltype_subset",
    "sample",
    "condition",
    # allow also raw obs col name; but for tools, keep enums above when possible
]

@dataclass
class CNVComputeConfig:
    """
    Compute / grouping logic for CNV heatmap (plot_cnv).

    Parameters
    ----------
    taxo_level : {"major","minor","subset","ploidy","auto"}
        Used only when `targets` are provided for subsetting by celltype_*.  
        - "auto": infer from `targets["taxo_level"]` if present; else default "major".
    target_cells :
        If provided and taxo_level is one of major/minor/subset/ploidy, subset adata to those cells.
        If no cells match, keep full data (original behavior).
    groupby : {"not specified","celltype_major","celltype_minor","celltype_subset","sample","condition"}
        How to define `cell_group` used for plot_cnv groupby.
        - "not specified": choose automatically:
            * if no subset match -> "celltype_major"
            * else -> "sample_for_deg"
        - "sample" or "condition": will be converted to "<x>_for_deg" and enable CNA spots.
    add_condition_prefix_to_aneuploid :
        If True and groupby starts with "celltype_", rename Aneuploid groups to:
        "Aneuploid <condition> <celltype_abbrev>" (your original behavior).
    """
    taxo_level: TaxoLevel = "auto"
    target_cells: Sequence[str] = ()
    groupby: GroupByMode = "not specified"
    add_condition_prefix_to_aneuploid: bool = True

    # Defaults that your old snippet sets depending on groupby
    Ns_min_default: float = 0.5
    show_cna_spots_default: bool = False
    n_cells_min_default: int = 100


@dataclass
class CNVHeatmapStyle:
    """Style options forwarded to scodaviz.plot_cnv."""
    title: str = "log2(CNR)"
    title_fontsize: int = 12
    title_y_pos: float = 1.1
    label_fontsize: int = 12
    tick_fontsize: int = 11

    figsize: Tuple[float, float] = (15, 10)
    swap_axes: bool = False
    var_group_rotation: int = 90

    cmap: str = "RdBu_r"
    vmax: Union[int, float] = 1

    show_ticks: bool = True
    xlabel: str = "Genomic spot"
    xtick_rotation: int = 0
    xtick_ha: Literal["right", "left", "center"] = "center"


@dataclass
class CNVDataKeys:
    """Where CNV matrices/metadata live in AnnData."""
    cnv_obsm_key: str = "X_cnv"
    cnv_uns_key: str = "cnv"


# ============================================================
# Helpers
# ============================================================
def _resolve_taxo_level(adata, compute_cfg: CNVComputeConfig, targets: Optional[Dict[str, Any]]) -> str:
    if compute_cfg.taxo_level != "auto":
        return compute_cfg.taxo_level
    if isinstance(targets, dict) and targets.get("taxo_level") in ["major", "minor", "subset", "ploidy"]:
        return str(targets["taxo_level"])
    # fallback
    return "major"


def _subset_by_celltype(
    adata,
    *,
    taxo_level: str,
    target_cells: Sequence[str],
) -> Tuple[Any, Optional[pd.Series]]:
    """
    Subset by celltype_<taxo_level> in obs if possible.
    Returns (adata_s, b_sel). If not applicable, b_sel=None and adata_s=adata.copy().
    """
    if taxo_level in ["major", "minor", "subset"]:
        col = f"celltype_{taxo_level}"
    elif taxo_level == "ploidy":
        col = "ploidy_dec"
    else:
        return adata.copy(), None

    if col not in adata.obs:
        return adata.copy(), None

    b_sel = adata.obs[col].isin(list(target_cells)) if len(target_cells) > 0 else adata.obs[col].isin([])
    if hasattr(b_sel, "sum") and b_sel.sum() > 0:
        return adata[b_sel, :].copy(), b_sel
    # original behavior: if no match, keep full
    return adata.copy(), b_sel


def _auto_groupby(groupby: str, b_sel: Optional[pd.Series]) -> str:
    if groupby != "not specified":
        return groupby
    # original logic:
    if b_sel is None or b_sel.sum() == 0:
        return "celltype_major"
    return "sample_for_deg"


def _prepare_cell_group(
    adata_s,
    *,
    groupby: str,
    rename_dict: dict,
    add_condition_prefix_to_aneuploid: bool,
    compute_cfg: CNVComputeConfig,
) -> Tuple[str, float, bool, float]:
    """
    Create adata_s.obs['cell_group'] and compute Ns_min/show_cna_spots/N_cells_min.

    Returns
    -------
    (groupby_used_for_cell_group, Ns_min, show_cna_spots, N_cells_min)
    """
    Ns_min = compute_cfg.Ns_min_default
    show_cna_spots = compute_cfg.show_cna_spots_default
    N_cells_min = float(compute_cfg.n_cells_min_default)

    # celltype_* grouping
    if groupby.startswith("celltype_"):
        if groupby not in adata_s.obs:
            # fallback to raw string conversion
            adata_s.obs["cell_group"] = "Unknown"
            return groupby, Ns_min, show_cna_spots, N_cells_min

        adata_s.obs["cell_group"] = adata_s.obs[groupby].astype(str).copy(deep=True)
        # apply abbreviations if available
        if isinstance(rename_dict, dict): # and groupby in rename_dict:
            adata_s.obs["cell_group"] = adata_s.obs["cell_group"].replace(rename_dict)

        # prefix aneuploid with condition + celltype label (as you did)
        if add_condition_prefix_to_aneuploid and ("ploidy_dec" in adata_s.obs) and ("condition" in adata_s.obs):
            b = adata_s.obs["ploidy_dec"] == "Aneuploid"
            adata_s.obs.loc[b, "cell_group"] = (
                "Aneuploid "
                + adata_s.obs.loc[b, "condition"].astype(str)
                + " "
                + adata_s.obs.loc[b, "cell_group"].astype(str)
            )
        return groupby, Ns_min, show_cna_spots, N_cells_min

    # sample/condition grouping for DEG-style comparisons
    if groupby in ["sample", "condition"]:
        gb = f"{groupby}_for_deg"
        if gb in adata_s.obs:
            groupby = gb
        show_cna_spots = True
        Ns_min = 4

        pcnt = adata_s.obs[groupby].value_counts()
        # original: mean/4
        if len(pcnt) > 0:
            N_cells_min = float(pcnt.mean() / 4.0)

    # generic grouping
    if groupby not in adata_s.obs:
        # fallback: create something
        adata_s.obs["cell_group"] = "all"
    else:
        adata_s.obs["cell_group"] = adata_s.obs[groupby].astype(str).copy(deep=True)

    return groupby, Ns_min, show_cna_spots, N_cells_min


# ============================================================
# Main
# ============================================================
def plot_cnv_heatmap(
    adata,
    *,
    targets: Optional[Dict[str, Any]] = None,
    compute_cfg: Optional[CNVComputeConfig] = None,
    style: Optional[CNVHeatmapStyle] = None,
    keys: Optional[CNVDataKeys] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Plot CNV heatmap (log2 CNR) grouped by a derived `cell_group` column.

    This is a tool-schema-friendly refactor of your snippet. It supports:
    - optional subsetting by cell types (`compute_cfg.target_cells` + `taxo_level`)
    - automatic groupby selection when groupby="not specified"
    - consistent construction of `cell_group` with abbreviations
    - your original special handling:
        * if groupby is sample/condition -> use *_for_deg, show CNA spots, Ns_min=4
        * if groupby starts with celltype_ -> prefix Aneuploid groups with condition

    Parameters
    ----------
    adata : AnnData
        Input AnnData. Must include CNV matrix in `adata.obsm[keys.cnv_obsm_key]` (default "X_cnv").
    targets : dict, optional
        Optional future extension hook. Example:
        {"taxo_level": "minor"} to override auto taxo level inference.
        (Subsetting itself uses compute_cfg.target_cells.)
    compute_cfg : CNVComputeConfig, optional
        Compute & grouping options.
    style : CNVHeatmapStyle, optional
        Plot styling forwarded to `plot_cnv`.
    keys : CNVDataKeys, optional
        Where CNV data live in AnnData (obsm/uns keys).
    rename_dict : dict, optional
        If provided, should be `get_abbreviations()`-like dict with keys:
        "celltype_major"/"celltype_minor"/"celltype_subset" mapping dicts.

    Returns
    -------
    dict
        {
          "taxo_level": ...,
          "subset_n_cells": ...,
          "subset_applied": bool,
          "groupby_requested": ...,
          "groupby_used": ...,
          "Ns_min": ...,
          "show_cna_spots": ...,
          "N_cells_min": ...,
        }

    Examples
    --------
    # 1) CNV heatmap for all cells, auto groupby
    plot_cnv_heatmap(adata)

    # 2) Subset to macrophages (minor), then group by sample/condition-style comparison
    plot_cnv_heatmap(
        adata,
        compute_cfg=CNVComputeConfig(
            taxo_level="minor",
            target_cells=["Macrophage"],
            groupby="sample",  # will use sample_for_deg if exists
        ),
    )

    # 3) Group by celltype_minor with aneuploid prefix renaming
    plot_cnv_heatmap(
        adata,
        compute_cfg=CNVComputeConfig(
            taxo_level="minor",
            target_cells=[],
            groupby="celltype_minor",
            add_condition_prefix_to_aneuploid=True,
        ),
    )
    """
    compute_cfg = compute_cfg or CNVComputeConfig()
    style = style or CNVHeatmapStyle()
    keys = keys or CNVDataKeys()

    # abbreviations
    if rename_dict is None:
        try:
            rename_dict = get_abbreviations_uni()
        except Exception:
            rename_dict = {}

    # resolve taxo level
    taxo_level = _resolve_taxo_level(adata, compute_cfg, targets)

    # subset by celltype if requested
    adata_s, b_sel = _subset_by_celltype(adata, taxo_level=taxo_level, target_cells=compute_cfg.target_cells)
    subset_applied = (b_sel is not None) and (hasattr(b_sel, "sum")) and (b_sel.sum() > 0)

    # groupby selection (auto if not specified)
    groupby_used = _auto_groupby(compute_cfg.groupby, b_sel)

    # build cell_group + compute Ns_min etc.
    groupby_used, Ns_min, show_cna_spots, N_cells_min = _prepare_cell_group(
        adata_s,
        groupby=groupby_used,
        rename_dict=rename_dict,
        add_condition_prefix_to_aneuploid=compute_cfg.add_condition_prefix_to_aneuploid,
        compute_cfg=compute_cfg,
    )

    # Plot
    axd, cna_spots = plot_cnv(
        adata_s,
        groupby="cell_group",
        N_cells_min=N_cells_min,
        title=style.title,
        title_fs=style.title_fontsize,
        title_y_pos=style.title_y_pos,
        label_fs=style.label_fontsize,
        tick_fs=style.tick_fontsize,
        Ns_min=Ns_min,
        show_cna_spots=show_cna_spots,
        figsize=style.figsize,
        swap_axes=style.swap_axes,
        var_group_rotation=style.var_group_rotation,
        cmap=style.cmap,
        vmax=style.vmax,
        cnv_obsm_key=keys.cnv_obsm_key,
        cnv_uns_key=keys.cnv_uns_key,
        show_ticks=style.show_ticks,
        xlabel=style.xlabel,
        xtick_rot=style.xtick_rotation,
        xtick_ha=style.xtick_ha,
    )

    return {
        "taxo_level": taxo_level,
        "subset_n_cells": int(adata_s.n_obs),
        "subset_applied": bool(subset_applied),
        "groupby_requested": compute_cfg.groupby,
        "groupby_used": groupby_used,
        "Ns_min": float(Ns_min),
        "show_cna_spots": bool(show_cna_spots),
        "N_cells_min": float(N_cells_min),
        "cnv_obsm_key": keys.cnv_obsm_key,
        "cnv_uns_key": keys.cnv_uns_key,
        "img_base64": axd,
        "images": axd,  
    }

def_plot_cnv_heatmap = '''
TaxoLevel = Literal["major", "minor", "subset", "ploidy", "auto"]

GroupByMode = Literal[
    "not specified",
    "celltype_major",
    "celltype_minor",
    "celltype_subset",
    "sample",
    "condition",
    # allow also raw obs col name; but for tools, keep enums above when possible
]

@dataclass
class CNVComputeConfig:
    """
    Compute / grouping logic for CNV heatmap (plot_cnv).

    Parameters
    ----------
    taxo_level : {"major","minor","subset","ploidy","auto"}
        Used only when `targets` are provided for subsetting by celltype_*.  
        - "auto": infer from `targets["taxo_level"]` if present; else default "major".
    target_cells :
        If provided and taxo_level is one of major/minor/subset/ploidy, subset adata to those cells.
        If no cells match, keep full data (original behavior).
    groupby : {"not specified","celltype_major","celltype_minor","celltype_subset","sample","condition"}
        How to define `cell_group` used for plot_cnv groupby.
        - "not specified": choose automatically:
            * if no subset match -> "celltype_major"
            * else -> "sample_for_deg"
        - "sample" or "condition": will be converted to "<x>_for_deg" and enable CNA spots.
    add_condition_prefix_to_aneuploid :
        If True and groupby starts with "celltype_", rename Aneuploid groups to:
        "Aneuploid <condition> <celltype_abbrev>" (your original behavior).
    """
    taxo_level: TaxoLevel = "auto"
    target_cells: Sequence[str] = ()
    groupby: GroupByMode = "not specified"
    add_condition_prefix_to_aneuploid: bool = True

    # Defaults that your old snippet sets depending on groupby
    Ns_min_default: float = 0.5
    show_cna_spots_default: bool = False
    n_cells_min_default: int = 100


@dataclass
class CNVHeatmapStyle:
    """Style options forwarded to scodaviz.plot_cnv."""
    title: str = "log2(CNR)"
    title_fontsize: int = 12
    title_y_pos: float = 1.1
    label_fontsize: int = 12
    tick_fontsize: int = 11

    figsize: Tuple[float, float] = (15, 10)
    swap_axes: bool = False
    var_group_rotation: int = 90

    cmap: str = "RdBu_r"
    vmax: Union[int, float] = 1

    show_ticks: bool = True
    xlabel: str = "Genomic spot"
    xtick_rotation: int = 0
    xtick_ha: Literal["right", "left", "center"] = "center"


@dataclass
class CNVDataKeys:
    """Where CNV matrices/metadata live in AnnData."""
    cnv_obsm_key: str = "X_cnv"
    cnv_uns_key: str = "cnv"

# ============================================================
# Main
# ============================================================
def plot_cnv_heatmap(
    adata,
    *,
    targets: Optional[Dict[str, Any]] = None,
    compute_cfg: Optional[CNVComputeConfig] = None,
    style: Optional[CNVHeatmapStyle] = None,
    keys: Optional[CNVDataKeys] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Plot CNV heatmap (log2 CNR) grouped by a derived `cell_group` column.

    This is a tool-schema-friendly refactor of your snippet. It supports:
    - optional subsetting by cell types (`compute_cfg.target_cells` + `taxo_level`)
    - automatic groupby selection when groupby="not specified"
    - consistent construction of `cell_group` with abbreviations
    - your original special handling:
        * if groupby is sample/condition -> use *_for_deg, show CNA spots, Ns_min=4
        * if groupby starts with celltype_ -> prefix Aneuploid groups with condition

    Parameters
    ----------
    adata : AnnData
        Input AnnData. Must include CNV matrix in `adata.obsm[keys.cnv_obsm_key]` (default "X_cnv").
    targets : dict, optional
        Optional future extension hook. Example:
        {"taxo_level": "minor"} to override auto taxo level inference.
        (Subsetting itself uses compute_cfg.target_cells.)
    compute_cfg : CNVComputeConfig, optional
        Compute & grouping options.
    style : CNVHeatmapStyle, optional
        Plot styling forwarded to `plot_cnv`.
    keys : CNVDataKeys, optional
        Where CNV data live in AnnData (obsm/uns keys).
    rename_dict : dict, optional
        If provided, should be `get_abbreviations()`-like dict with keys:
        "celltype_major"/"celltype_minor"/"celltype_subset" mapping dicts.

    Returns
    -------
    dict
        {
          "taxo_level": ...,
          "subset_n_cells": ...,
          "subset_applied": bool,
          "groupby_requested": ...,
          "groupby_used": ...,
          "Ns_min": ...,
          "show_cna_spots": ...,
          "N_cells_min": ...,
        }

    Examples
    --------
    # 1) CNV heatmap for all cells, auto groupby
    plot_cnv_heatmap(adata)

    # 2) Subset to macrophages (minor), then group by sample/condition-style comparison
    plot_cnv_heatmap(
        adata,
        compute_cfg=CNVComputeConfig(
            taxo_level="minor",
            target_cells=["Macrophage"],
            groupby="sample",  # will use sample_for_deg if exists
        ),
    )

    # 3) Group by celltype_minor with aneuploid prefix renaming
    plot_cnv_heatmap(
        adata,
        compute_cfg=CNVComputeConfig(
            taxo_level="minor",
            target_cells=[],
            groupby="celltype_minor",
            add_condition_prefix_to_aneuploid=True,
        ),
    )
    """
    
    """ Some Code"""
    
    return {
        "taxo_level": taxo_level,
        "subset_n_cells": int(adata_s.n_obs),
        "subset_applied": bool(subset_applied),
        "groupby_requested": compute_cfg.groupby,
        "groupby_used": groupby_used,
        "Ns_min": float(Ns_min),
        "show_cna_spots": bool(show_cna_spots),
        "N_cells_min": float(N_cells_min),
        "cnv_obsm_key": keys.cnv_obsm_key,
        "cnv_uns_key": keys.cnv_uns_key,
        "img_base64": axd,
    }
'''

# ============================================================
# CNV heatmap JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_CNV = {
    "type": "object",
    "properties": {
        "targets": {
            "type": "object", 
            "properties": {
                "obs_col": {"type": "string"}, 
                "value": {"type": "string"}
            },
            "required": ["obs_col", "value"],
            "description": "데이터 서브셋 필터"
        },
        "compute_cfg": {
            "type": "object",
            "properties": {
                "taxo_level": {
                    "type": "string", 
                    "enum": ["major", "minor", "subset", "ploidy", "auto"],
                    "default": "auto"
                },
                "target_cells": {"type": "array", "items": {"type": "string"}, "default": []},
                "groupby": {
                    "type": "string", 
                    "enum": ["not specified", "celltype_major", "celltype_minor", "celltype_subset", "sample", "condition"],
                    "default": "not specified"
                },
                "add_condition_prefix_to_aneuploid": {"type": "boolean", "default": True},
                "Ns_min_default": {"type": "number", "default": 0.5},
                "show_cna_spots_default": {"type": "boolean", "default": False},
                "n_cells_min_default": {"type": "integer", "default": 100}
            },
        },
        "style": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "log2(CNR)"},
                "title_fontsize": {"type": "integer", "default": 12},
                "title_y_pos": {"type": "number", "default": 1.1},
                "label_fontsize": {"type": "integer", "default": 12},
                "tick_fontsize": {"type": "integer", "default": 11},
                "figsize": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2, "default": [15, 10]},
                "swap_axes": {"type": "boolean", "default": False},
                "var_group_rotation": {"type": "integer", "default": 90},
                "cmap": {"type": "string", "default": "RdBu_r"},
                "vmax": {"type": "number", "default": 1.0},
                "show_ticks": {"type": "boolean", "default": True},
                "xlabel": {"type": "string", "default": "Genomic spot"},
                "xtick_rotation": {"type": "integer", "default": 0},
                "xtick_ha": {"type": "string", "enum": ["right", "left", "center"], "default": "center"}
            },
        }
    },
}
