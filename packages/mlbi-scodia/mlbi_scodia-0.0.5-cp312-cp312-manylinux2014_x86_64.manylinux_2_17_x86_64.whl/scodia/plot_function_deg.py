from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal
import copy

from scodaviz import plot_deg


# -----------------------------
# Tool-friendly configs
# -----------------------------
DEGMode = Literal["DEG", "DEG_vs_ref"]


@dataclass
class DEGComputeConfig:
    """
    Compute-side options for DEG plotting.

    Parameters
    ----------
    deg_mode :
        Which DEG result to use from adata.uns.
        - "DEG"        -> adata.uns["DEG"]
        - "DEG_vs_ref" -> adata.uns["DEG_vs_ref"]
    taxo_level :
        Obs column that defines celltype names.
        If None, inferred from adata.uns['analysis_parameters']['CCI_DEG_BASE'].
    """
    deg_mode: DEGMode = "DEG"
    taxo_level: Optional[str] = None


@dataclass
class DEGPlotConfig:
    """
    Plot & filtering options forwarded to `plot_deg`.

    Notes
    -----
    - `sort_by` controls how DEG dataframe is ranked before plotting.
    - Default 'nz_pct_score' matches your current behavior.
    """
    n_genes_to_show: int = 30
    pval_cutoff: float = 0.01
    sort_by: str = "nz_pct_score"

    figsize: Tuple[float, float] = (4, 2)
    dpi: int = 100

    text_fontsize: int = 7
    title_fontsize: int = 12
    label_fontsize: int = 10
    tick_fontsize: int = 9

    ncols: int = 5
    wspace: float = 0.2
    hspace: float = 0.5

    show_log_pv: bool = False


# -----------------------------
# Helpers
# -----------------------------
def _infer_taxo_level(adata, taxo_level: Optional[str]) -> Optional[str]:
    if taxo_level is not None:
        return taxo_level
    try:
        return adata.uns["analysis_parameters"]["CCI_DEG_BASE"]
    except Exception:
        return None


