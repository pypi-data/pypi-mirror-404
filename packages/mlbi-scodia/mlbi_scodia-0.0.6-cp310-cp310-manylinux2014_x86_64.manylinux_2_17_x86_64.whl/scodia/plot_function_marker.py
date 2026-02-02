from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Literal, Tuple

from scodaviz import plot_marker_exp, find_condition_specific_markers

# ============================================================
# Tool-friendly configs (structured inputs)
# ============================================================
@dataclass
class MarkerFindConfig:
    """
    Configuration for selecting condition-specific marker genes from DEG table.

    Notes
    -----
    This config is passed to `find_condition_specific_markers(...)`.

    Typical usage
    -------------
    - score_col: 'nz_pct_score' (SCODA default)
    - surfaceome_only: True for therapeutic target discovery
    """
    score_col: str = "nz_pct_score"
    n_markers_max: int = 50
    score_cutoff: float = 0.25
    pval_cutoff: float = 0.05
    fc_cutoff: float = 1.5
    surfaceome_only: bool = True
    # verbose: bool = False
    # print_markers: bool = True  # wrapper-side behavior


@dataclass
class MarkerPlotConfig:
    """
    Configuration for plotting marker expression patterns.

    Notes
    -----
    This config is passed to `plot_marker_exp(...)`.
    Keep it relatively small for tool schema.
    """
    # selection / sampling
    N_cells_per_group_min: int = 40
    N_markers_per_group_max: int = 20
    N_markers_total: int = 140

    # aesthetics / layout
    title_y_pos: float = 2.0
    title_fs: int = 24
    text_fs: int = 14
    var_group_height: float = 1.2
    var_group_rotation: int = 45
    standard_scale: Optional[Literal["var", "obs"]] = "var"

    # filtering
    nz_frac_max: float = 0.8
    nz_frac_cutoff: float = 0.05
    rem_mkrs_common_in_N_groups_or_more: int = 3

    # rendering
    legend: bool = True
    figsize: Optional[Tuple[float, float]] = None
    swap_ax: bool = False
    add_rect: bool = True
    cmap: str = "Reds"
    linewidth: float = 2
    linecolor: str = "firebrick"


@dataclass
class ObsFilter:
    """Subset selector for AnnData based on obs column equality."""
    obs_col: str
    value: Any


# ============================================================
# Helper: subset AnnData safely (optional)
# ============================================================
def _subset_adata(adata_t, targets: Optional[ObsFilter]) -> Optional[Any]:
    """
    Return a copy of AnnData optionally filtered by obs equality.

    Returns None if targets invalid.
    """
    if targets is None:
        return adata_t[:, :].copy()

    if targets.obs_col not in adata_t.obs:
        return None
    if targets.value not in list(adata_t.obs[targets.obs_col].unique()):
        return None

    b = adata_t.obs[targets.obs_col] == targets.value
    return adata_t[b, :].copy()


