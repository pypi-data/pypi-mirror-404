from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Literal, Union, Sequence

import numpy as np
import pandas as pd

from scodaviz import get_population_per_sample, plot_population_grouped


TaxoLevel = Literal["major", "minor", "subset", "ploidy"]

@dataclass
class PopulationComputeConfig:
    """
    Compute-side parameters for per-sample population summary.

    taxo_level -> obs column mapping
    -------------------------------
    - "major"  -> "celltype_major"
    - "minor"  -> "celltype_minor"
    - "subset" -> "celltype_subset"
    - "ploidy" -> "ploidy_dec"
    """
    taxo_level: TaxoLevel = "minor"
    sample_col: str = "sample"
    sort_by: Tuple[str, ...] = ()


@dataclass
class PopulationPlotConfig:
    """Plot styling options for grouped bar plot."""
    bar_width: float = 0.6
    title: Optional[str] = None
    title_fontsize: int = 12
    title_y_pos: float = 1.2
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 45
    xtick_ha: Literal["right", "left", "center"] = "right"
    legend_fontsize: int = 9
    legend_loc: str = "center left"
    legend_bbox_to_anchor: Tuple[float, float] = (1.05, 0.5)
    legend_ncol: int = 1
    cmap: Optional[Union[str, Sequence[str]]] = None
    wspace: float = 0.3
    hspace: float = 0.2
    figsize: Tuple[float, float] = (7, 2)
    dpi: int = 100


def _category_col_from_taxo(taxo_level: TaxoLevel) -> str:
    if taxo_level == "subset":
        return "celltype_subset"
    if taxo_level == "minor":
        return "celltype_minor"
    if taxo_level == "major":
        return "celltype_major"
    if taxo_level == "ploidy":
        return "ploidy_dec"
    raise ValueError(f"Unknown taxo_level: {taxo_level}")


def _normalize_targets(targets: Optional[Any]) -> Optional[Dict[str, Any]]:
    """
    Canonicalize targets to dict schema:
        {"obs_col": <str>, "value": <Any>}

    Accepts (optional, for backward compatibility):
        - None
        - dict with keys obs_col/value
        - tuple/list of length 2: (obs_col, value)

    Returns
    -------
    dict or None
        None means "no subsetting".
        Returns {} is never used; invalid input returns a dict with '__invalid__'=True.
    """
    if targets is None:
        return None

    # dict form (preferred)
    if isinstance(targets, dict):
        if "obs_col" in targets and "value" in targets:
            return {"obs_col": str(targets["obs_col"]), "value": targets["value"]}
        return {"__invalid__": True, "raw": targets}

    # tuple/list form (compat)
    if isinstance(targets, (tuple, list)) and len(targets) == 2:
        return {"obs_col": str(targets[0]), "value": targets[1]}

    return {"__invalid__": True, "raw": targets}


def _subset_adata(adata_t, targets: Optional[Any]):
    """
    Subset selector based on obs equality.

    Standard (tool-friendly) schema:
        targets = {"obs_col": ..., "value": ...}
    """
    t = _normalize_targets(targets)
    if t is None:
        return adata_t[:, :]

    if "__invalid__" in t:
        return None

    obs_col = t["obs_col"]
    value = t["value"]

    if obs_col not in adata_t.obs:
        return None
    if value not in list(adata_t.obs[obs_col].unique()):
        return None

    b = adata_t.obs[obs_col] == value
    return adata_t[b, :].copy()


def _pick_most_abundant_category(df_pct: pd.DataFrame) -> Optional[str]:
    num = df_pct.select_dtypes(include="number")
    if num.shape[1] == 0:
        return None
    return num.sum(axis=0).idxmax()

    
