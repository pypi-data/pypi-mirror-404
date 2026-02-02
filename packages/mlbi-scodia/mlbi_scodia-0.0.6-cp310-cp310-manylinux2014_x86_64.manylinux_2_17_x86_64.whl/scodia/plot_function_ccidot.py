from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple, Literal, Union

from scodaviz import plot_cci_dot, get_abbreviations, get_abbreviations_uni


def find_tumor_origin_celltype( adata ):

    tumor_org_ind = None
    if adata.uns['usr_param']['tumor_id']:
        b = adata.obs['tumor_origin_ind'] == True
        pcnt = adata.obs.loc[b, 'celltype_major'].value_counts()
        if pcnt.index.values[0] != 'unassigned':
            tumor_org_ind = pcnt.index.values[0]
        else:
            tumor_org_ind = 'unassigned, %s' % pcnt.index.values[1]
    return tumor_org_ind


# ============================================================
# Tool-friendly configs
# ============================================================
@dataclass
class CCIComputeConfig:
    """
    Data selection options for CCI dot plot.

    Parameters
    ----------
    condition :
        If provided and exists in adata.uns["CCI"], uses adata.uns["CCI"][condition].
        Otherwise falls back to adata.uns["CCI"] (global).
    expand_ploidy_from_tumor_origin :
        If True, tries to expand target_cells by appending
        "Aneuploid <cell>" and "Diploid <cell>" when a tumor-origin celltype is detected.
        (Requires your helper `find_tumor_origin_celltype` to be available in scope.)
    """
    condition: Optional[str] = None
    expand_ploidy_from_tumor_origin: bool = True


@dataclass
class CCIDotPlotConfig:
    """Style and filtering options forwarded to `plot_cci_dot`."""
    n_pairs_to_show: int = 30
    pval_cutoff: float = 0.1
    mean_cutoff: float = 0.1

    title: Optional[str] = None
    title_fontsize: int = 12
    legend_fontsize: int = 9
    legend_marker_size: int = 9
    tick_fontsize: int = 9
    xtick_rotation: int = 90
    xtick_ha: Literal["right", "left", "center"] = "center"
    dpi: int = 100
    swap_ax: bool = True
    cmap: Optional[Union[str, Sequence[str]]] = None


# ============================================================
# Helpers
# ============================================================
def _select_cci_object(adata, condition: Optional[str]) -> Any:
    """
    Return the CCI object to plot.
    - If condition exists in adata.uns["CCI"], return adata.uns["CCI"][condition]
    - else return adata.uns["CCI"]
    """
    cci = adata.uns.get("CCI", None)
    if cci is None:
        return None
    if condition is not None and isinstance(cci, dict) and (condition in cci):
        return cci[condition]
    return cci


def _expand_target_cells_with_ploidy(
    adata,
    target_cells: Sequence[str],
    *,
    enabled: bool,
) -> list[str]:
    """
    Expand target_cells by adding 'Aneuploid <t>' and 'Diploid <t>' if tumor-origin is detected.

    Requires `find_tumor_origin_celltype(adata)` in the caller's environment.
    """
    out = list(target_cells)
    if not enabled:
        return out

    # Lazy import behavior: if helper missing, just skip
    try:
        tumor_org_ind = find_tumor_origin_celltype(adata)  # noqa: F821
    except Exception:
        tumor_org_ind = None

    if tumor_org_ind is None:
        return out

    for t in list(target_cells):
        if t in tumor_org_ind:
            out.append(f"Aneuploid {t}")
            out.append(f"Diploid {t}")
            break
    return out


def _get_cell_rename_map(rename_dict: Optional[dict]) -> Optional[dict]:
    """
    Resolve rename mapping for cell names.
    - If rename_dict provided and has 'celltype_minor', use it
    - else fall back to get_abbreviations()['celltype_minor'] if available
    """
    if isinstance(rename_dict, dict):
        if "celltype_minor" in rename_dict and isinstance(rename_dict["celltype_minor"], dict):
            return rename_dict["celltype_minor"]

    try:
        rd = get_abbreviations()
        if isinstance(rd, dict) and isinstance(rd.get("celltype_minor"), dict):
            return rd["celltype_minor"]
    except Exception:
        pass
    return None