# ============================================================
# Wrapper: find condition-specific markers + plot expression
# ============================================================
def plot_markers_and_expression_dot(
    adata_t,
    *,
    target_cell: Optional[str] = None,
    deg_key: str = "DEG",
    targets: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    find_cfg: Optional[MarkerFindConfig] = None,
    plot_cfg: Optional[MarkerPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Tool-friendly wrapper to:
      1) retrieve DEG table for a target cell type
      2) find condition-specific marker genes (optionally surfaceome-only)
      3) plot marker expression patterns via `plot_marker_exp`

    Parameters
    ----------
    adata_t : AnnData
        SCODA-processed AnnData containing DEG results in `adata.uns[deg_key]`.
    target_cell : str, optional
        Celltype name used to locate DEG table: `adata.uns[deg_key][target_cell]`.
        If None, wrapper will skip marker finding and only plot if `markers` is supplied
        (currently this wrapper expects target_cell for marker finding).
    deg_key : str, default "DEG"
        Key under `adata.uns` where DEG dictionary is stored.
    targets : dict, optional
        Optional subset filter before plotting: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
        Note: marker finding uses DEG table (already computed), but plotting can be limited to subset.
    title : str, optional
        Plot title. If None and target_cell is provided, defaults to "{target_cell} marker expression pattern".
    find_cfg : MarkerFindConfig, optional
        Parameters for `find_condition_specific_markers`.
    plot_cfg : MarkerPlotConfig, optional
        Parameters for `plot_marker_exp`.

    Returns
    -------
    dict
        {
          "target_cell": str or None,
          "markers": dict or None,
          "df_deg_dct_updated": object or None,
          "markers_used_for_plot": dict or None,
          "subset": dict or None,
          "title": str or None,
          "warnings": list[str]
        }

    Dependencies
    ------------
    Requires your existing functions:
      - find_condition_specific_markers(df_deg, ...)
      - plot_marker_exp(adata, markers=..., celltype_selection=..., ...)
    """
    verbose = False
    print_markers = False

    find_cfg = find_cfg or MarkerFindConfig()
    plot_cfg = plot_cfg or MarkerPlotConfig()
    warnings: list[str] = []

    # parse targets
    obs_filter = None
    if targets is not None:
        if isinstance(targets, dict) and ("obs_col" in targets) and ("value" in targets):
            obs_filter = ObsFilter(obs_col=str(targets["obs_col"]), value=targets["value"])
        else:
            raise ValueError("targets must be a dict with keys {'obs_col','value'}")

    # marker finding (from precomputed DEG)
    mkr_dict = None
    df_deg_dct_updated = None

    check = True
    if target_cell is not None:
        if deg_key not in adata_t.uns:
            print(f"⚠️ WARNING: adata.uns['{deg_key}'] not found.")
            check = False
        elif target_cell not in adata_t.uns[deg_key]:
            print(f"⚠️ WARNING: adata.uns['{deg_key}']['{target_cell}'] not found. Available: {list(adata_t.uns[deg_key].keys())[:20]}...")
            check = False

        if not check:
            print(f"⚠️ WARNING: Specified target_cell, {target_cell}, switched to None and Marker finding skipped.")
            target_cell = None
        else:
            mkr_dict, df_deg_dct_updated = find_condition_specific_markers(
                adata_t.uns[deg_key][target_cell],
                score_col=find_cfg.score_col,
                n_markers_max=find_cfg.n_markers_max,
                score_cutoff=find_cfg.score_cutoff,
                pval_cutoff=find_cfg.pval_cutoff,
                nz_pct_fc_cutoff=find_cfg.fc_cutoff,
                surfaceome_only=find_cfg.surfaceome_only,
                verbose=verbose,
            )
    
            if mkr_dict is not None and print_markers:
                for key in mkr_dict.keys():
                    mkr_dict[key].sort()
                    print(f"{key} ({len(mkr_dict[key])}): ", mkr_dict[key])
    else:
        warnings.append("target_cell is None. Marker finding was skipped.")
        print("⚠️ WARNING: target_cell is None. Marker finding was skipped.")

    # title default
    if title is None and target_cell is not None:
        title = f"{target_cell} marker expression pattern"

    # subset for plotting (optional)
    adata_plot = _subset_adata(adata_t, obs_filter)
    if adata_plot is None:
        warnings.append(f"Invalid targets: {targets}")
        err_msg = (f"⚠️ WARNING: targets {targets} seems not properly defined.")
        return err_msg
        '''
        return {
            "target_cell": target_cell,
            "markers": mkr_dict,
            "df_deg_dct_updated": df_deg_dct_updated,
            "markers_used_for_plot": None,
            "subset": None,
            "title": title,
            "warnings": warnings,
        }
        '''

    # plot
    markers_used, ax = plot_marker_exp(
        adata_plot,
        markers=mkr_dict,
        celltype_selection=target_cell,
        N_cells_per_group_min=plot_cfg.N_cells_per_group_min,
        N_markers_per_group_max=plot_cfg.N_markers_per_group_max,
        N_markers_total=plot_cfg.N_markers_total,
        title=title,
        title_y_pos=plot_cfg.title_y_pos,
        title_fs=plot_cfg.title_fs,
        text_fs=plot_cfg.text_fs,
        var_group_height=plot_cfg.var_group_height,
        var_group_rotation=plot_cfg.var_group_rotation,
        standard_scale=plot_cfg.standard_scale,
        nz_frac_max=plot_cfg.nz_frac_max,
        nz_frac_cutoff=plot_cfg.nz_frac_cutoff,
        rem_mkrs_common_in_N_groups_or_more=plot_cfg.rem_mkrs_common_in_N_groups_or_more,
        legend=plot_cfg.legend,
        figsize=plot_cfg.figsize,
        swap_ax=plot_cfg.swap_ax,
        add_rect=plot_cfg.add_rect,
        cmap=plot_cfg.cmap,
        linewidth=plot_cfg.linewidth,
        linecolor=plot_cfg.linecolor,
    )

    return {
        "target_cell": target_cell,
        "markers": mkr_dict,
        "df_deg_dct_updated": df_deg_dct_updated,
        "markers_used_for_plot": markers_used,
        "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
        "title": title,
        "warnings": warnings,
        "img_base64": ax,
        "images": ax,  
    }

def_plot_markers_and_expression_dot = '''
@dataclass
class MarkerFindConfig:
    """
    Configuration for selecting condition-specific marker genes from DEG table.

    Notes
    -----
    This config is passed to `find_condition_specific_markers(...)`.

    Typical usage
    -------------
    - score_col: 'nz_pct_score' (SCODA default)
    - surfaceome_only: True for therapeutic target discovery
    """
    score_col: str = "nz_pct_score"
    n_markers_max: int = 50
    score_cutoff: float = 0.25
    pval_cutoff: float = 0.05
    fc_cutoff: float = 1.5
    surfaceome_only: bool = True


@dataclass
class MarkerPlotConfig:
    """
    Configuration for plotting marker expression patterns.

    Notes
    -----
    This config is passed to `plot_marker_exp(...)`.
    Keep it relatively small for tool schema.
    """
    # selection / sampling
    N_cells_per_group_min: int = 40
    N_markers_per_group_max: int = 20
    N_markers_total: int = 140

    # aesthetics / layout
    title_y_pos: float = 2.0
    title_fs: int = 24
    text_fs: int = 14
    var_group_height: float = 1.2
    var_group_rotation: int = 45
    standard_scale: Optional[Literal["var", "obs"]] = "var"

    # filtering
    nz_frac_max: float = 0.8
    nz_frac_cutoff: float = 0.05
    rem_mkrs_common_in_N_groups_or_more: int = 3

    # rendering
    legend: bool = True
    figsize: Optional[Tuple[float, float]] = None
    swap_ax: bool = False
    add_rect: bool = True
    cmap: str = "Reds"
    linewidth: float = 2
    linecolor: str = "firebrick"


@dataclass
class ObsFilter:
    """Subset selector for AnnData based on obs column equality."""
    obs_col: str
    value: Any

# ============================================================
# Wrapper: find condition-specific markers + plot expression
# ============================================================
def plot_markers_and_expression_dot(
    adata_t,
    *,
    target_cell: Optional[str] = None,
    deg_key: str = "DEG",
    targets: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    find_cfg: Optional[MarkerFindConfig] = None,
    plot_cfg: Optional[MarkerPlotConfig] = None,
) -> Dict[str, Any]:
    """
    Short description: Dot plot showing marker expression patterns, e.g., subset markers or condition-specific markers for a given cell type. 
    
    Tool-friendly wrapper to:
      1) retrieve DEG table for a target cell type
      2) find condition-specific marker genes (optionally surfaceome-only)
      3) plot marker expression patterns via `plot_marker_exp`

    Parameters
    ----------
    adata_t : AnnData
        SCODA-processed AnnData containing DEG results in `adata.uns[deg_key]`.
    target_cell : str, optional
        Celltype name used to locate DEG table: `adata.uns[deg_key][target_cell]`.
        If None, wrapper will skip marker finding and only plot if `markers` is supplied
        (currently this wrapper expects target_cell for marker finding).
    deg_key : str, default "DEG"
        Key under `adata.uns` where DEG dictionary is stored.
    targets : dict, optional
        Optional subset filter before plotting: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
        Note: marker finding uses DEG table (already computed), but plotting can be limited to subset.
    title : str, optional
        Plot title. If None and target_cell is provided, defaults to "{target_cell} marker expression pattern".
    find_cfg : MarkerFindConfig, optional
        Parameters for `find_condition_specific_markers`.
    plot_cfg : MarkerPlotConfig, optional
        Parameters for `plot_marker_exp`.

    Returns
    -------
    dict
        {
          "target_cell": str or None,
          "markers": dict or None,
          "df_deg_dct_updated": object or None,
          "markers_used_for_plot": dict or None,
          "subset": dict or None,
          "title": str or None,
          "warnings": list[str]
          "img_base64": axes,
          "images": ax,  
        }

    Dependencies
    ------------
    Requires your existing functions:
      - find_condition_specific_markers(df_deg, ...)
      - plot_marker_exp(adata, markers=..., celltype_selection=..., ...)
    """
    
    """ Some Code"""
    
    return {
        "target_cell": target_cell,
        "markers": mkr_dict,
        "df_deg_dct_updated": df_deg_dct_updated,
        "markers_used_for_plot": markers_used,
        "subset": None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value},
        "title": title,
        "warnings": warnings,
    }
'''

# ============================================================
# MARKER EXP JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
ACTION_SCHEMA_MARKER = {
    "type": "object",
    "properties": {
        "target_cell": {
            "type": "string",  
            "nullable": True,         # null 허용 여부 명시
            "default": None,          # "null" 문자열이 아닌 실제 None            
            "description": "The name of the celltype to analyze (e.g., 'Epithelial cell'). MUST be null if the user did not specify any celltype. If specified, it Must exist in the DEG table and the deg_key shouldn't be null. "
        },
        "deg_key": {
            "type": "string",  
            "enum": ["DEG", "DEG_vs_ref"],
            "nullable": True,         # null 허용 여부 명시
            "default": "DEG",
            "description": "The dictionary key in `adata.uns` containing DEG results. Choose 'DEG' for standard analysis or 'DEG_vs_ref' for reference-based comparisons. Used only when target_cell is not null"
        },                
        "targets": {  
            "type": "object",
            "default": None,
            "description": "Optional filter to select cells (e.g., {'obs_col': 'celltype_major', 'value': 'Epithelial cell'})",
            "properties": {
                "obs_col": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["obs_col", "value"],
            "nullable": True,
            "description": "분석 대상을 필터링할 경우 사용 (예: 특정 celltype만 보기)"
        },        
        "find_cfg": {
            "type": "object",
            "description": "MarkerFindConfig 클래스용 설정",
            "properties": {
                "score_col": {"type": "string", "default": "nz_pct_score"},
                "n_markers_max": {"type": "integer", "default": 50},
                "score_cutoff": {"type": "number", "default": 0.25},
                "pval_cutoff": {"type": "number", "default": 0.05},
                "fc_cutoff": {"type": "number", "default": 1.5},
                "surfaceome_only": {"type": "boolean", "default": True}
            },
        },
        "plot_cfg": {
            "type": "object",
            "description": "MarkerPlotConfig 클래스용 설정",
            "properties": {
                "N_cells_per_group_min": {"type": "integer", "default": 40},
                "N_markers_per_group_max": {"type": "integer", "default": 20},
                "N_markers_total": {"type": "integer", "default": 140},
                "title_y_pos": {"type": "number", "default": 2.0},
                "title_fs": {"type": "integer", "default": 24},
                "text_fs": {"type": "integer", "default": 14},
                "var_group_height": {"type": "number", "default": 1.2},
                "var_group_rotation": {"type": "integer", "default": 45},
                "standard_scale": {
                    "type": "string", 
                    "enum": ["var", "obs"], 
                    "nullable": True, 
                    "default": "var"
                },
                "nz_frac_max": {"type": "number", "default": 0.8},
                "nz_frac_cutoff": {"type": "number", "default": 0.05},
                "rem_mkrs_common_in_N_groups_or_more": {"type": "integer", "default": 3},
                "legend": {"type": "boolean", "default": True},
                "figsize": {
                    "type": "array", 
                    "items": {"type": "number"}, 
                    "minItems": 2, 
                    "maxItems": 2, 
                    "nullable": True, 
                    "default": None
                },
                "swap_ax": {"type": "boolean", "default": False},
                "add_rect": {"type": "boolean", "default": True},
                "cmap": {"type": "string", "default": "Reds"},
                "linewidth": {"type": "number", "default": 2.0},
                "linecolor": {"type": "string", "default": "firebrick"}
            },
        }
    },
}

