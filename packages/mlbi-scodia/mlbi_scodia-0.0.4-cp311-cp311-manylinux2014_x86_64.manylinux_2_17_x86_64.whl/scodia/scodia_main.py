## SCODA-viz에 Plot 함수 interface 추가함
from .plot_function_umap import plot_umap, UMAPEmbedConfig, UMAPPlotConfig
from .plot_function_stackedbar import plot_celltype_population, PopulationComputeConfig, PopulationPlotConfig
from .plot_function_deg import plot_degs, DEGComputeConfig, DEGPlotConfig
from .plot_function_gsea import plot_gsea_go, GSAComputeConfig, GSABarPlotConfig, GSADotPlotConfig
from .plot_function_ccidot import plot_cci_dots, CCIComputeConfig, CCIDotPlotConfig
from .plot_function_cnv_heatmap import plot_cnv_heatmap, CNVComputeConfig, CNVHeatmapStyle, CNVDataKeys
from .plot_function_marker import plot_markers_and_expression_dot, MarkerFindConfig, MarkerPlotConfig
from .plot_function_violin import plot_violin_for_gene_expression_with_signif_difference
from .plot_function_violin import SignifTestConfig, GeneSelectConfig, ViolinPlotStyle
from .plot_function_box import plot_box_for_celltype_population_with_signif_difference
from .plot_function_box import plot_box_for_cci_with_signif_difference
from .plot_function_box import plot_box_for_gene_expression_with_signif_difference
from .plot_function_box import ObsFilter, SignifTestConfig, FeatureSelectConfig, BoxPlotStyle

## 함수의 정의, schema json, Tool name to Tool map (비공개)
from .tool_map import TOOL_FUNCS, FUNCTION_DEF_REGISTRY
from .tool_map import SCHEMA_REGISTRY, Tool_config_map

from .scodia_supp import display_analysis_parameters, render_scoda_info
from .scodia_supp import render_scoda_explanation, render_gemini_questions
from .scodia_supp import create_doc_with_style, creat_download_link
from .scodia_supp import build_repro_code_snippet_clean

###########################################
### Create Data Context
###########################################

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

def get_data_description_str( adata ):
    
    info = 'AnnData: ' + f'{adata.obs.shape[0]} cells × {adata.var.shape[0]} genes'
    
    items = [i for i in adata.obs.columns.values]
    info = info + '\n - obs columns: ' + ', '.join(items)
    items = [i for i in adata.var.columns.values]
    info = info + '\n - var columns: ' + ', '.join(items)

    info = info + '\n - species: ' + adata.uns['usr_param']['species']
    info = info + '\n - tissue: ' + adata.uns['usr_param']['tissue']

    info = info + '\n - conditions: ' + ', '.join( list(adata.obs['condition'].unique()) )
    info = info + '\n - celltype_major: ' + ', '.join( list(adata.obs['celltype_major'].unique()) )
    info = info + '\n - celltype_minor: ' + ', '.join( list(adata.obs['celltype_minor'].unique()) )
    info = info + '\n - celltype_subset: ' + ', '.join( list(adata.obs['celltype_subset'].unique()) )
    if adata.uns['usr_param']['tumor_id']:
        b = adata.obs['tumor_origin_ind'] == True
        pcnt = adata.obs.loc[b, 'celltype_major'].value_counts()
        if pcnt.index.values[0] != 'unassigned':
            tumor_org_ind = pcnt.index.values[0]
        else:
            tumor_org_ind = 'unassigned, %s' % pcnt.index.values[1]
        info = info + '\n - Tumor origin celltype: ' + tumor_org_ind  
        info = info + '\n - ploidy_dec: Aneuploid, Diploid '

    taxo_level = adata.uns['analysis_parameters']['CCI_DEG_BASE'] # .split('_')[-1]
    deg_ref = adata.uns['analysis_parameters']['DEG_REF_GROUP']

    if deg_ref in list(adata.obs['condition'].unique()):
        info = info + '\n - Reference condition for DEG_vs_ref, GSEA_vs_ref, and GSA_vs_ref_up: ' + deg_ref

    if 'CCI' in list(adata.uns.keys()):
        cts = list(adata.uns['CCI'].keys())
        info = info + '\n - CCI DataFrame columns: ' + ', '.join(adata.uns['CCI'][cts[0]].columns.values.tolist())

    if 'DEG' in list(adata.uns.keys()):
        cts = list(adata.uns['DEG'].keys())
        ccs = list(adata.uns['DEG'][cts[0]])
        info = info + '\n - DEG DataFrame columns: ' + ', '.join(adata.uns['DEG'][cts[0]][ccs[0]].columns.values.tolist())

    if 'GSEA' in list(adata.uns.keys()):
        cts = list(adata.uns['GSEA'].keys())
        ccs = list(adata.uns['GSEA'][cts[0]])
        info = info + '\n - GSEA DataFrame columns: ' + ', '.join(adata.uns['GSEA'][cts[0]][ccs[0]].columns.values.tolist())

    if 'GSA_up' in list(adata.uns.keys()):
        cts = list(adata.uns['GSA_up'].keys())
        ccs = list(adata.uns['GSA_up'][cts[0]])
        info = info + '\n - GSA DataFrame columns: ' + ', '.join(adata.uns['GSA_up'][cts[0]][ccs[0]].columns.values.tolist())

    info = info + '\n\nPrecomputed results include .. '
    if 'CCI' in list(adata.uns.keys()):
        info = info + '\n - uns[\'CCI\']: ' + f'Cell-cell interaction (CellPhoneDB) results per condition.'  
    if 'CCI_sample' in list(adata.uns.keys()):
        info = info + '\n - uns[\'CCI_sample\']: ' + f'Cell-cell interaction (CellPhoneDB) results per sample.'  
    if 'DEG' in list(adata.uns.keys()):
        info = info + '\n - uns[\'DEG\']: ' + f'DEG results for each {taxo_level} comparing one condition versus the rest.'  
    if 'DEG_vs_ref' in list(adata.uns.keys()):
        info = info + '\n - uns[\'DEG_vs_ref\']: ' + f'DEG results for each {taxo_level} comparing one condition versus the reference condition.'  
    if 'GSEA' in list(adata.uns.keys()):
        info = info + '\n - uns[\'GSEA\']: ' + f'GSEA results for each {taxo_level} comparing one condition versus the rest.'  
    if 'GSEA_vs_ref' in list(adata.uns.keys()):
        info = info + '\n - uns[\'GSEA_vs_ref\']: ' + f'GSEA results for each {taxo_level} comparing one condition versus the reference condition.'  
    if 'GSA_up' in list(adata.uns.keys()):
        info = info + '\n - uns[\'GSA_up\']: ' + f'GO results for each {taxo_level} comparing one condition versus the rest.'  
    if 'GSA_vs_ref_up' in list(adata.uns.keys()):
        info = info + '\n - uns[\'GSA_vs_ref_up\']: ' + f'DO results for each {taxo_level} comparing one condition versus the reference condition.'  

    if adata.uns['usr_param']['tumor_id']:
        info = info + '\n - obs[\'ploidy_dec\']: ' + f'Ploidy inference label (Aneuploid/Diploid).'
        info = info + '\n - obsm[\'X_cnv\']: ' + 'CNV estimates.'
        
    return info