def plot_celltype_population(
    adata_t,
    *,
    targets: Optional[Dict[str, Any]] = None,
    compute_cfg: Optional[PopulationComputeConfig] = None,
    plot_cfg: Optional[PopulationPlotConfig] = None,
) -> Optional[Dict[str, Any]]:
    """
    Plot per-sample population (counts and percentages) as grouped bars.

    Tool-schema friendly interface:
    - `targets` uses dict schema: {"obs_col": str, "value": Any}
    - `compute_cfg` and `plot_cfg` configs encapsulate parameters
    - supports taxo_level in {"major","minor","subset","ploidy"}

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData. Requires:
        - adata_t.obs[compute_cfg.sample_col] (default "sample")
        - adata_t.obs[category_col] where category_col depends on compute_cfg.taxo_level
    targets : dict, optional
        Subset selector. Example:
            {"obs_col": "condition", "value": "Tumor"}
        If None, use all cells.
    compute_cfg : PopulationComputeConfig, optional
        Compute-side configuration.
    plot_cfg : PopulationPlotConfig, optional
        Plot styling configuration.

    Returns
    -------
    dict or None
        {
          "category_col": str,
          "taxo_level": str,
          "subset": None or {"obs_col":..., "value":...},
          "sorted_by": list[str],
          "Cell counts per sample": DataFrame,
          "Cell percentages per sample": DataFrame
        }
        Returns None if inputs/targets are invalid or required columns are missing.
    """
    compute_cfg = compute_cfg or PopulationComputeConfig()
    plot_cfg = plot_cfg or PopulationPlotConfig()

    # Subset (dict schema preferred; tuple/list also accepted via _subset_adata)
    adata = _subset_adata(adata_t, targets)
    if adata is None:
        err_msg = (f"❌ERROR: targets {targets} seems not properly defined.")
        return err_msg

    try:
        category_col = _category_col_from_taxo(compute_cfg.taxo_level)
    except ValueError as e:
        err_msg = (f"❌ERROR: {e}")
        return err_msg

    # Validate required columns
    if compute_cfg.sample_col not in adata.obs:
        err_msg = (f"❌ERROR: sample_col '{compute_cfg.sample_col}' not in adata.obs.")
        return err_msg
    if category_col not in adata.obs:
        err_msg = (f"❌ERROR: category_col '{category_col}' not in adata.obs.")
        return err_msg

    # Compute
    df_cnt, df_pct = get_population_per_sample(
        adata,
        category_col,
        sort_by=list(compute_cfg.sort_by),
        sample_col=compute_cfg.sample_col,
    )

    # Sort for plotting
    sorted_by = list(compute_cfg.sort_by)
    if len(sorted_by) == 0:
        abundant = _pick_most_abundant_category(df_pct)
        if abundant is not None:
            sorted_by = [abundant]

    # Plot
    ax = plot_population_grouped(
        df_pct,
        sort_by=sorted_by,
        bar_width=plot_cfg.bar_width,
        title=plot_cfg.title,
        title_fs=plot_cfg.title_fontsize,
        title_y_pos=plot_cfg.title_y_pos,
        label_fs=plot_cfg.label_fontsize,
        tick_fs=plot_cfg.tick_fontsize,
        xtick_rot=plot_cfg.xtick_rotation,
        xtick_ha=plot_cfg.xtick_ha,
        legend_fs=plot_cfg.legend_fontsize,
        legend_loc=plot_cfg.legend_loc,
        bbox_to_anchor=plot_cfg.legend_bbox_to_anchor,
        legend_ncol=plot_cfg.legend_ncol,
        cmap=plot_cfg.cmap,
        figsize=plot_cfg.figsize,
        dpi=plot_cfg.dpi,
        wspace=plot_cfg.wspace,
        hspace=plot_cfg.hspace,
    )

    subset_info = None
    if targets is not None:
        t = _normalize_targets(targets)
        if t is not None and "__invalid__" not in t:
            subset_info = {"obs_col": t["obs_col"], "value": t["value"]}

    return {
        "category_col": category_col,
        "taxo_level": compute_cfg.taxo_level,
        "subset": subset_info,
        "sorted_by": sorted_by,
        "Cell counts per sample": df_cnt,
        "Cell percentages per sample": df_pct,
        "img_base64": ax,  
        "images": ax,  
    }

