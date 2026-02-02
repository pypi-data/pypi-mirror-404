from __future__ import annotations

from scodaviz import plot_population, plot_population_grouped
from scodaviz import plot_cci_dot, plot_cci_circ_group
from scodaviz import plot_gsa_bar, plot_gsa_dot, add_to_subset_markers
from scodaviz import plot_deg, plot_marker_exp, plot_cnv_hit
from scodaviz import plot_cnv, plot_violin, plot_pct_box
from scodaviz import get_sample_to_group_map, plot_sankey

from scodaviz import get_population_per_sample, get_cci_means, get_gene_expression_mean
from scodaviz import get_markers_from_deg, test_group_diff, filter_gsa_result
from scodaviz import find_condition_specific_markers, find_genomic_spots_of_cnv_peaks
from scodaviz import load_scoda_processed_sample_data, get_abbreviations, decompress_tar_gz
from scodaviz import get_amp_regions_for_known_markers, plot_cnv_stat, get_abbreviations_uni
from scodaviz.misc import show_tree

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Literal, Union

import pandas as pd

# ============================================================
# Dataclasses: tool-schema friendly inputs (structured + safe)
# ============================================================
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="condition", value="Tumor")
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
class FeatureSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `items` is provided (non-empty): plot those items (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression and celltype population, usually use `keyword_match="exact"`.
    For CCI identifiers, `keyword_match="contains"` is often more useful.
    """
    max_n_items_to_plot: int = 8
    items_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "contains"


@dataclass
class BoxPlotStyle:
    """
    Shared plotting style options forwarded to `plot_pct_box`.

    Notes
    -----
    Keep this small for tool calling. Prefer presets rather than exposing every matplotlib option.
    """
    ncols: int = 3
    figsize: Tuple[float, float] = (3.5, 3.5)
    dpi: int = 100
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_y_pos: float = 1.05
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 15
    xtick_ha: str = "center"
    annot_ref: Optional[str] = None
    annot_fmt: Literal["simple", "star"] = "simple"
    annot_fontsize: int = 10
    wspace: float = 0.3
    hspace: float = 0.3
    stripplot: bool = True
    stripplot_markersize: int = 5
    cmap: str = "tab10"


# ============================================================
# Core engine (shared)
# ============================================================
def plot_box_with_signif_from_df(
    df: pd.DataFrame,
    *,
    group_col: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    ylabel: str = "Value",
    rename_dict: Optional[dict] = None,
    rename_key: str = "celltype_minor",
) -> Dict[str, Any]:
    """
    Generic engine: (sample × feature) table → significance test → feature selection → box plot.

    Parameters
    ----------
    df : DataFrame
        Must include:
        - numeric feature columns
        - group label column named by `group_col` (default: 'Group')
    group_col : str
        Column name for group labels.
    test_cfg : SignifTestConfig, optional
        Controls `ref_group` and `pval_cutoff` for `test_group_diff`.
    select_cfg : FeatureSelectConfig, optional
        Controls how features are selected for plotting.
    style : BoxPlotStyle, optional
        Plot styling forwarded to `plot_pct_box`.
    ylabel : str
        Y-axis label for box plots.
    rename_dict : dict, optional
        Dictionary containing abbreviation maps. If provided and `rename_key` exists,
        will be passed as `rename_cells` to `plot_pct_box`.
    rename_key : str
        Key within rename_dict (default: 'celltype_minor').

    Returns
    -------
    dict
        {
          "df_res": DataFrame from test_group_diff (indexed by features),
          "features_plotted": list[str],
          "df_matrix": DataFrame used for plotting (df[features_plotted]),
          "groups": Series group labels,
          "warnings": list[str]
        }

    Notes
    -----
    This function depends on your existing functions:
      - test_group_diff(df, ref_group=..., pval_cutoff=...)
      - plot_pct_box(X, groups, **kwargs)

    Examples
    --------
    >>> out = plot_box_with_signif_from_df(df, group_col="Group")
    >>> out["features_plotted"]
    """
    test_cfg = test_cfg or SignifTestConfig()
    select_cfg = select_cfg or FeatureSelectConfig()
    style = style or BoxPlotStyle()

    warnings: List[str] = []

    if df is None or df.shape[0] == 0:
        raise ValueError("df is empty.")
    if group_col not in df.columns:
        raise KeyError(f"'{group_col}' column not found. Available: {list(df.columns)}")

    groups = df[group_col]
    feat_cols = [c for c in df.columns if c != group_col]
    X = df[feat_cols].copy()
    X = X.select_dtypes(include="number")

    if X.shape[1] == 0:
        raise ValueError("No numeric feature columns found (excluding group column).")

    # test_group_diff expects Group inside df in your current codebase pattern
    df_for_test = X.copy()
    df_for_test[group_col] = groups

    df_res = test_group_diff(
        df_for_test,
        ref_group=test_cfg.ref_group,
        pval_cutoff=test_cfg.pval_cutoff,
    )

    available = df_res.index.tolist()

    # --- feature selection (priority: items_to_plot > keywords > topN)
    idx_sel: List[str] = []

    if select_cfg.items_to_plot:
        for it in select_cfg.items_to_plot:
            if it in available:
                idx_sel.append(it)
            else:
                warnings.append(f"item '{it}' not found in test results.")
                print(f"⚠️ WARNING: item '{it}' not found in test results.")
    else:
        if select_cfg.target_keywords:
            if select_cfg.keyword_match == "exact":
                kw_set = set(select_cfg.target_keywords)
                idx_sel = [i for i in available if i in kw_set]
            else:
                tmp = []
                for i in available:
                    for kw in select_cfg.target_keywords:
                        if kw in str(i):
                            tmp.append(i)
                            break
                idx_sel = tmp

        if not idx_sel:
            idx_sel = available[: min(select_cfg.max_n_items_to_plot, len(available))]

    if not idx_sel:
        warnings.append(f"⚠️No items to plot.")
        err_msg = (f"⚠️ WARNING: No items to plot.")
        return err_msg
        '''
        return {
            "df_res": df_res,
            "features_plotted": [],
            "df_matrix": pd.DataFrame(),
            "groups": groups,
            "warnings": warnings,
        }
        '''

    # rename map
    rend = get_abbreviations_uni()
    # if rename_dict is not None and isinstance(rename_dict, dict):
    #     rend = rename_dict.get(rename_key, None)

    # plot
    ax = plot_pct_box(
        X[idx_sel],
        groups,
        ylabel=ylabel,
        ncols=style.ncols,
        figsize=style.figsize,
        dpi=style.dpi,
        group_order=style.group_order,
        rename_cells=rend,
        title=style.title,
        title_y_pos=style.title_y_pos,
        title_fs=style.title_fontsize,
        label_fs=style.label_fontsize,
        tick_fs=style.tick_fontsize,
        xtick_rot=style.xtick_rotation,
        xtick_ha=style.xtick_ha,
        annot_ref=style.annot_ref,
        annot_fmt=style.annot_fmt,
        annot_fs=style.annot_fontsize,
        ws_hs=(style.wspace, style.hspace),
        stripplot=style.stripplot,
        stripplot_ms=style.stripplot_markersize,
        cmap=style.cmap,
    )

    return {
        "df_res": df_res,
        "features_plotted": idx_sel,
        "df_matrix": X[idx_sel],
        "groups": groups,
        "warnings": warnings,
        "img_base64": ax,
        "images": ax,  
    }


# ============================================================
# Helper: subset AnnData safely (tool-friendly targets)
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
# Wrapper 1) Gene expression (sample-mean) box plot
# ============================================================
def plot_box_for_gene_expression_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    obs_group_col: str = "condition",
    group_col_out: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Plot box plots of sample-mean gene expression with significance annotation.

    This tool-friendly wrapper differs from CCI/population wrappers only in preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - normalize_total + log1p
    - compute sample-mean expression table by `get_gene_expression_mean`

    Then delegates to `plot_box_with_signif_from_df(...)`.

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData.
    target_genes : Sequence[str], optional
        Genes of interest. Used as selection keywords (exact-match) unless `select_cfg.items_to_plot` is set.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    obs_group_col : str, default "condition"
        If the computed DataFrame lacks group labels, map sample → `adata.obs[obs_group_col]`.
    group_col_out : str, default "Group"
        Name of group label column to create/use in the intermediate DataFrame.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_gene_expression_with_signif_difference(
    ...     adata, target_genes=["ERBB2","MKI67"],
    ...     targets={"obs_col":"celltype_minor","value":"Tumor epithelial"},
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     style=BoxPlotStyle(annot_fmt="star", title="DEG box plot")
    ... )
    """
    import scanpy as sc

    test_cfg = test_cfg or SignifTestConfig()
    style = style or BoxPlotStyle()

    # default selection behavior for genes: exact match on gene names
    if select_cfg is None:
        select_cfg = FeatureSelectConfig(
            max_n_items_to_plot=8,
            items_to_plot=(),
            target_keywords=list(target_genes),
            keyword_match="exact",
        )
    else:
        # if user didn't supply keywords, inherit from target_genes
        if (not select_cfg.items_to_plot) and (not select_cfg.target_keywords) and target_genes:
            select_cfg = FeatureSelectConfig(
                max_n_items_to_plot=select_cfg.max_n_items_to_plot,
                items_to_plot=select_cfg.items_to_plot,
                target_keywords=list(target_genes),
                keyword_match=select_cfg.keyword_match,
            )

    # parse targets
    obs_filter = None
    if targets is not None:
        if isinstance(targets, dict) and ("obs_col" in targets) and ("value" in targets):
            obs_filter = ObsFilter(obs_col=str(targets["obs_col"]), value=targets["value"])
        else:
            raise ValueError("targets must be a dict with keys {'obs_col','value'}")

    adata = _subset_adata(adata_t, obs_filter)
    if adata is None:
        return {"df_res": None, "features_plotted": [], "df_matrix": pd.DataFrame(), "groups": pd.Series(dtype=object), "warnings": [f"Invalid targets: {targets}"], "df_raw": None}

    # normalize + log1p for expression
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    df = get_gene_expression_mean(
        adata,
        genes=list(target_genes),
        group_col="sample",
        nz_pct=True,
    )

    # Ensure group column exists
    if group_col_out not in df.columns:
        if obs_group_col not in adata.obs.columns:
            raise KeyError(f"'{group_col_out}' not in df and '{obs_group_col}' not in adata.obs.")
        sample_to_group = (
            adata.obs[["sample", obs_group_col]]
            .drop_duplicates()
            .set_index("sample")[obs_group_col]
        )
        # assume df index is sample
        df[group_col_out] = pd.Index(df.index).map(sample_to_group)

    out = plot_box_with_signif_from_df(
        df,
        group_col=group_col_out,
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Gene expression (sample mean)",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out


# ============================================================
# Wrapper 2) CCI (sample-mean) box plot
# ============================================================
def plot_box_for_cci_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Plot box plots of CCI sample means with significance annotation.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - build per-sample CCI mean table via `get_cci_means(...)`
      (returned df must include 'Group' column)

    Selection:
    - default uses keyword_match="contains" with `target_genes` (CCI identifiers are often composite strings)

    Parameters
    ----------
    adata_t : AnnData
        AnnData containing CCI results used by `get_cci_means`.
    target_cells : Sequence[str], optional
        Cell types used to filter CCIs in `get_cci_means`.
    target_genes : Sequence[str], optional
        Keywords for selecting CCI identifiers (contains-match by default).
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_cci_with_signif_difference(
    ...     adata,
    ...     target_cells=["T cell","Myeloid cell"],
    ...     target_genes=["CXCL","CCL"],
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ... )
    """
    test_cfg = test_cfg or SignifTestConfig()
    style = style or BoxPlotStyle()

    # default selection behavior for CCI: contains match
    if select_cfg is None:
        select_cfg = FeatureSelectConfig(
            max_n_items_to_plot=8,
            items_to_plot=(),
            target_keywords=list(target_genes),
            keyword_match="contains",
        )
    else:
        if (not select_cfg.items_to_plot) and (not select_cfg.target_keywords) and target_genes:
            select_cfg = FeatureSelectConfig(
                max_n_items_to_plot=select_cfg.max_n_items_to_plot,
                items_to_plot=select_cfg.items_to_plot,
                target_keywords=list(target_genes),
                keyword_match=select_cfg.keyword_match,
            )

    # parse targets
    obs_filter = None
    if targets is not None:
        if isinstance(targets, dict) and ("obs_col" in targets) and ("value" in targets):
            obs_filter = ObsFilter(obs_col=str(targets["obs_col"]), value=targets["value"])
        else:
            raise ValueError("targets must be a dict with keys {'obs_col','value'}")

    adata = _subset_adata(adata_t, obs_filter)
    if adata is None:
        return {"df_res": None, "features_plotted": [], "df_matrix": pd.DataFrame(), "groups": pd.Series(dtype=object), "warnings": [f"Invalid targets: {targets}"], "df_raw": None}

    # Build CCI mean table (IMPORTANT: pass pval_cutoff from test_cfg, not hard-coded)
    df = get_cci_means(
        adata,
        cci_idx_lst=None,
        cells=list(target_cells),
        genes=list(target_genes),
        pval_cutoff=test_cfg.pval_cutoff,
    )

    out = plot_box_with_signif_from_df(
        df,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="CCI sample mean",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )

    if (out is None) or isinstance(out, str):
        return out
        
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out


# ============================================================
# Wrapper 3) Celltype population (per-sample proportion) box plot
# ============================================================
def plot_box_for_celltype_population_with_signif_difference(
    adata_t,
    *,
    taxo_level: Literal["major", "minor", "subset"] = "minor",
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Plot box plots of sample-wise celltype proportions with significance annotation.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - choose taxonomy column by taxo_level: celltype_major/minor/subset
    - compute per-sample counts and proportions using `get_population_per_sample`
      (df_pct must include 'Group' column)

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData containing cell type annotations in obs.
    taxo_level : {"major","minor","subset"}, default "minor"
        Which cell type taxonomy column to use.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_cnt": counts per sample
        - "df_raw": df_pct (proportions per sample incl. 'Group')

    Examples
    --------
    >>> out = plot_box_for_celltype_population_with_signif_difference(
    ...     adata, taxo_level="minor",
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     select_cfg=FeatureSelectConfig(items_to_plot=["T cell","Myeloid cell"]),
    ... )
    """
    test_cfg = test_cfg or SignifTestConfig()
    style = style or BoxPlotStyle()

    # default selection behavior for population: exact match on celltype names if keywords provided
    if select_cfg is None:
        select_cfg = FeatureSelectConfig(
            max_n_items_to_plot=8,
            items_to_plot=(),
            target_keywords=(),
            keyword_match="exact",
        )

    # parse targets
    obs_filter = None
    if targets is not None:
        if isinstance(targets, dict) and ("obs_col" in targets) and ("value" in targets):
            obs_filter = ObsFilter(obs_col=str(targets["obs_col"]), value=targets["value"])
        else:
            raise ValueError("targets must be a dict with keys {'obs_col','value'}")

    adata = _subset_adata(adata_t, obs_filter)
    if adata is None:
        return {"df_res": None, "features_plotted": [], "df_matrix": pd.DataFrame(), "groups": pd.Series(dtype=object), "warnings": [f"Invalid targets: {targets}"], "df_raw": None}

    # taxonomy column
    celltype_col = f"celltype_{taxo_level}"
    if celltype_col not in adata.obs.columns:
        raise KeyError(f"'{celltype_col}' not found in adata.obs.")

    df_cnt, df_pct = get_population_per_sample(adata, celltype_col)

    out = plot_box_with_signif_from_df(
        df_pct,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Celltype proportion",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_cnt"] = df_cnt
    out["df_raw"] = df_pct
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    out["taxo_level"] = taxo_level
    return out


# ============================================================
# Optional: minimal code-snippet generator (for reproducibility)
# ============================================================
def make_code_snippet_plot_box(tool_name: str, args_used: dict, *, adata_var_name: str = "adata") -> str:
    """
    Create a copy-pastable Python snippet for reproducibility (display only; do NOT exec untrusted code).

    Parameters
    ----------
    tool_name : str
        One of:
        - 'plot_box_for_gene_expression_with_signif_difference'
        - 'plot_box_for_cci_with_signif_difference'
        - 'plot_box_for_celltype_population_with_signif_difference'
    args_used : dict
        The validated/normalized arguments used for execution.
    adata_var_name : str
        Variable name representing AnnData in user's workspace.

    Returns
    -------
    str
        Code snippet string.
    """
    def _fmt(v):
        return repr(v)

    lines = [f"out = {tool_name}(",
             f"    {adata_var_name},"]

    for k, v in args_used.items():
        lines.append(f"    {k}={_fmt(v)},")

    lines.append(")")
    return "\n".join(lines)


def_plot_box = '''
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="condition", value="Tumor")
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
class FeatureSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `items_to_plot` is provided (non-empty): plot those items (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression and celltype population, usually use `keyword_match="exact"`.
    For CCI identifiers, `keyword_match="contains"` is often more useful.
    """
    max_n_items_to_plot: int = 8
    items_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "contains"


@dataclass
class BoxPlotStyle:
    """
    Shared plotting style options forwarded to `plot_pct_box`.

    Notes
    -----
    Keep this small for tool calling. Prefer presets rather than exposing every matplotlib option.
    """
    ncols: int = 3
    figsize: Tuple[float, float] = (3.5, 3.5)
    dpi: int = 100
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_y_pos: float = 1.05
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 15
    xtick_ha: str = "center"
    annot_ref: Optional[str] = None
    annot_fmt: Literal["simple", "star"] = "simple"
    annot_fontsize: int = 10
    wspace: float = 0.3
    hspace: float = 0.3
    stripplot: bool = True
    stripplot_markersize: int = 5
    cmap: str = "tab10"

# ============================================================
# Wrapper 1) Gene expression (sample-mean) box plot
# ============================================================
def plot_box_for_gene_expression_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    obs_group_col: str = "condition",
    group_col_out: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-mean gene expression with significant difference between conditions.

    This tool-friendly wrapper differs from CCI/population wrappers only in preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - normalize_total + log1p
    - compute sample-mean expression table by `get_gene_expression_mean`

    Then delegates to `plot_box_with_signif_from_df(...)`.

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData.
    target_genes : Sequence[str], optional
        Genes of interest. Used as selection keywords (exact-match) unless `select_cfg.items_to_plot` is set.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    obs_group_col : str, default "condition"
        If the computed DataFrame lacks group labels, map sample → `adata.obs[obs_group_col]`.
    group_col_out : str, default "Group"
        Name of group label column to create/use in the intermediate DataFrame.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_gene_expression_with_signif_difference(
    ...     adata, target_genes=["ERBB2","MKI67"],
    ...     targets={"obs_col":"celltype_minor","value":"Tumor epithelial"},
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     style=BoxPlotStyle(annot_fmt="star", title="DEG box plot")
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df,
        group_col=group_col_out,
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Gene expression (sample mean)",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out


# ============================================================
# Wrapper 2) CCI (sample-mean) box plot
# ============================================================
def plot_box_for_cci_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-mean CCI with significant difference between conditions.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - build per-sample CCI mean table via `get_cci_means(...)`
      (returned df must include 'Group' column)

    Selection:
    - default uses keyword_match="contains" with `target_genes` (CCI identifiers are often composite strings)

    Parameters
    ----------
    adata_t : AnnData
        AnnData containing CCI results used by `get_cci_means`.
    target_cells : Sequence[str], optional
        Cell types used to filter CCIs in `get_cci_means`.
    target_genes : Sequence[str], optional
        Keywords for selecting CCI identifiers (contains-match by default).
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_cci_with_signif_difference(
    ...     adata,
    ...     target_cells=["T cell","Myeloid cell"],
    ...     target_genes=["CXCL","CCL"],
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="CCI sample mean",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out


# ============================================================
# Wrapper 3) Celltype population (per-sample proportion) box plot
# ============================================================
def plot_box_for_celltype_population_with_signif_difference(
    adata_t,
    *,
    taxo_level: Literal["major", "minor", "subset"] = "minor",
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-wise celltype proportions with significant difference between conditions.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - choose taxonomy column by taxo_level: celltype_major/minor/subset
    - compute per-sample counts and proportions using `get_population_per_sample`
      (df_pct must include 'Group' column)

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData containing cell type annotations in obs.
    taxo_level : {"major","minor","subset"}, default "minor"
        Which cell type taxonomy column to use.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_cnt": counts per sample
        - "df_raw": df_pct (proportions per sample incl. 'Group')

    Examples
    --------
    >>> out = plot_box_for_celltype_population_with_signif_difference(
    ...     adata, taxo_level="minor",
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     select_cfg=FeatureSelectConfig(items_to_plot=["T cell","Myeloid cell"]),
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df_pct,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Celltype proportion",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_cnt"] = df_cnt
    out["df_raw"] = df_pct
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    out["taxo_level"] = taxo_level
    return out


'''

def_plot_box_for_gene_expression_with_signif_difference = '''
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="condition", value="Tumor")
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
class FeatureSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `items_to_plot` is provided (non-empty): plot those items (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression and celltype population, usually use `keyword_match="exact"`.
    For CCI identifiers, `keyword_match="contains"` is often more useful.
    """
    max_n_items_to_plot: int = 8
    items_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "contains"


@dataclass
class BoxPlotStyle:
    """
    Shared plotting style options forwarded to `plot_pct_box`.

    Notes
    -----
    Keep this small for tool calling. Prefer presets rather than exposing every matplotlib option.
    """
    ncols: int = 3
    figsize: Tuple[float, float] = (3.5, 3.5)
    dpi: int = 100
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_y_pos: float = 1.05
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 15
    xtick_ha: str = "center"
    annot_ref: Optional[str] = None
    annot_fmt: Literal["simple", "star"] = "simple"
    annot_fontsize: int = 10
    wspace: float = 0.3
    hspace: float = 0.3
    stripplot: bool = True
    stripplot_markersize: int = 5
    cmap: str = "tab10"

# ============================================================
# Wrapper 1) Gene expression (sample-mean) box plot
# ============================================================
def plot_box_for_gene_expression_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    obs_group_col: str = "condition",
    group_col_out: str = "Group",
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-mean gene expression with significant difference between conditions.

    This tool-friendly wrapper differs from CCI/population wrappers only in preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - normalize_total + log1p
    - compute sample-mean expression table by `get_gene_expression_mean`

    Then delegates to `plot_box_with_signif_from_df(...)`.

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData.
    target_genes : Sequence[str], optional
        Genes of interest. Used as selection keywords (exact-match) unless `select_cfg.items_to_plot` is set.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    obs_group_col : str, default "condition"
        If the computed DataFrame lacks group labels, map sample → `adata.obs[obs_group_col]`.
    group_col_out : str, default "Group"
        Name of group label column to create/use in the intermediate DataFrame.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_gene_expression_with_signif_difference(
    ...     adata, target_genes=["ERBB2","MKI67"],
    ...     targets={"obs_col":"celltype_minor","value":"Tumor epithelial"},
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     style=BoxPlotStyle(annot_fmt="star", title="DEG box plot")
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df,
        group_col=group_col_out,
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Gene expression (sample mean)",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out

'''

def_plot_box_for_cci_with_signif_difference = '''
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="condition", value="Tumor")
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
class FeatureSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `items_to_plot` is provided (non-empty): plot those items (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression and celltype population, usually use `keyword_match="exact"`.
    For CCI identifiers, `keyword_match="contains"` is often more useful.
    """
    max_n_items_to_plot: int = 8
    items_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "contains"


@dataclass
class BoxPlotStyle:
    """
    Shared plotting style options forwarded to `plot_pct_box`.

    Notes
    -----
    Keep this small for tool calling. Prefer presets rather than exposing every matplotlib option.
    """
    ncols: int = 3
    figsize: Tuple[float, float] = (3.5, 3.5)
    dpi: int = 100
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_y_pos: float = 1.05
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 15
    xtick_ha: str = "center"
    annot_ref: Optional[str] = None
    annot_fmt: Literal["simple", "star"] = "simple"
    annot_fontsize: int = 10
    wspace: float = 0.3
    hspace: float = 0.3
    stripplot: bool = True
    stripplot_markersize: int = 5
    cmap: str = "tab10"

# ============================================================
# Wrapper 2) CCI (sample-mean) box plot
# ============================================================
def plot_box_for_cci_with_signif_difference(
    adata_t,
    *,
    target_cells: Sequence[str] = (),
    target_genes: Sequence[str] = (),
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-mean CCI with significant difference between conditions.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - build per-sample CCI mean table via `get_cci_means(...)`
      (returned df must include 'Group' column)

    Selection:
    - default uses keyword_match="contains" with `target_genes` (CCI identifiers are often composite strings)

    Parameters
    ----------
    adata_t : AnnData
        AnnData containing CCI results used by `get_cci_means`.
    target_cells : Sequence[str], optional
        Cell types used to filter CCIs in `get_cci_means`.
    target_genes : Sequence[str], optional
        Keywords for selecting CCI identifiers (contains-match by default).
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_raw": intermediate DataFrame used for testing/plotting

    Examples
    --------
    >>> out = plot_box_for_cci_with_signif_difference(
    ...     adata,
    ...     target_cells=["T cell","Myeloid cell"],
    ...     target_genes=["CXCL","CCL"],
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="CCI sample mean",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_raw"] = df
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    return out
'''

def_plot_box_for_celltype_population_with_signif_difference = '''
@dataclass
class ObsFilter:
    """
    Subset selector for AnnData based on equality on one obs column.

    Examples
    --------
    ObsFilter(obs_col="condition", value="Tumor")
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
class FeatureSelectConfig:
    """
    Feature selection policy for plotting.

    Priority
    --------
    1) If `items_to_plot` is provided (non-empty): plot those items (intersection with available features).
    2) Else if `target_keywords` is provided: select by keyword matching (contains/exact).
    3) Else: plot top-N (first N rows from df_res index).

    Notes
    -----
    For gene expression and celltype population, usually use `keyword_match="exact"`.
    For CCI identifiers, `keyword_match="contains"` is often more useful.
    """
    max_n_items_to_plot: int = 8
    items_to_plot: Sequence[str] = ()
    target_keywords: Sequence[str] = ()
    keyword_match: Literal["contains", "exact"] = "contains"


@dataclass
class BoxPlotStyle:
    """
    Shared plotting style options forwarded to `plot_pct_box`.

    Notes
    -----
    Keep this small for tool calling. Prefer presets rather than exposing every matplotlib option.
    """
    ncols: int = 3
    figsize: Tuple[float, float] = (3.5, 3.5)
    dpi: int = 100
    group_order: Optional[Sequence[str]] = None
    title: Optional[str] = None
    title_y_pos: float = 1.05
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    xtick_rotation: int = 15
    xtick_ha: str = "center"
    annot_ref: Optional[str] = None
    annot_fmt: Literal["simple", "star"] = "simple"
    annot_fontsize: int = 10
    wspace: float = 0.3
    hspace: float = 0.3
    stripplot: bool = True
    stripplot_markersize: int = 5
    cmap: str = "tab10"

# ============================================================
# Wrapper 3) Celltype population (per-sample proportion) box plot
# ============================================================
def plot_box_for_celltype_population_with_signif_difference(
    adata_t,
    *,
    taxo_level: Literal["major", "minor", "subset"] = "minor",
    targets: Optional[Dict[str, Any]] = None,
    test_cfg: Optional[SignifTestConfig] = None,
    select_cfg: Optional[FeatureSelectConfig] = None,
    style: Optional[BoxPlotStyle] = None,
    rename_dict: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Short description: Box plots of sample-wise celltype proportions with significant difference between conditions.

    Preprocessing:
    - optional subset filtering by targets={"obs_col":..., "value":...}
    - choose taxonomy column by taxo_level: celltype_major/minor/subset
    - compute per-sample counts and proportions using `get_population_per_sample`
      (df_pct must include 'Group' column)

    Parameters
    ----------
    adata_t : AnnData
        Input AnnData containing cell type annotations in obs.
    taxo_level : {"major","minor","subset"}, default "minor"
        Which cell type taxonomy column to use.
    targets : dict, optional
        Subset filter: {"obs_col": str, "value": Any}.
        Example: {"obs_col":"condition","value":"Tumor"}.
    test_cfg, select_cfg, style :
        See `plot_box_with_signif_from_df`.
    rename_dict : dict, optional
        Abbreviation mapping (passed through to engine).

    Returns
    -------
    dict
        Engine output plus:
        - "df_cnt": counts per sample
        - "df_raw": df_pct (proportions per sample incl. 'Group')

    Examples
    --------
    >>> out = plot_box_for_celltype_population_with_signif_difference(
    ...     adata, taxo_level="minor",
    ...     test_cfg=SignifTestConfig(ref_group="Normal", pval_cutoff=0.05),
    ...     select_cfg=FeatureSelectConfig(items_to_plot=["T cell","Myeloid cell"]),
    ... )
    """
    
    """ Some Code"""
    
    out = plot_box_with_signif_from_df(
        df_pct,
        group_col="Group",
        test_cfg=test_cfg,
        select_cfg=select_cfg,
        style=style,
        ylabel="Celltype proportion",
        rename_dict=rename_dict,
        rename_key="celltype_minor",
    )
    out["df_cnt"] = df_cnt
    out["df_raw"] = df_pct
    out["subset"] = None if obs_filter is None else {"obs_col": obs_filter.obs_col, "value": obs_filter.value}
    out["taxo_level"] = taxo_level
    return out


'''


# ============================================================
# BOXPLOT JSON schema helpers (OpenAI/Gemini tool schema friendly)
# ============================================================
BOXPLOT_COMMON_PROPS = {
    "test_cfg": {
        "type": "object",
        "properties": {
            "ref_group": {"type": "string"},
            "pval_cutoff": {"type": "number", "default": 0.1}
        },
    },
    "select_cfg": {
        "type": "object",
        "properties": {
            "max_n_items_to_plot": {"type": "integer", "default": 8},
            "items_to_plot": {"type": "array", "items": {"type": "string"}, "default": []},
            "target_keywords": {"type": "array", "items": {"type": "string"}, "default": []},
            "keyword_match": {"type": "string", "enum": ["contains", "exact"], "default": "contains"}
        },
    },
    "style": {
        "type": "object",
        "properties": {
            "ncols": {"type": "integer", "default": 3},
            "figsize": {"type": "array", "items": {"type": "number"}, "default": [3.5, 3.5]},
            "dpi": {"type": "integer", "default": 100},
            "xtick_rotation": {"type": "integer", "default": 15},
            "stripplot": {"type": "boolean", "default": True},
            "annot_fmt": {"type": "string", "enum": ["simple", "star"], "default": "simple"}
        },
    }
}

#############################################################
# 8. Boxplot Gene/CCI/Population
#############################################################
ACTION_SCHEMA_BOX_GENE = {
    "type": "object",
    "properties": {
        "target_genes": {"type": "array", "items": {"type": "string"}},
        "targets": {"type": "object", "properties": {"obs_col": {"type": "string"}, "value": {"type": "string"}}},
        **BOXPLOT_COMMON_PROPS
    },
}

# 9. Boxplot CCI
ACTION_SCHEMA_BOX_CCI = {
    "type": "object",
    "properties": {
        "target_cells": {"type": "array", "items": {"type": "string"}},
        "target_genes": {"type": "array", "items": {"type": "string"}},
        **BOXPLOT_COMMON_PROPS
    },
}

# 10. Boxplot Population
ACTION_SCHEMA_BOX_POPULATION = {
    "type": "object",
    "properties": {
        "taxo_level": {"type": "string", "enum": ["major", "minor", "subset"], "default": "minor"},
        **BOXPLOT_COMMON_PROPS
    },
}