def get_data_context( adata ):
    
    data_context = get_data_description_str( adata ) 
    role = '\n\n[DATA CONTEXT]\n'
    role = role + 'An AnnData (obtained from single-cell RNA-seq data) is given: \n'
    role = role + data_context
    return role


###########################################
### PROMPTs
###########################################

ROUTER_PROMPT = """
You are the SCODA-AI Strategic Router.
Analyze the user's request and toggle the functional flags and select the appropriate tool from the 10 specialized functions.

[FUNCTIONAL FLAGS]
- info: True if the user asks for a general dataset overview / what data contains.
- plot: True if any visualization (UMAP, Heatmap, Dotplot, Boxplot, etc.) is requested.
- table_summary: True if the user wants structured results (DEG, CCI, etc.).
- explain_data: True if the user requests interpretation/explanation grounded in the dataset outputs (plots/tables) or asks “what does this mean in this dataset?”
- explain_general: True if the user requests general biology/medical knowledge NOT grounded in this dataset (no need for data context).
- reportgen: True if the user wants a formal downloadable report.
- specific_pathway: True ONLY if the user explicitly mentions a named biological pathway (e.g., "cell cycle", "TGF-beta signaling", "WNT signaling") that should be used for GENE SET–BASED target_genes selection, optionally with a known database reference (KEGG, WikiPathways, MSigDB). If the user names a pathway only as background context and does not intend gene set–based target_genes selection, set specific_pathway = False.

[EXPLANATION ROUTING RULES]
- If the user references "this plot/table/result", specific clusters/celltypes in the dataset, or asks to interpret dataset-derived outputs → explain_data=True.
- If the user asks general definitions/mechanisms (e.g., “what is EMT?”, “List some cell-cycle-related genes.”) without referencing dataset outputs → explain_general=True.
- Both can be True if the user asks to explain a dataset result AND requests general background.
- explain_general should be True if all other flags are False.

[TOOL SELECTION GUIDE]
If 'plot' is True, you MUST select one of the following in 'selected_tool':
1. 'plot_umap': For UMAP/t-SNE visualization (gene-expression X or CNV-based mode).
2. 'plot_celltype_population': For grouped bar charts of per-sample cell counts/proportions.
3. 'plot_degs': For DEG ranking plots (DEG / DEG_vs_ref).
4. 'plot_gsea_go': For GSEA/GO(GSA) enrichment plots (bar or dot).
5. 'plot_cci_dots': For CCI interaction dot plots.
6. 'plot_cnv_heatmap': For CNV heatmaps (log2 CNR) grouped by derived 'cell_group'.
7. 'plot_markers_and_expression_dot': For marker discovery + expression dot plots.
8. 'plot_violin_for_gene_expression_with_signif_difference': For single-cell gene expression violin plots.
9. 'plot_box_for_gene_expression_with_signif_difference': Boxplots of sample-mean gene expression across conditions with statistical significance testing.
10. 'plot_box_for_cci_with_signif_difference': Boxplots of sample-mean cell–cell interaction (CCI) scores across conditions with statistical significance testing.
11. 'plot_box_for_celltype_population_with_signif_difference': Boxplots of per-sample celltype proportions across conditions with statistical significance testing.

[OUTPUT RULES]
1) Return ONLY valid JSON.
2) If plot is False and no tool matches, set 'selected_tool' to "none".

[INFO_ANSWER RULES — MUST FOLLOW WHEN info=True]
- If flags.info is True, you MUST provide a non-empty info_answer.
- The info_answer should explain:
  • what the dataset is
  • what analyses/functions are available
  • what the user can do with this data
  • example questions the user may ask
- If the user asks in English, provide the info_answer in English.

### INFO_ANSWER OUTPUT FORMAT:
- "summary": array of strings (each string should be one bullet-ready sentence).
- "functions": array of "name: desc" strings.
- "capabilities": array of strings explaining possible analyses.
- "example_questions": array of 4~8 possible questions.
- "reason" must be a single short sentence (<= 200 chars).

### STRICT KEY RULES:
- You MUST use the exact keys specified below. 
- DO NOT change the casing, DO NOT replace underscores with spaces, and DO NOT add or remove any characters.
- Valid keys are: "summary", "functions", "capabilities", "example_questions"
"""

'''
- Write for a human collaborator (clear, structured, explanatory).
'''

ROUTER_SCHEMA = {
  "type": "object",
  "properties": {
    "kind": {"type": "string", "enum": ["plan"]},
    "flags": {
      "type": "object",
      "properties": {
        "info": {"type": "boolean"},
        "plot": {"type": "boolean"},
        "table_summary": {"type": "boolean"},
        "explain_data": {"type": "boolean"},
        "explain_general": {"type": "boolean"},
        "reportgen": {"type": "boolean"},
        "specific_pathway": {"type": "boolean"}          
      },
      "required": ["info", "plot", "table_summary", "explain_data", "explain_general", "specific_pathway", "reportgen"]
    },      
    "selected_tool": {
      "type": "string",
      "enum": [
        "plot_umap", 
        "plot_celltype_population", 
        "plot_degs", 
        "plot_gsea_go", 
        "plot_cci_dots", 
        "plot_cnv_heatmap", 
        "plot_markers_and_expression_dot",
        "plot_violin_for_gene_expression_with_signif_difference",
        "plot_box_for_gene_expression_with_signif_difference",
        "plot_box_for_cci_with_signif_difference",
        "plot_box_for_celltype_population_with_signif_difference",
        "none"
      ]
    },
    # 이 부분을 ["string", "null"]에서 "string"으로 수정합니다.
    "info_answer": {
      "type": "string",
      "description": "REQUIRED. If info=True, write a concise explanation of the dataset and its capabilities in the user's language. Never empty."
    }, 
    "confidence": {"type": "integer", "minimum": 0, "maximum": 10},
    "target_analysis": {
      "type": "string", 
      "enum": ["dataset", "population", "cnv", "cci", "deg", "go", "gsea", "marker_expression", "none"]
    },
    "plot_type": {
      "type": "string",
      "enum": ["dot", "heatmap", "umap", "violin", "bar", "box", "volcano", "table", "none"]
    },
    "pathway_phrase": {
      "type": ["string", "null"],
      "description": (
        "Short phrase for a named biological pathway explicitly mentioned by the user. "
        "Examples: 'cell cycle', 'TGF-beta signaling', 'WNT signaling pathway'. "
        "Set to null if flags.specific_pathway is false."
      )
    },      
    "need_context": {"type": "boolean"},
    "reason": {"type": "string"},
    "questions": {"type": "array", "items": {"type": "string"}}
  },
  "required": [
      "kind", "flags", "selected_tool", "info_answer", 
      "confidence", "target_analysis", "plot_type", 
      "need_context", "questions"
  ]
}