# -----------------------------
# Main function
# -----------------------------
def plot_degs(
    adata,
    *,
    target_cells: Sequence[str],
    target_genes: Sequence[str] = (),
    compute_cfg: Optional[DEGComputeConfig] = None,
    plot_cfg: Optional[DEGPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Plot DEG results for one or more target cell types.

    Tool-schema friendly wrapper around `scodaviz.plot_deg`.

    Expected AnnData structure
    --------------------------
    adata.uns must contain:
      - adata.uns["DEG"] or adata.uns["DEG_vs_ref"]
      - adata.uns["DEG_stat"] or adata.uns["DEG_vs_ref_stat"] (optional)

    Returns
    -------
    dict
        {
          "deg_mode": "DEG" | "DEG_vs_ref",
          "taxo_level": <str>,
          "requested_cells": [...],
          "plotted_cells": [...],
          "missing_cells": [...],
          "cells_without_deg": [...],
          "warnings": [...]
        }
    """
    compute_cfg = compute_cfg or DEGComputeConfig()
    plot_cfg = plot_cfg or DEGPlotConfig()

    warnings: list[str] = []

    deg_item = compute_cfg.deg_mode
    taxo_level = _infer_taxo_level(adata, compute_cfg.taxo_level)

    if taxo_level is None:
        warnings.append("Cannot determine taxo_level. Set compute_cfg.taxo_level explicitly.")

    if len(target_cells) == 0:
        warnings.append("No target_cells provided.")
        return {
            "deg_mode": deg_item,
            "taxo_level": taxo_level,
            "requested_cells": [],
            "plotted_cells": [],
            "missing_cells": [],
            "cells_without_deg": [],
            "warnings": warnings,
        }

    deg_dct = adata.uns.get(deg_item)
    if not isinstance(deg_dct, dict):
        warnings.append(f"adata.uns['{deg_item}'] not found or invalid.")
        return {
            "deg_mode": deg_item,
            "taxo_level": taxo_level,
            "requested_cells": list(target_cells),
            "plotted_cells": [],
            "missing_cells": list(target_cells),
            "cells_without_deg": list(target_cells),
            "warnings": warnings,
        }

    deg_stat_all = adata.uns.get(f"{deg_item}_stat", {})

    available_celltypes = (
        set(adata.obs[taxo_level].unique())
        if taxo_level in adata.obs
        else None
    )

    plotted, missing, no_deg = [], [], []
    deg_res_to_return = {}
    axes = {}

    for c in target_cells:
        if available_celltypes is not None and c not in available_celltypes:
            missing.append(c)
            warnings.append(f"Cannot identify celltype '{c}' in obs['{taxo_level}']")
            continue

        if c not in deg_dct:
            no_deg.append(c)
            warnings.append(f"No DEG result for celltype '{c}'")
            continue

        deg_df = copy.deepcopy(deg_dct[c])
        deg_stat = copy.deepcopy(deg_stat_all.get(c))

        # --- sorting (filtering-level option) ---
        for case in deg_df.keys():
            if len(target_genes) > 0:
                b = (deg_df[case]['gene'].isin(target_genes)) & (deg_df[case]["pval"] <= plot_cfg.pval_cutoff)
                if b.sum() > 0:
                    deg_df[case] = deg_df[case].loc[b]                    
                    if plot_cfg.sort_by in deg_df[case].columns:
                        deg_df[case] = deg_df[case].sort_values(plot_cfg.sort_by, ascending=False).iloc[:min(plot_cfg.n_genes_to_show, deg_df[case].shape[0])]
                else:
                    del deg_df[case]
                    del deg_stat[case]

        deg_res_to_return[c] = deg_df

        print(c)
        ax = plot_deg(
            deg_df,
            n_genes_to_show=plot_cfg.n_genes_to_show,
            pval_cutoff=plot_cfg.pval_cutoff,
            figsize=plot_cfg.figsize,
            dpi=plot_cfg.dpi,
            text_fs=plot_cfg.text_fontsize,
            title_fs=plot_cfg.title_fontsize,
            label_fs=plot_cfg.label_fontsize,
            tick_fs=plot_cfg.tick_fontsize,
            ncols=plot_cfg.ncols,
            wspace=plot_cfg.wspace,
            hspace=plot_cfg.hspace,
            deg_stat_dct=deg_stat,
            show_log_pv=plot_cfg.show_log_pv,
        )

        axes[c] = ax
        plotted.append(c)

    return {
        "deg_mode": deg_item,
        "deg_summaries": deg_res_to_return,
        "taxo_level": taxo_level,
        "requested_cells": list(target_cells),
        "plotted_cells": plotted,
        "missing_cells": missing,
        "cells_without_deg": no_deg,
        "warnings": warnings,
        "img_base64": axes,
        "images": axes,  
    }


# ============================================================
# Function definition 
# ============================================================
def_plot_degs = '''
DEGMode = Literal["DEG", "DEG_vs_ref"]

@dataclass
class DEGComputeConfig:
    """
    Compute-side options for DEG plotting.

    Parameters
    ----------
    deg_mode :
        Which DEG result to use from adata.uns.
        - "DEG"        -> adata.uns["DEG"]
        - "DEG_vs_ref" -> adata.uns["DEG_vs_ref"]
    taxo_level :
        Obs column that defines celltype names.
        If None, inferred from adata.uns['analysis_parameters']['CCI_DEG_BASE'].
    """
    deg_mode: DEGMode = "DEG"
    taxo_level: Optional[str] = None

@dataclass
class DEGPlotConfig:
    """
    Plot & filtering options forwarded to `plot_deg`.

    Notes
    -----
    - `sort_by` controls how DEG dataframe is ranked before plotting.
    - Default 'nz_pct_score' matches your current behavior.
    """
    n_genes_to_show: int = 30
    pval_cutoff: float = 0.01
    sort_by: str = "nz_pct_score"

    figsize: Tuple[float, float] = (4, 2)
    dpi: int = 100

    text_fontsize: int = 7
    title_fontsize: int = 12
    label_fontsize: int = 10
    tick_fontsize: int = 9

    ncols: int = 5
    wspace: float = 0.2
    hspace: float = 0.5

    show_log_pv: bool = False

# -----------------------------
# Main function
# -----------------------------
def plot_degs(
    adata,
    *,
    target_cells: Sequence[str],
    target_genes: Sequence[str] = (),
    compute_cfg: Optional[DEGComputeConfig] = None,
    plot_cfg: Optional[DEGPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Short description: Plot DEG results (gene ranking) for one or more target cell types.

    Tool-schema friendly wrapper around `scodaviz.plot_deg`.

    Expected AnnData structure
    --------------------------
    adata.uns must contain:
      - adata.uns["DEG"] or adata.uns["DEG_vs_ref"]
      - adata.uns["DEG_stat"] or adata.uns["DEG_vs_ref_stat"] (optional)

    Returns
    -------
    dict
        {
          "deg_mode": "DEG" | "DEG_vs_ref",
          "taxo_level": <str>,
          "requested_cells": [...],
          "plotted_cells": [...],
          "missing_cells": [...],
          "cells_without_deg": [...],
          "warnings": [...]
        }
    """
    
    """ Some Code"""
    

    return {
        "deg_mode": deg_item,
        "taxo_level": taxo_level,
        "requested_cells": list(target_cells),
        "plotted_cells": plotted,
        "missing_cells": missing,
        "cells_without_deg": no_deg,
        "img_base64": ax,
        "warnings": warnings,
    }

'''

# ============================================================
# DEG JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_DEG = {
    "type": "object",
    "properties": {
        "target_cells": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "분석하려는 세포 타입 리스트 (celltype_minor 등)"
        },
        "target_genes": {
            "type": "array", 
            "items": {"type": "string"}, 
            "default": [],
            "description": "분석하고자 하는 유전자 리스트 (예: ['GAPDH', 'CD3E'])"
        },        
        "compute_cfg": {
            "type": "object",
            "properties": {
                "deg_mode": {
                    "type": "string", 
                    "enum": ["DEG", "DEG_vs_ref"], 
                    "default": "DEG"
                },
                "taxo_level": {
                    "type": "string", 
                    "nullable": True, 
                    "default": None,
                    "description": "세포 타입을 정의하는 obs 컬럼명 (예: celltype_minor)"
                }
            },
        },
        "plot_cfg": {
            "type": "object",
            "properties": {
                "n_genes_to_show": {"type": "integer", "default": 30},
                "pval_cutoff": {"type": "number", "default": 0.01},
                "sort_by": {"type": "string", "default": "nz_pct_score"},
                "figsize": {
                    "type": "array", 
                    "items": {"type": "number"}, 
                    "minItems": 2, 
                    "maxItems": 2, 
                    "default": [4, 2]
                },
                "dpi": {"type": "integer", "default": 100},
                "text_fontsize": {"type": "integer", "default": 7},
                "title_fontsize": {"type": "integer", "default": 12},
                "label_fontsize": {"type": "integer", "default": 10},
                "tick_fontsize": {"type": "integer", "default": 9},
                "ncols": {"type": "integer", "default": 5},
                "wspace": {"type": "number", "default": 0.2},
                "hspace": {"type": "number", "default": 0.5},
                "show_log_pv": {"type": "boolean", "default": False}
            },
        }
    },
}