# ============================================================
# Main
# ============================================================
def plot_cci_dots(
    adata,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    compute_cfg: Optional[CCIComputeConfig] = None,
    dot_cfg: Optional[CCIDotPlotConfig] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    
    """
    Plot Cell-Cell Interaction (CCI) dot plot for selected cell types/genes.

    Tool-schema friendly wrapper around `scodaviz.plot_cci_dot`.

    Expected AnnData structure
    --------------------------
    adata.uns["CCI"] must exist. It can be either:
      - a dict keyed by condition: adata.uns["CCI"][condition]
      - or a global object directly: adata.uns["CCI"]

    Parameters
    ----------
    adata : AnnData
        SCODA-processed AnnData containing CCI results in `.uns["CCI"]`.
    target_cells : Sequence[str]
        Cell types to include in the plot.
    target_genes : Sequence[str]
        Gene keywords used to filter CCI pairs (optional; depends on your `plot_cci_dot` behavior).
    compute_cfg : CCIComputeConfig, optional
        Controls which CCI object to use (by condition) and whether to expand ploidy labels.
    dot_cfg : CCIDotPlotConfig, optional
        Plot and filter settings forwarded to `plot_cci_dot`.
    rename_dict : dict, optional
        If provided, should contain {"celltype_minor": {...}} mapping for abbreviations.
        If not provided, falls back to `get_abbreviations()`.

    Returns
    -------
    dict
        {
          "condition": <str or None>,
          "requested_cells": [...],
          "expanded_cells": [...],
          "requested_genes": [...],
          "used_cci_source": "CCI[condition]" | "CCI",
          "warnings": [...],
        }

    Examples
    --------
    # 1) Basic CCI dot plot
    plot_cci_dots(
        adata,
        target_cells=["Macrophage", "T cell"],
        target_genes=["CXCL", "CCR"],
        compute_cfg=CCIComputeConfig(condition=None),
        dot_cfg=CCIDotPlotConfig(n_pairs_to_show=40),
    )

    # 2) Condition-specific + ploidy expansion
    plot_cci_dots(
        adata,
        target_cells=["Epithelial"],
        target_genes=[],
        compute_cfg=CCIComputeConfig(condition="Tumor", expand_ploidy_from_tumor_origin=True),
        dot_cfg=CCIDotPlotConfig(pval_cutoff=0.05, mean_cutoff=0.1),
    )
    """
    compute_cfg = compute_cfg or CCIComputeConfig()
    dot_cfg = dot_cfg or CCIDotPlotConfig()

    warnings: list[str] = []

    # Expand cells with ploidy tags if desired
    expanded_cells = _expand_target_cells_with_ploidy(
        adata,
        target_cells,
        enabled=compute_cfg.expand_ploidy_from_tumor_origin,
    )

    # Get rename map
    # rename_cells = _get_cell_rename_map(rename_dict)
    rename_cells = get_abbreviations_uni()

    # Select CCI object
    adata_uns_cci = _select_cci_object(adata, compute_cfg.condition)
    if adata_uns_cci is None:
        warnings.append("adata.uns['CCI'] not found.")
        return {
            "condition": compute_cfg.condition,
            "requested_cells": list(target_cells),
            "expanded_cells": expanded_cells,
            "requested_genes": list(target_genes),
            "used_cci_source": None,
            "warnings": warnings,
        }

    used_source = "CCI"
    if compute_cfg.condition is not None:
        cci = adata.uns.get("CCI", None)
        if isinstance(cci, dict) and compute_cfg.condition in cci:
            used_source = f"CCI[{compute_cfg.condition}]"

    # Plot
    img_base64s = plot_cci_dot(
        adata_uns_cci,
        n_gene_pairs=dot_cfg.n_pairs_to_show,
        target_cells = expanded_cells,
        target_genes=list(target_genes),
        pval_cutoff=dot_cfg.pval_cutoff,
        mean_cutoff=dot_cfg.mean_cutoff,
        rename_cells=rename_cells,
        title=dot_cfg.title,
        title_fs=dot_cfg.title_fontsize,
        legend_fs=dot_cfg.legend_fontsize,
        legend_mkr_sz=dot_cfg.legend_marker_size,
        tick_fs=dot_cfg.tick_fontsize,
        xtick_rot=dot_cfg.xtick_rotation,
        xtick_ha=dot_cfg.xtick_ha,
        dpi=dot_cfg.dpi,
        swap_ax=dot_cfg.swap_ax,
        cmap=dot_cfg.cmap,
    )

    return {
        "condition": compute_cfg.condition,
        "requested_cells": list(target_cells),
        "expanded_cells": expanded_cells,
        "requested_genes": list(target_genes),
        "used_cci_source": used_source,
        "img_base64": img_base64s,  # keep for programmatic reuse if caller wants
        "images": img_base64s,  # keep for programmatic reuse if caller wants
        "warnings": warnings,
    }

def_plot_cci_dots = '''
@dataclass
class CCIComputeConfig:
    """
    Data selection options for CCI dot plot.

    Parameters
    ----------
    condition :
        If provided and exists in adata.uns["CCI"], uses adata.uns["CCI"][condition].
        Otherwise falls back to adata.uns["CCI"] (global).
    expand_ploidy_from_tumor_origin :
        If True, tries to expand target_cells by appending
        "Aneuploid <cell>" and "Diploid <cell>" when a tumor-origin celltype is detected.
        (Requires your helper `find_tumor_origin_celltype` to be available in scope.)
    """
    condition: Optional[str] = None
    expand_ploidy_from_tumor_origin: bool = True


@dataclass
class CCIDotPlotConfig:
    """Style and filtering options forwarded to `plot_cci_dot`."""
    n_pairs_to_show: int = 30
    pval_cutoff: float = 0.1
    mean_cutoff: float = 0.1

    title: Optional[str] = None
    title_fontsize: int = 12
    legend_fontsize: int = 9
    legend_marker_size: int = 9
    tick_fontsize: int = 9
    xtick_rotation: int = 90
    xtick_ha: Literal["right", "left", "center"] = "center"
    dpi: int = 100
    swap_ax: bool = True
    cmap: Optional[Union[str, Sequence[str]]] = None

@dataclass
class CCIComputeConfig:
    """
    Data selection options for CCI dot plot.

    Parameters
    ----------
    condition :
        If provided and exists in adata.uns["CCI"], uses adata.uns["CCI"][condition].
        Otherwise falls back to adata.uns["CCI"] (global).
    expand_ploidy_from_tumor_origin :
        If True, tries to expand target_cells by appending
        "Aneuploid <cell>" and "Diploid <cell>" when a tumor-origin celltype is detected.
        (Requires your helper `find_tumor_origin_celltype` to be available in scope.)
    """
    condition: Optional[str] = None
    expand_ploidy_from_tumor_origin: bool = True


@dataclass
class CCIDotPlotConfig:
    """Style and filtering options forwarded to `plot_cci_dot`."""
    n_pairs_to_show: int = 30
    pval_cutoff: float = 0.1
    mean_cutoff: float = 0.1

    title: Optional[str] = None
    title_fontsize: int = 12
    legend_fontsize: int = 9
    legend_marker_size: int = 9
    tick_fontsize: int = 9
    xtick_rotation: int = 90
    xtick_ha: Literal["right", "left", "center"] = "center"
    dpi: int = 100
    swap_ax: bool = True
    cmap: Optional[Union[str, Sequence[str]]] = None


def plot_cci_dots(
    adata,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    compute_cfg: Optional[CCIComputeConfig] = None,
    dot_cfg: Optional[CCIDotPlotConfig] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    
    """
    Short description: Plot Cell-Cell Interaction (CCI) dot plot for selected cell types/genes.

    Tool-schema friendly wrapper around `scodaviz.plot_cci_dot`.

    Expected AnnData structure
    --------------------------
    adata.uns["CCI"] must exist. It can be either:
      - a dict keyed by condition: adata.uns["CCI"][condition]
      - or a global object directly: adata.uns["CCI"]

    Parameters
    ----------
    adata : AnnData
        SCODA-processed AnnData containing CCI results in `.uns["CCI"]`.
    target_cells : Sequence[str]
        Cell types to include in the plot.
    target_genes : Sequence[str]
        Exact gene names used to filter CCI pairs (optional; depends on your `plot_cci_dot` behavior).
    compute_cfg : CCIComputeConfig, optional
        Controls which CCI object to use (by condition) and whether to expand ploidy labels.
    dot_cfg : CCIDotPlotConfig, optional
        Plot and filter settings forwarded to `plot_cci_dot`.
    rename_dict : dict, optional
        If provided, should contain {"celltype_minor": {...}} mapping for abbreviations.
        If not provided, falls back to `get_abbreviations()`.

    Returns
    -------
    dict
        {
          "condition": <str or None>,
          "requested_cells": [...],
          "expanded_cells": [...],
          "requested_genes": [...],
          "used_cci_source": "CCI[condition]" | "CCI",
          "warnings": [...],
        }

    Examples
    --------
    # 1) Basic CCI dot plot
    plot_cci_dots(
        adata,
        target_cells=["Macrophage", "T cell"],
        target_genes=["CXCL8", "CCR3"],
        compute_cfg=CCIComputeConfig(condition=None),
        dot_cfg=CCIDotPlotConfig(n_pairs_to_show=40),
    )

    # 2) Condition-specific + ploidy expansion
    plot_cci_dots(
        adata,
        target_cells=["Epithelial"],
        target_genes=[],
        compute_cfg=CCIComputeConfig(condition="Tumor", expand_ploidy_from_tumor_origin=True),
        dot_cfg=CCIDotPlotConfig(pval_cutoff=0.05, mean_cutoff=0.1),
    )
    """

    """ Some Code"""

    return {
        "condition": compute_cfg.condition,
        "requested_cells": list(target_cells),
        "expanded_cells": expanded_cells,
        "requested_genes": list(target_genes),
        "used_cci_source": used_source,
        "img_base64": ax,  # keep for programmatic reuse if caller wants
        "warnings": warnings,
    }
'''

# ============================================================
# CCI JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_CCI = {
    "type": "object",
    "properties": {
        "target_cells": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "분석에 포함할 세포 타입들 (예: ['T cell CD8+', 'Macrophage'])"
        },
        "target_genes": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "관심 있는 리간드-수용체 유전자들"
        },
        "compute_cfg": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string", 
                    "nullable": True, 
                    "default": None,
                    "description": "adata.uns['CCI'] 내의 특정 조건 (예: 'TNBC')"
                },
                "expand_ploidy_from_tumor_origin": {
                    "type": "boolean", 
                    "default": True
                }
            },
        },
        "dot_cfg": {
            "type": "object",
            "properties": {
                "n_pairs_to_show": {"type": "integer", "default": 30},
                "pval_cutoff": {"type": "number", "default": 0.1},
                "mean_cutoff": {"type": "number", "default": 0.1},
                "title": {"type": "string", "nullable": True, "default": None},
                "title_fontsize": {"type": "integer", "default": 12},
                "legend_fontsize": {"type": "integer", "default": 9},
                "legend_marker_size": {"type": "integer", "default": 9},
                "tick_fontsize": {"type": "integer", "default": 9},
                "xtick_rotation": {"type": "integer", "default": 90},
                "xtick_ha": {
                    "type": "string", 
                    "enum": ["right", "left", "center"], 
                    "default": "center"
                },
                "dpi": {"type": "integer", "default": 100},
                "swap_ax": {"type": "boolean", "default": True},
                "cmap": {
                    "type": "string", 
                    "nullable": True, 
                    "default": None,
                    "description": "컬러맵 이름 (예: 'Viridis', 'RdYlBu_r')"
                }
            },
        }
    },
}