def_plot_celltype_population = '''
TaxoLevel = Literal["major", "minor", "subset", "ploidy"]

@dataclass
class PopulationComputeConfig:
    """
    Compute-side parameters for per-sample population summary.

    taxo_level -> obs column mapping
    -------------------------------
    - "major"  -> "celltype_major"
    - "minor"  -> "celltype_minor"
    - "subset" -> "celltype_subset"
    - "ploidy" -> "ploidy_dec"
    """
    taxo_level: TaxoLevel = "minor"
    sample_col: str = "sample"
    sort_by: Tuple[str, ...] = ()


@dataclass
class PopulationPlotConfig:
    """Plot styling options for grouped bar plot."""
    bar_width: float = 0.6
    title: Optional[str] = None
    title_fontsize: int = 12
    title_y_pos: float = 1.2
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 45
    xtick_ha: Literal["right", "left", "center"] = "right"
    legend_fontsize: int = 9
    legend_loc: str = "center left"
    legend_bbox_to_anchor: Tuple[float, float] = (1.05, 0.5)
    legend_ncol: int = 1
    cmap: Optional[Union[str, Sequence[str]]] = None
    wspace: float = 0.3
    hspace: float = 0.2
    figsize: Tuple[float, float] = (7, 2)
    dpi: int = 100


def plot_celltype_population(
    adata_t,
    *,
    targets: Optional[Dict[str, Any]] = None,
    compute_cfg: Optional[PopulationComputeConfig] = None,
    plot_cfg: Optional[PopulationPlotConfig] = None,
) -> Optional[Dict[str, Any]]:
    """
    Short description: Plot per-sample celltype population (counts and percentages) as grouped bars.

    Tool-schema friendly interface:
    - `targets` uses dict schema: {"obs_col": str, "value": Any}
    - `compute_cfg` and `plot_cfg` configs encapsulate parameters
    - supports taxo_level in {"major","minor","subset","ploidy"}

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData. Requires:
        - adata_t.obs[compute_cfg.sample_col] (default "sample")
        - adata_t.obs[category_col] where category_col depends on compute_cfg.taxo_level
    targets : dict, optional
        Subset selector. Example:
            {"obs_col": "condition", "value": "Tumor"}
        If None, use all cells.
    compute_cfg : PopulationComputeConfig, optional
        Compute-side configuration.
    plot_cfg : PopulationPlotConfig, optional
        Plot styling configuration.

    Returns
    -------
    dict or None
        {
          "category_col": str,
          "taxo_level": str,
          "subset": None or {"obs_col":..., "value":...},
          "sorted_by": list[str],
          "Cell counts per sample": DataFrame,
          "Cell percentages per sample": DataFrame
        }
        Returns None if inputs/targets are invalid or required columns are missing.
    """
    
    """ Some Code"""
    
    return {
        "category_col": category_col,
        "taxo_level": compute_cfg.taxo_level,
        "subset": subset_info,
        "sorted_by": sorted_by,
        "Cell counts per sample": df_cnt,
        "Cell percentages per sample": df_pct,
        "img_base64": ax,  
        "images": ax,  
    }
'''


# ============================================================
# Population JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_POPULATION = {
    "type": "object",
    "properties": {
        "targets": {
            "type": "object",
            "nullable": True,
            "properties": {
                "obs_col": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["obs_col", "value"],
            "description": "분석 대상을 필터링할 경우 사용 (예: 특정 condition만 보기)"
        },
        "compute_cfg": {
            "type": "object",
            "properties": {
                "taxo_level": {
                    "type": "string",
                    "enum": ["major", "minor", "subset", "ploidy"],
                    "default": "minor"
                },
                "sample_col": {"type": "string", "default": "sample"},
                "sort_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": []
                }
            },
        },
        "plot_cfg": {
            "type": "object",
            "properties": {
                "bar_width": {"type": "number", "default": 0.6},
                "title": {"type": "string", "nullable": True, "default": None},
                "title_fontsize": {"type": "integer", "default": 12},
                "title_y_pos": {"type": "number", "default": 1.2},
                "label_fontsize": {"type": "integer", "default": 11},
                "tick_fontsize": {"type": "integer", "default": 10},
                "xtick_rotation": {"type": "integer", "default": 45},
                "xtick_ha": {
                    "type": "string",
                    "enum": ["right", "left", "center"],
                    "default": "right"
                },
                "legend_fontsize": {"type": "integer", "default": 9},
                "legend_loc": {"type": "string", "default": "center left"},
                "legend_bbox_to_anchor": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                    "default": [1.05, 0.5]
                },
                "legend_ncol": {"type": "integer", "default": 1},
                "cmap": {"type": "string", "nullable": True, "default": None},
                "wspace": {"type": "number", "default": 0.3},
                "hspace": {"type": "number", "default": 0.2},
                "figsize": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                    "default": [7, 2]
                },
                "dpi": {"type": "integer", "default": 100}
            },
        }
    },
}