SYSTEM_ACTION_PLANNER = """
You are the SCODA-AI Strategic Action Planner. 
Your goal is to convert a user's analysis request into precise JSON arguments for one of the 10 specialized analytical functions.

[ANALYSIS TOOLSET]
- UMAP: plot_umap (Visualization of cell clusters)
- Population: plot_celltype_population (Bar charts for cell counts/proportions)
- DEG Bar: plot_degs (Differentially Expressed Genes analysis)
- GSEA/GO: plot_gsea_go (Gene Set/Pathway enrichment analysis)
- CCI Dot: plot_cci_dots (Cell-Cell Interaction patterns)
- CNV Heatmap: plot_cnv_heatmap (Copy Number Variation visualization)
- Marker Expression: plot_markers_and_expression_dot (Marker finding + expression dot plot)
- Violinplot: plot_violin_for_gene_expression_with_signif_difference (gene expression violin plot)
- Boxplot (Gene): plot_box_for_gene_expression_with_signif_difference (Sample-mean gene expression comparison)
- Boxplot (CCI): plot_box_for_cci_with_signif_difference (Sample-mean CCI comparison)
- Boxplot (Population): plot_box_for_celltype_population_with_signif_difference (Celltype proportion comparison)

[FUNCTIONAL SPECIFICATION]
{function_definition} 

Species-Specific Gene/Pathway Selection: If the query involves specific genes or pathways, identify relevant gene symbols (HUGO symbols) or Pathways specifically tailored to the species mentioned in the [DATA CONTEXT].
Use these genes when setting target_genes or relavant args.

[STRICT GENERATION RULES]
1. Target Identification: Look up 'celltype_minor', 'condition', or 'sample' values in the provided Data Context to ensure exact string matching for 'target_cells', 'target_genes', and 'targets'.
2. Statistical Reference: For all Boxplot functions, you MUST identify a 'ref_group' (e.g., 'Normal', 'Control', or 'Healthy') from the Data Context only if specified by the user.
3. Parameter Mapping: 
   - Mapping 'T cells' -> find all matching subtypes in celltype_minor.
   - Mapping 'CCI keywords' -> put into 'target_genes' list.
4. Default Policy: Use the default values from the @dataclass for any parameter not explicitly requested. NEVER use null/None.
5. Mode Selection: For GSEA/GO, choose 'plot_type' ("bar" or "dot") based on the number of cell types (multiple cells -> "dot" is preferred).
6. SCHEMA COMPLIANCE (CRITICAL):
   - Output JSON MUST contain only keys defined in the provided response schema.
   - Do NOT invent new keys. If a parameter is not explicitly requested, omit it entirely.
7. Species-Specific Gene / Pathway Selection:
   - If the user query involves specific genes, markers, or pathways, you MUST identify
     the appropriate gene symbols or pathway names that are compatible with the species
     indicated in the [DATA CONTEXT].
   - Use canonical gene symbols (e.g., HUGO symbols for human, MGI symbols for mouse).
   - Only select genes or pathways that are:
       (a) explicitly mentioned by the user, OR
       (b) strongly implied by the biological context AND present in the DATA CONTEXT.
   - When setting `target_genes` or pathway-related arguments, prefer species-consistent
     identifiers already observed in the dataset.
   - If species information is ambiguous or missing, assume the species used in the
     DATA CONTEXT and do NOT invent cross-species gene names.
"""

SYSTEM_ACTION_PLANNER = """
You are the SCODA-AI Strategic Action Planner.
Convert the user's request into schema-valid JSON arguments for the selected tool.

[FUNCTIONAL SPECIFICATION]
{function_definition}

[GLOBAL RULES — STRICT]
- Output ONLY valid JSON matching the response schema.
- Use ONLY keys defined in the schema. Do NOT invent keys.
- Do NOT output null / None. Omit optional fields if not requested.
- Use dataclass defaults implicitly.

[TARGET MATCHING]
- Cell types / conditions / samples must EXACTLY match values in DATA CONTEXT.
- Expand broad labels (e.g. "T cells") to matching subtypes in `celltype_minor` when applicable.
- Do NOT guess missing labels; ask clarification via `questions` if schema allows.

[GENE SYMBOL RULE — CRITICAL]
- `target_genes` MUST be concrete gene symbols.
- NEVER output prefixes or keywords as gene names.
  ❌ ["ITG"], ["COL"], ["CXCL"], ["HLA"], ["MMP"]
- If the user mentions a gene family or pathway (e.g. “integrin-related”),
  EXPAND it into a list of canonical gene symbols appropriate for the species in DATA CONTEXT.
- Assume species from DATA CONTEXT if not explicitly stated.
- If the user query involves specific genes or proteins, you MUST identify
  the appropriate gene symbols that are compatible with the species indicated in the [DATA CONTEXT].

[CANONICAL DEFAULT — USE WHEN ASKED]
- Human integrins:
  ITGA1, ITGA2, ITGA3, ITGA4, ITGA5, ITGA6, ITGA7, ITGA8, ITGA9, ITGA10, ITGA11, ITGAE, ITGAL, ITGAM, ITGAV, ITGAX, ...
- Mouse integrins:
  Itga1, Itga2, Itga3, Itga4, Itga5, Itga6, Itga7, Itga8, Itga9, Itga10, Itga11, Itgae, Itgal, Itgam, Itgav, Itgax, ...

[TOOL-SPECIFIC]
- plot_cci_dots:
  If user asks for “integrin-related interactions”, set `target_genes`
  to the expanded integrin gene list (not prefixes).

[FINAL CHECK]
- JSON only
- No nulls
- No prefixes in `target_genes`
"""


EXPLAIN_RESULT_PROMPT = """
You are an expert Scientist in Bioinformatics/Biology/Medicine. Interpret the following analysis results with biological/medical insight and technical precision.

[DATA CONTEXT]
{data_context}

[ANALYSIS INFORMATION]
- User Query: {user_query}
- Tool Used: {target_tool}
- Parameters Applied: {ai_args}

[INSTRUCTIONS]
1. Visual Interpretation: Describe key features observed in the provided visualization(s), if any.
2. Table/Text Interpretation: If tabular/text summaries are provided, interpret key patterns and notable signals.
3. Biological Reasoning: Connect findings with the provided data context (obs/uns metadata) to derive meaningful biological conclusions.
4. Tone & Audience: Professional yet accessible, as if explaining to a collaborator. Respond in Korean.
5. Language: follow the one in user_query.

[OUTPUT FORMAT]
# **[Core Analysis Title Here]**

When explaining analysis results:
- Start with a clear, bold title summarizing the core theme.
- Use bullet points / structured sections.
- Use Markdown section headers (##) for major sections
- Always format section titles in bold or as headers
- Do NOT use plain list items for section titles
- Structure as:
## Analysis Overview 
## Visual Summary
## Biological Interpretation
## Clinical Implications
"""

EXPLAIN_GENERAL_PROMPT = """
You are a senior expert in biology and medicine. Provide a comprehensive response to the user's query based on high-level scientific expertise.

[DATA CONTEXT]
{data_context}

[ANALYSIS INFORMATION]
- User Query: {user_query}

[INSTRUCTIONS]
1. Advanced Knowledge Integration:
   - Answer using strong biological/medical reasoning.
   - If you are not actually retrieving external papers here, do NOT fabricate specific citations/titles/years.
   - Instead, summarize commonly reported recent trends at a high level.
2. Species-Specific Gene Mapping:
   - If the query involves specific genes/pathways, list 10–20 relevant gene symbols (HUGO symbols).
   - If species is unclear in [DATA CONTEXT], assume human and state the assumption explicitly.
3. Structural Depth: three sections:
   - **Current Global Trends**
   - **Core Scientific Debates**
   - **Future Perspectives**
4. Formatting:
   - Large, bold title for each section.
   - Professional, academic, pedagogical tone.
5. Language: Korean.

[OUTPUT FORMAT]
# **[Main Academic Title Here]**

## **[Section Title: Trends]**
(Content here...)

## **[Section Title: Core Issues]**
(Content here...)

## **[Section Title: Outlook]**
(Content here...)
"""

EXPLAIN_GENERAL_PROMPT = """
You are a senior expert in biology and medicine. Provide a comprehensive response to the user's query based on high-level scientific expertise.

[DATA CONTEXT]
{data_context}

[ANALYSIS INFORMATION]
- User Query: {user_query}

[INSTRUCTIONS]
1. Advanced Knowledge Integration:
   - Answer using strong biological/medical reasoning.
   - If you are not actually retrieving external papers here, do NOT fabricate specific citations/titles/years.
   - Instead, summarize commonly reported recent trends at a high level.
2. Species-Specific Gene Mapping:
   - If the query involves specific genes/pathways, list 10–20 relevant gene symbols (HUGO symbols).
   - If species is unclear in [DATA CONTEXT], assume human and state the assumption explicitly.
3. Language: follow the one in user_query.
"""

###########################################
## Generate Tool default args
###########################################
import inspect
from dataclasses import asdict, is_dataclass
from copy import deepcopy

def _to_plain(v):
    if is_dataclass(v):
        return asdict(v)
    return deepcopy(v)

def build_tool_defaults_v3(tool_funcs: dict, Tool_config_map: dict) -> dict:
    """
    함수 시그니처 + Tool_config_map을 이용해 TOOL_DEFAULTS 자동 생성
    """
    TOOL_DEFAULTS = {}
    for tool_name, fn in tool_funcs.items():
        sig = inspect.signature(fn)
        cfg_map = Tool_config_map.get(tool_name, {})
        d = {}

        for p in sig.parameters.values():
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue

            pname = p.name

            # config param이면 dataclass default 인스턴스 생성
            if pname in cfg_map:
                cfg_cls = cfg_map[pname]
                d[pname] = _to_plain(cfg_cls())   # dict 형태로 저장(표시용)
                continue

            # 일반 param: 함수 default 사용
            if p.default is not inspect._empty:
                d[pname] = _to_plain(p.default)

        TOOL_DEFAULTS[tool_name] = d

    return TOOL_DEFAULTS


###########################################
### Merge Args from AI to default Args
###########################################

def _asdict_safe(x):
    if is_dataclass(x):
        return asdict(x)
    return x

def deep_merge(defaults: dict, patch: dict) -> dict:
    out = dict(defaults or {})
    if not isinstance(patch, dict):
        return out

    for k, v in patch.items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def coerce_tool_configs(tool_name: str, args: dict, Tool_config_map: dict) -> dict:
    """
    Tool_config_map 기준으로 args 내 nested config dict를 dataclass로 변환.
    - None이면 key 제거 (함수 default 사용)
    - dict이면 dataclass(**dict)
    - 이미 dataclass면 그대로
    """
    cfg_map = Tool_config_map.get(tool_name, {})
    out = dict(args or {})

    for key, cls in cfg_map.items():
        if key not in out:
            continue
        v = out[key]

        if v is None:
            del out[key]
            continue

        if is_dataclass(v):
            continue

        if isinstance(v, dict):
            out[key] = cls(**v)
        else:
            del out[key]

    return out

def materialize_tool_args(tool_name: str, ai_args: dict, TOOL_DEFAULTS: dict, Tool_config_map: dict):
    # 1) 표시/로그/UI용: 전부 dict로 채워진 full args
    full_args_dict = deep_merge(TOOL_DEFAULTS.get(tool_name, {}), ai_args or {})

    # 2) 실행용: config만 dataclass로 변환
    exec_args = coerce_tool_configs(tool_name, full_args_dict, Tool_config_map)

    return full_args_dict, exec_args



###########################################
### SCODIA main class
###########################################

import base64, io, json, re, time
from openai import OpenAI

# Gemini (new SDK)
from google.genai import types
from google import genai

from IPython.display import Image, Markdown, display, HTML
from typing import Any, Dict, List, Optional, Literal, Tuple, Union

# -----------------------------
# 3) Main class
# -----------------------------
try:
    from jsonschema import validate as jsonschema_validate
    from jsonschema import ValidationError as JSONSchemaValidationError
except Exception:
    jsonschema_validate = None
    JSONSchemaValidationError = Exception

from dataclasses import dataclass
from typing import Any, Dict, Optional

import inspect

def detect_output_language(user_query: str):
    """
    Returns: "ko" | "en"
    """
    q = user_query.lower()

    # 1. 명시적 언어 지시 (최우선)
    if re.search(r"(영어|english)", q):
        return "en"
    if re.search(r"(한글|한국어|korean)", q):
        return "ko"

    # 2. 질문 언어 기반 heuristic
    if re.search(r"[가-힣]", user_query):
        return "ko"

    return "en"


def filter_kwargs_for_fn(fn, kwargs: dict) -> dict:
    sig = inspect.signature(fn)
    allowed = set(sig.parameters.keys())
    return {k: v for k, v in kwargs.items() if k in allowed}


@dataclass
class LLMResult:
    content: Any                       # str | dict | list
    usage: Dict[str, int]              # {"input_tokens":..., "output_tokens":..., "total_tokens":...}
    raw: Any = None                    # provider raw response (optional)
    provider: str = ""                 # "openai" | "gemini"
    model: str = ""

def GET_DEF_FOR(target_function_name):
    return FUNCTION_DEF_REGISTRY[target_function_name]

def drop_nones(obj):
    if isinstance(obj, dict):
        return {k: drop_nones(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [drop_nones(v) for v in obj]
    return obj

def _extract_json_object(text: str) -> str:
    """
    Tries to extract the first JSON object/array from a string.
    Handles ```json ... ``` fences and extra prose.
    """
    if text is None:
        return ""

    s = text.strip()

    # 1) Strip markdown code fences if present
    # ```json\n...\n```
    if s.startswith("```"):
        # remove first fence line
        s = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", s)
        # remove trailing fence
        s = re.sub(r"\s*```$", "", s).strip()

    # 2) Fast path: already pure JSON object/array
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        return s

    # 3) Extract first {...} or [...]
    m = re.search(r"(\{.*\}|\[.*\])", s, flags=re.DOTALL)
    return m.group(1).strip() if m else s


PATHWAY_RESOLVER_SCHEMA_MIN = {
  "type": "object",
  "properties": {
    "kind": {"type": "string", "enum": ["pathway_resolver"]},
    "query_raw": {"type": "string"},
    "selected_pathway": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "needs_clarification": {"type": "boolean"},
    "clarifying_question": {"type": "string"}
  },
  "required": [
    "kind",
    "query_raw",
    "selected_pathway",
    "confidence",
    "needs_clarification",
    "clarifying_question"
  ]
}

PATHWAY_RESOLVER_PROMPT_MIN = """
You are a strict Pathway Name Resolver.
Return ONLY valid JSON matching the schema. No markdown.

Task:
- Choose EXACTLY ONE pathway name from the provided candidate_pathways list
  that best matches the user's pathway phrase.

Hard rules:
1) selected_pathway MUST be one of candidate_pathways (exactly as written).
2) Prefer direct string/normalized matches:
   - ignore case, extra spaces, punctuation, hyphens
   - you may remove generic suffix words like "pathway" if it helps
3) If ambiguous, still choose the best guess, set needs_clarification=true,
   and ask ONE short Korean question.

user_phrase:
{user_phrase}

candidate_pathways (allowed list):
{candidate_pathways_json}
""".strip()

EXTRA_CONTEXT_FOR_TARGET_GENES = """
[RESOLVED_PATHWAY_CONTEXT]
- User mentioned pathway phrase: "{pathway_phrase}"
- The phrase was resolved to the following known pathway: "{selected_pathway}"
- This pathway was selected from a predefined pathway database.
- The following gene set is FINAL and MUST be used for gene selection:
  {selected_genes}
- Do NOT re-infer or modify this gene list.
"""

class scodia:

    def __init__(self, api_key=None, model_to_use="gpt-5", adata=None,
                 TOOL_FUNCS: dict = None, TOOL_DEFAULTS: dict = None, 
                 Tool_config_map: dict = None, max_retries: int = 1):
        self.set_api_key(api_key, model_to_use, adata, TOOL_FUNCS, 
                         TOOL_DEFAULTS, Tool_config_map, max_retries)
        return

    def set_api_key(self, api_key, model_to_use="gemini-2.5-flash", adata=None,
                    TOOL_FUNCS: dict = None, TOOL_DEFAULTS: dict = None, 
                    Tool_config_map: dict = None, max_retries: int = 1):
        self.api_key = api_key
        self.model_name = model_to_use
        self.adata = adata

        if model_to_use.startswith("gemini"):
            # Google GenAI client
            self.client = genai.Client(api_key=api_key)
        else:
            # OpenAI client
            self.client = OpenAI(api_key=api_key)

        self.data_context = get_data_context(adata)

        self.Tool_config_map = Tool_config_map
        self.Tool_funcs = TOOL_FUNCS
        self.tool_defaults = build_tool_defaults_v3(TOOL_FUNCS, Tool_config_map)
        self.max_retries = max_retries

        return

    # =========================================================
    # Helpers
    # =========================================================
    def _combine_role(self, system_message: str = "", data_context: str = "") -> str:
        return ((system_message or "") + (data_context or "")).strip()

    def _build_prompt(self, user_query: str, role: str = "") -> str:
        prompt = ""
        if role:
            prompt += role.strip() + "\n\n"
        prompt += (user_query or "").strip()
        return prompt

    def _normalize_images(self, images_base64: Optional[List[str]]) -> Optional[List[str]]:
        """
        Accepts:
          - pure base64
          - data URL: data:image/png;base64,....
        Returns:
          - list of pure base64 strings
        """
        if not images_base64:
            return None
        out = []
        for s in images_base64:
            if not s:
                continue
            s = s.strip()
            if s.startswith("data:") and "base64," in s:
                s = s.split("base64,", 1)[1]
            out.append(s)
        return out or None

    def _normalize_text_parts(self, text_parts: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        """
        Optional extra text parts (e.g., df.to_markdown()) to be fed along with prompt & images.
        """
        if text_parts is None:
            return None
        if isinstance(text_parts, str):
            return [text_parts]
        # list/tuple
        return [str(x) for x in text_parts if x is not None] or None

    # =========================================================
    # Gemini call (TEXT + optional IMAGES + optional EXTRA TEXT + optional schema)
    # =========================================================
    def _norm_usage_gemini(self, resp) -> Dict[str, int]:
        # Gemini는 보통 usage_metadata / usageMetadata 쪽에 토큰 카운트가 있음
        md = getattr(resp, "usage_metadata", None) or getattr(resp, "usageMetadata", None) or None
        if md is None and isinstance(resp, dict):
            md = resp.get("usage_metadata") or resp.get("usageMetadata")
    
        def _get(x, *names, default=0):
            if x is None:
                return default
            if isinstance(x, dict):
                for n in names:
                    if n in x and x[n] is not None:
                        return int(x[n])
                return default
            for n in names:
                v = getattr(x, n, None)
                if v is not None:
                    return int(v)
            return default
    
        in_tok = _get(md, "prompt_token_count", "promptTokenCount", "input_token_count", "inputTokenCount", default=0)
        out_tok = _get(md, "candidates_token_count", "candidatesTokenCount", "output_token_count", "outputTokenCount", default=0)
        tot = _get(md, "total_token_count", "totalTokenCount", default=(in_tok + out_tok))
    
        return {"input_tokens": int(in_tok), "output_tokens": int(out_tok), "total_tokens": int(tot)}

    def _ask_gemini(
        self,
        user_query: str,
        role: str = "",
        schema: dict | None = None,
        *,
        images_base64: Optional[List[str]] = None,
        extra_text_parts: Optional[Union[str, List[str]]] = None,
        image_mime: str = "image/png",
    ) -> LLMResult:
        
        prompt = self._build_prompt(user_query, role)
        images_base64 = self._normalize_images(images_base64)
        extra_texts = self._normalize_text_parts(extra_text_parts)

        # Gemini expects "contents" which can be: [text, Part(image), text, ...]
        contents: List[Any] = [prompt]

        if extra_texts:
            for t in extra_texts:
                if t and str(t).strip():
                    contents.append(str(t))

        if images_base64:
            for b64_data in images_base64:
                if b64_data:
                    img_part = types.Part.from_bytes(
                        data=base64.b64decode(b64_data),
                        mime_type=image_mime
                    )
                    contents.append(img_part)

        try:
            if schema is None:
                cfg = types.GenerateContentConfig()
                resp = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=cfg,
                )
                # content(text) 추출 (기존 방식)
                out_text = getattr(resp, "text", None)
                if out_text is None:
                    out_text = str(resp)
            
                usage = self._norm_usage_gemini(resp)
            
                return LLMResult(
                    content=out_text,
                    usage=usage,
                    raw=resp,
                    provider="gemini",
                    model=str(self.model_name),
                )            
                # return resp.text

            cfg = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            )
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=cfg,
            )
            # content(text) 추출 (기존 방식)
            out_text = getattr(resp, "text", None)
            if out_text is None:
                out_text = str(resp)
        
            usage = self._norm_usage_gemini(resp)
        
            return LLMResult(
                content=out_text,
                usage=usage,
                raw=resp,
                provider="gemini",
                model=str(self.model_name),
            )            
            # return json.loads(resp.text)

        except Exception as e:
            import traceback
            print("❌ _ask_gemini error:", type(e).__name__, str(e))
            traceback.print_exc()
            print("---- schema keys ----")
            if isinstance(schema, dict):
                print(list(schema.keys()))
            print("---- resp.text (if any) ----")
            try:
                print(resp.text[:500])
            except Exception:
                pass
            raise

    # =========================================================
    # GPT call (OpenAI) - TEXT only (kept as-is)
    # NOTE:
    # - For images you can later switch this to Responses API with input_image.
    # - For now, images/extra_text just get appended into the prompt text for GPT.
    # =========================================================

    def _norm_usage_openai(self, usage_obj) -> Dict[str, int]:
        # usage_obj가 dict이든 pydantic object든 섞일 수 있으니 방어적으로
        if usage_obj is None:
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
        if isinstance(usage_obj, dict):
            in_tok = int(usage_obj.get("input_tokens") or usage_obj.get("prompt_tokens") or 0)
            out_tok = int(usage_obj.get("output_tokens") or usage_obj.get("completion_tokens") or 0)
            tot = int(usage_obj.get("total_tokens") or (in_tok + out_tok))
            return {"input_tokens": in_tok, "output_tokens": out_tok, "total_tokens": tot}
    
        # attribute-style
        in_tok = int(getattr(usage_obj, "input_tokens", getattr(usage_obj, "prompt_tokens", 0)) or 0)
        out_tok = int(getattr(usage_obj, "output_tokens", getattr(usage_obj, "completion_tokens", 0)) or 0)
        tot = int(getattr(usage_obj, "total_tokens", (in_tok + out_tok)) or (in_tok + out_tok))
        return {"input_tokens": in_tok, "output_tokens": out_tok, "total_tokens": tot}

        
    def _ask_gpt(
        self,
        user_query: str,
        role: str = "",
        schema: dict | None = None,
        *,
        images_base64: Optional[List[str]] = None,
        extra_text_parts: Optional[Union[str, List[str]]] = None,
        system_message: str = "",
        data_context: str = "",
        image_mime: str = "image/png",  # "image/jpeg" also OK
    ) -> "LLMResult":
        """
        OpenAI Responses API wrapper (text + optional images).
        - If schema is not None: expects JSON-only output and parses json.loads.
        - If schema is None: returns plain text.
        """
    
        # -----------------------------
        # 1) Build prompt text
        # -----------------------------
        parts: List[str] = []
        if system_message:
            parts.append(system_message.strip())
        if data_context:
            parts.append("[DATA CONTEXT]\n" + data_context.strip())
        if role:
            parts.append(f"[ROLE]\n{role.strip()}")
        parts.append("[USER]\n" + user_query.strip())
    
        if extra_text_parts:
            if isinstance(extra_text_parts, str):
                parts.append(extra_text_parts)
            else:
                parts.extend([str(x) for x in extra_text_parts])
    
        prompt = "\n\n".join([p for p in parts if p])
    
        # -----------------------------
        # 2) Build multimodal content
        # -----------------------------
        content: List[dict] = [{"type": "input_text", "text": prompt}]
    
        # Attach images (base64 strings, without the "data:image/...;base64," prefix)
        if images_base64:
            for b64 in images_base64:
                if not b64:
                    continue
                content.append({
                    "type": "input_image",
                    "image_url": f"data:{image_mime};base64,{b64}",
                })
    
        # Responses API input format
        messages = [{"role": "user", "content": content}]
    
        # -----------------------------
        # 3) Call API
        # -----------------------------
        resp = self.client.responses.create(
            model=str(self.model_name),
            input=messages,
        )
    
        # Extract text safely
        out_text = (getattr(resp, "output_text", None) or "").strip()
        usage = self._norm_usage_openai(getattr(resp, "usage", None))
    
        # -----------------------------
        # 4) Parse (JSON vs text)
        # -----------------------------
        if schema is not None:
            try:
                content_parsed: Any = json.loads(out_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    "GPT did not return valid JSON.\n"
                    f"error={e}\n"
                    f"first500={out_text[:500]}"
                )
            return LLMResult(
                content=content_parsed,
                usage=usage,
                raw=resp,
                provider="openai",
                model=str(self.model_name),
            )
    
        return LLMResult(
            content=out_text,
            usage=usage,
            raw=resp,
            provider="openai",
            model=str(self.model_name),
        )
    
    # =============================================================
    # Unified entry (now supports images_base64 + extra_text_parts)
    # =============================================================
    def ask_inner(
        self,
        user_query: str,
        *,
        schema: dict = None,
        system_message: str = "",
        data_context: str = "",
        images_base64: Optional[List[str]] = None,
        extra_text_parts: Optional[Union[str, List[str]]] = None,
        image_mime: str = "image/png",
    ) -> LLMResult:
        role = self._combine_role(system_message, data_context)
    
        if str(self.model_name).startswith("gemini"):
            return self._ask_gemini(
                user_query,
                role,
                schema=schema,
                images_base64=images_base64,
                extra_text_parts=extra_text_parts,
                image_mime=image_mime,
            )
    
        return self._ask_gpt(
            user_query,
            role,
            schema=schema,
            images_base64=images_base64,
            extra_text_parts=extra_text_parts,
            image_mime=image_mime,
        )    

    # ===========================================================
    # JSON Enforced Call (post-validate + retry) - model agnostic
    # ===========================================================
    def _json_enforced_call(
        self,
        user_query: str,
        *,
        schema: dict,
        system_message: str = "",
        data_context: str = "",
        max_retries: int = 2,
    ) -> LLMResult:
    
        schema_text = json.dumps(schema, ensure_ascii=False)
        json_contract = (
            "\n\n"
            "=== OUTPUT CONTRACT (VERY IMPORTANT) ===\n"
            "You MUST return ONLY valid JSON.\n"
            "Do NOT include markdown, explanations, or extra keys.\n"
            "The JSON must conform EXACTLY to the provided JSON schema.\n"
            "If you cannot comply, internally fix your output and return only corrected JSON.\n"
            "=== END CONTRACT ===\n"
            f"JSON_SCHEMA:\n{schema_text}\n"
        )
    
        base_system = (system_message or "") + json_contract
        prompt_user = user_query
    
        last_err = None
        last_raw = None
    
        # (선택) 시도별 토큰 누적해서 로그/모니터링에 쓰고 싶으면
        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
        for attempt in range(max_retries + 1):
            res = self.ask_inner(
                prompt_user,
                schema=None,
                system_message=base_system,
                data_context=data_context,

            )
    
            for k in total_usage:
                total_usage[k] += int(res.usage.get(k, 0))
    
            raw = res.content
            if isinstance(raw, (dict, list)):
                data = raw
                last_raw = json.dumps(raw, ensure_ascii=False)
            else:
                last_raw = (raw or "").strip()
                try:
                    # data = json.loads(last_raw)
                    candidate = _extract_json_object(last_raw)
                    data = json.loads(candidate)

                except Exception as e:
                    last_err = e
                    data = None
    
            if data is not None:
                try:
                    data = drop_nones(data)
                    jsonschema_validate(instance=data, schema=schema)
                    return LLMResult(
                        content=data,
                        usage=total_usage,
                        raw={"attempts": attempt + 1},   # optional
                        provider=res.provider,
                        model=res.model,
                    )
                except Exception as e:
                    last_err = e
    
            prompt_user = (
                "Your previous output did not conform to the schema.\n\n"
                f"[VALIDATION_ERROR]\n{type(last_err).__name__}: {str(last_err)}\n\n"
                f"[YOUR_PREVIOUS_OUTPUT]\n{last_raw}\n\n"
                "Now regenerate ONLY the corrected JSON that conforms EXACTLY to the schema. "
                "No markdown, no extra keys."
            )
    
        raise RuntimeError(
            f"Failed to produce schema-valid JSON after retries. "
            f"Last error: {type(last_err).__name__}: {str(last_err)}\n"
            f"Last output: {str(last_raw)[:800]}"
        )


    # ========================================================================
    # Explain on images (now uses ask_inner with images + optional extra text)
    # ========================================================================
    def explain_analysis_result(self, target_tool, ai_args, result_data, user_query):
        images = []
        extra_texts = []

        # Flexible extraction:
        # - str: could be image_base64 or text; assume image if it looks base64-ish? Here keep old behavior: str treated as image.
        if isinstance(result_data, str):
            images.append(result_data)

        elif isinstance(result_data, list):
            for item in result_data:
                if isinstance(item, str):
                    images.append(item)
                elif isinstance(item, dict):
                    img = item.get('img_base64')
                    if img:
                        images.append(img)
                    txt = item.get('text')
                    if txt:
                        extra_texts.append(str(txt))

        elif isinstance(result_data, dict):
            img = result_data.get('img_base64')
            if img:
                images.append(img)
            txt = result_data.get('text')
            if txt:
                extra_texts.append(str(txt))

        if not images and not extra_texts:
            return None # "해석할 이미지/텍스트 데이터가 없습니다."

        prompt = EXPLAIN_RESULT_PROMPT.format( data_context = self.data_context,
                                               user_query = user_query,
                                               target_tool = target_tool,
                                               ai_args = ai_args).strip()
                                               
        start_time = time.time()
        print(f'✅ Calling {self.model_name} for explanation .. ', end='')
        
        # One unified call (Gemini: multimodal; GPT: text-only)
        out = self.ask_inner(
            prompt,
            schema=None,
            system_message="",
            data_context="",
            images_base64=images if images else None,
            extra_text_parts=extra_texts if extra_texts else None,
        )

        end_time = time.time()
        print(f"done ({(end_time - start_time):.2f}), {list(out.usage.values())}")

        # Keep downstream compatibility: Gemini returns text via string in our ask_inner (for schema=None),
        # while original gemini response object has .text. To keep your render_scoda_explanation(explanation.text),
        # we wrap text into a tiny object.
        # class _Resp:
        #     def __init__(self, text): self.text = text
        # return _Resp(out)

        class _Resp:
            def __init__(self, text, usage):
                self.text = text
                self.usage = usage        
        # return _Resp(out.content, out.usage)  
        return out

    # ================================================================
    # General explanation (text-only, but via ask_inner unified entry)
    # ================================================================
    def explain_in_general_sense(self, user_query):

        prompt = EXPLAIN_GENERAL_PROMPT.format(user_query = user_query, 
                                               data_context = self.data_context).strip()
        start_time = time.time()
        print(f'✅ Calling {self.model_name} for explanation .. ', end='')
        
        out = self.ask_inner(prompt, schema=None)
        
        end_time = time.time()
        print(f"done ({(end_time - start_time):.2f}), {list(out.usage.values())}")

        # class _Resp:
        #     def __init__(self, text): self.text = text
        # return _Resp(out)

        class _Resp:
            def __init__(self, text, usage):
                self.text = text
                self.usage = usage        
        # return _Resp(out.content, out.usage)  
        return out

    # =========================================================
    # Dynamic parameter generation (JSON enforced)
    # =========================================================

    def generate_parameters_260128(self, target_function_name, user_query):
        data_context = self.data_context
        try:
            selected_schema = SCHEMA_REGISTRY[target_function_name]
            prompt = SYSTEM_ACTION_PLANNER.format(
                function_definition=GET_DEF_FOR(target_function_name)
            )
    
            if selected_schema is None:
                print(f"❌ No schema for tool: {target_function_name}")
                return None
                
            start_time = time.time()
            print(f'✅ Calling {self.model_name} to get args to {target_function_name} .. ', end='')
    
            res = self._json_enforced_call(
                user_query,
                schema=selected_schema,
                system_message=prompt,
                data_context=data_context,
                max_retries=self.max_retries,
            )
    
            end_time = time.time()
    
            spec = res.content
            usage = res.usage
            print(f"done ({(end_time - start_time):.2f}), {list(usage.values())}")
    
        except Exception as e:
            print(f'Tool name {target_function_name} not available. ({type(e).__name__}: {e})')
            spec = None
            usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            res = None
            
            import traceback
            print(f"❌ generate_parameters failed for tool={target_function_name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            return None        
        
        # ✅ 기존 호환 유지가 필요하면 spec만 리턴하고, usage는 self에 저장하는 것도 가능
        # self.last_usage = usage
    
        # return spec, usage
        return res


    def generate_parameters(self, target_function_name, user_query, *, extra_overrides=None, extra_context=None):
        data_context = self.data_context
        try:
            selected_schema = SCHEMA_REGISTRY[target_function_name]
            prompt = SYSTEM_ACTION_PLANNER.format(
                function_definition=GET_DEF_FOR(target_function_name)
            )
    
            if selected_schema is None:
                print(f"❌ No schema for tool: {target_function_name}")
                return None
    
            # ✅ LLM에게 힌트로 추가 컨텍스트를 'data_context'에 합침
            if extra_context:
                data_context = (data_context or "") + "\n\n" + extra_context.strip() + "\n"
    
            start_time = time.time()
            print(f'✅ Calling {self.model_name} to get args to {target_function_name} .. ', end='')
    
            res = self._json_enforced_call(
                user_query,
                schema=selected_schema,
                system_message=prompt,
                data_context=data_context,
                max_retries=self.max_retries,
            )
    
            end_time = time.time()
            spec = res.content
            usage = res.usage
            print(f"done ({(end_time - start_time):.2f}), {list(usage.values())}")
    
            # ✅ 강제 주입(LLM 출력이 뭐든 override를 우선 적용)
            if isinstance(extra_overrides, dict) and isinstance(spec, dict):
                spec = deep_merge(spec, extra_overrides)   # 또는 deep_merge(extra_overrides, spec) 아님! override가 덮어써야 함
                res.content = spec  # LLM_res 객체에 다시 넣어줌 (가능하다면)
    
            return res
    
        except Exception as e:
            print(f'Tool name {target_function_name} not available. ({type(e).__name__}: {e})')
            import traceback
            print(f"❌ generate_parameters failed for tool={target_function_name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            return None
    
    # =================================================================================
    # Unified ask() with routing (routing call via _json_enforced_call; rest unchanged)
    # =================================================================================
    def ask(self, user_query: str, auto_render: bool = True, verbose = False):

        lang = detect_output_language(user_query)

        res = {'query': user_query}
        res_to_user = {'query': user_query }
        total_usage = 0
        
        # ------------------------------------- #
        # ---- Router call (JSON enforced) ---- #
        # ------------------------------------- #
        start_time = time.time()
        print(f'✅ Calling {self.model_name} .. ', end='')

        prompt = ROUTER_PROMPT
        schema = ROUTER_SCHEMA
        LLM_res = self._json_enforced_call(
            user_query,
            schema=schema,
            system_message=prompt,
            data_context=self.data_context,
            max_retries=self.max_retries,
        )
        end_time = time.time()

        spec = LLM_res.content
        usage = LLM_res.usage
        model = LLM_res.provider
        total_usage += usage['total_tokens']
        print(f"done ({(end_time - start_time):.2f}), {list(usage.values())}")

        if verbose: print(spec)
        res['router_res'] = spec

        # return spec
        if spec['flags']['info']:
            render_scoda_info(spec['info_answer'], lang=lang)

        # render_gemini_questions(spec["questions"])
        if spec['info_answer']: 
            res_to_user['info'] = spec['info_answer']

        # ------------------------------------------------------------- #
        # ---- Plotting function args request call (JSON enforced) ---- #
        # ------------------------------------------------------------- #

        plot_result = None
        ai_generated_args = None
        target_function_name = None

        if spec['flags']["plot"]:

            res_to_user['plot_func'] = spec['selected_tool']
            target_function_name = spec['selected_tool']
            selected_schema = SCHEMA_REGISTRY[target_function_name]

            # -------------------------------------------------------------------
            #-- Check if the user mentions specific pathway for gene selection.
            # -------------------------------------------------------------------
            selected_genes = []
            if spec['flags']["specific_pathway"]:
                
                start_time = time.time()
                print(f'✅ Calling {self.model_name} to resolve pathways .. ', end='')
    
                pathway_phrase = spec["pathway_phrase"]
                candidate_pathways=list(self.adata.uns["Pathways_DB"].keys())
                prompt = PATHWAY_RESOLVER_PROMPT_MIN.format(
                    user_phrase=pathway_phrase,
                    candidate_pathways_json=json.dumps(candidate_pathways, ensure_ascii=False)
                )
                schema = PATHWAY_RESOLVER_SCHEMA_MIN
                LLM_res = self._json_enforced_call(
                    user_query,
                    schema=schema,
                    system_message=prompt,
                    data_context=self.data_context,
                    max_retries=self.max_retries,
                )
                end_time = time.time()
                spec_pw = LLM_res.content
                usage = LLM_res.usage
                model = LLM_res.provider
                total_usage += usage['total_tokens']
                print(f"done ({(end_time - start_time):.2f}), {list(usage.values())}. Selected PW: {spec_pw['selected_pathway']}")
    
                selected_pathway = spec_pw['selected_pathway']
                if not spec_pw["needs_clarification"]:
                    if selected_pathway in candidate_pathways:
                        selected_genes = list( self.adata.uns["Pathways_DB"][selected_pathway] )
                        # print(selected_genes)
                    else:
                        print(f"⚠️ WARNING: Pathway, {spec_pw['selected_pathway']}, not in the pathways list.")

            # ----------------------------------------------------#
            #-- Generate Arguments for plotting function to run --#
            # ----------------------------------------------------#
            if len(selected_genes) == 0:
                LLM_res = self.generate_parameters(target_function_name, user_query)
            else:
                extra_context = EXTRA_CONTEXT_FOR_TARGET_GENES.format(
                    pathway_phrase = pathway_phrase,
                    selected_pathway = selected_pathway,
                    selected_genes = selected_genes
                )
                LLM_res = self.generate_parameters(
                    target_function_name,
                    user_query,
                    extra_overrides={"target_genes": selected_genes},
                    extra_context=extra_context
                )

            ai_generated_args = LLM_res.content
            usage = LLM_res.usage
            model = LLM_res.provider
            total_usage += usage['total_tokens']
            
            full_args_dict, exec_args = materialize_tool_args(
                target_function_name,
                ai_generated_args,
                self.tool_defaults,
                self.Tool_config_map
            )

            res['plot_params'] = full_args_dict
            res_to_user['plot_params'] = full_args_dict
            
            if verbose: display_analysis_parameters(target_function_name, full_args_dict)

            # -------------------------------------------------- #
            # ---- Run plotting function & show the results ---- #
            # -------------------------------------------------- #
            start_time = time.time()
            print(f'🛠️ Generating plots .. ', end='')
        
            plot_fn = self.Tool_funcs[target_function_name]
            exec_args = filter_kwargs_for_fn(plot_fn, exec_args)
            plot_result = plot_fn(self.adata, **exec_args)            
            
            end_time = time.time()

            if plot_result is None or isinstance(plot_result, str):
                if isinstance(plot_result, str):
                    print(f"✅ Generating plots .. done ({(end_time - start_time):.2f}). {plot_result}")
            else:
                print(f"done ({(end_time - start_time):.2f})")
                res['plot_res'] = plot_result
                res_to_user['plot_res'] = plot_result

                # ------------------------------------------------------ #
                # ---- Generate Code-snippet to reproduce the image ---- #
                # ------------------------------------------------------ #
                code_snippet = ""
                if spec['flags']["plot"] and target_function_name and full_args_dict:
                    code_snippet = build_repro_code_snippet_clean(
                        target_function_name,
                        exec_args,
                        adata_var_name="adata_t",   # 네 노트북 변수명
                        result_var_name="result",
                        assume_imported=True,       # dataclass import 되어 있다고 했으니
                    )
                    res["plot_code"] = code_snippet
                    res_to_user['plot_code'] = code_snippet

                    if target_function_name == "plot_degs":
                        deg_dct_dct_df = plot_result["deg_summaries"]
                        for c in deg_dct_dct_df.keys():
                            print(f"=== Selected DEGs for {c} ===")
                            for case in deg_dct_dct_df[c].keys():
                                print(case)
                                display(deg_dct_dct_df[c][case])
                        

        # ---------------------------------------------------- #
        # ---- Table summary request call (Unified ask()) ---- #
        # ---------------------------------------------------- #
        elif spec['flags']["table_summary"]:
            pass

        # --------------------------------------------------- #
        # ---- Explanation request call (Unified ask())  ---- #
        # --------------------------------------------------- #
        if spec['flags']["explain_data"]:
            explanation = None
            result_payload = None

            if spec['flags']["plot"] and (plot_result is not None):
                result_payload = plot_result.get('img_base64', plot_result)
                LLM_res = self.explain_analysis_result(
                    target_function_name,
                    ai_generated_args,
                    result_payload,
                    user_query
                )
                if LLM_res is not None:
                    explanation = LLM_res.content
                    usage = LLM_res.usage
                    model = LLM_res.provider
                    total_usage += usage['total_tokens']
                    # print(usage)
                
                if explanation is not None:                
                    # ---- Show explanation ---- #
                    text = explanation # .text if hasattr(explanation, "text") else str(explanation)
                    full_markdown = render_scoda_explanation(text)
    
                    # ---- Creat MS doc and show download link ---- #
                    doc_buffer = create_doc_with_style(text, result_payload)
                    display(HTML(creat_download_link(doc_buffer, f"{user_query}.docx")))
                    print(' ')
        
                    res['explanation'] = explanation
                    res['total_usage'] = total_usage 
    
                    res_to_user['explanation'] = explanation
                    res_to_user['total_usage'] = total_usage 
    
        # --------------------------------------------------- #
        # ---- Explanation request call (Unified ask())  ---- #
        # --------------------------------------------------- #
        if spec['flags']["explain_general"]:
            explanation = None
            result_payload = None

            if (not spec['flags']["plot"]) and (not spec['flags']["table_summary"]):
                LLM_res = self.explain_in_general_sense(user_query)
                explanation = LLM_res.content
                usage = LLM_res.usage
                model = LLM_res.provider
                total_usage += usage['total_tokens']
                # print(usage)

            if explanation is not None:                
                # ---- Show explanation ---- #
                text = explanation # .text if hasattr(explanation, "text") else str(explanation)
                full_markdown = render_scoda_explanation(text)

                # ---- Creat MS doc and show download link ---- #
                doc_buffer = create_doc_with_style(text, result_payload)
                display(HTML(creat_download_link(doc_buffer, f"{user_query}.docx")))
                print(' ')
    
                res['explanation'] = explanation
                res['total_usage'] = total_usage 

                res_to_user['explanation'] = explanation
                res_to_user['total_usage'] = total_usage 
        
        # render_gemini_questions(spec["questions"])
        
        if spec['flags']["reportgen"]:
            print('Report generation comming soon')

        return res

