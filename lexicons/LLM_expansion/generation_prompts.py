"""
Prompt builder for theory-driven lexicon GENERATION (LLM-as-Lexicographer).

Design: rather than asking the LLM to enumerate a category in one shot
(which produces shallow, duplicative output), we run 7 sliced prompts per
category and union the results. Each slice asks for a specific
register or morphological subset.

Slices
------
    formal_single        Formal-register single tokens
    formal_phrase        Formal-register N-grams (>=2 tokens)
    colloquial_single    Colloquial / spoken single tokens
    colloquial_phrase    Colloquial N-grams
    domain_specific      Domain-anchored items (legal, academic, political...)
    archaic_literary     Archaic / literary register
    inflectional         Morphological variants of canonical seeds
Output schema (per item)
------------------------
    {
      "word": <str>,
      "register": "formal" | "colloquial" | "domain" | "archaic" | "neutral",
      "type": "single" | "phrase" | "inflection" | "antonym" | "boundary",
      "confidence": "high" | "medium" | "low",
      "rationale": <str>
    }

The prompt builder and post-processing schema retain an `is_hard_negative`
field for compatibility with separately flagged inputs, although the default
seven-slice configuration uses only positive generation slices.
"""
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Slice specs
# ---------------------------------------------------------------------------
SLICE_SPECS: Dict[str, Dict] = {
    "formal_single": {
        "instructions": (
            "Generate FORMAL-register SINGLE-WORD items. Targets: written, "
            "academic, legal, news-editorial, professional discourse. "
            "All items must be single tokens (no spaces). Set type='single'."
        ),
        "type_field": "single",
        "register_hint": "formal",
        "is_hard_negative": False,
        "target_count": 30,
    },
    "formal_phrase": {
        "instructions": (
            "Generate FORMAL-register N-GRAM items (multi-word expressions, "
            "fixed phrases, idiom-like locutions). Targets: 'in conclusion', "
            "'on the grounds that', 'it follows that'. Each item must contain "
            "at least one space (>=2 tokens). Set type='phrase'."
        ),
        "type_field": "phrase",
        "register_hint": "formal",
        "is_hard_negative": False,
        "target_count": 25,
    },
    "colloquial_single": {
        "instructions": (
            "Generate COLLOQUIAL / SPOKEN single-word items. Targets: spoken "
            "English, informal writing, social-media discourse. Include "
            "interjections, informal contractions where they function "
            "lexically (e.g., 'yeah', 'nah', 'totally'). All items single "
            "tokens. Set type='single'."
        ),
        "type_field": "single",
        "register_hint": "colloquial",
        "is_hard_negative": False,
        "target_count": 20,
    },
    "colloquial_phrase": {
        "instructions": (
            "Generate COLLOQUIAL / SPOKEN N-grams that DIRECTLY perform "
            "the rhetorical function of THIS category, expressed in casual "
            "register. Each item >=2 tokens.\n\n"
            "CRITICAL: Do NOT output generic conversational fillers, "
            "hedges, or topic-management phrases (e.g. 'you know what', "
            "'I mean', 'to be honest', 'at the end of the day', 'the "
            "bottom line is', 'that being said') unless they LITERALLY "
            "encode the category's function. These items belong to other "
            "PI categories (Filler, By.The.Way, etc.) — generating them "
            "here is category leakage.\n"
            "Test each candidate: 'If I delete the candidate from the "
            "sentence, does the {category} function disappear?' If the "
            "answer is no (the rhetorical function survives without it), "
            "do not output it.\n"
            "Examples of good output: for IMPACT_GAIN, 'pays off big', "
            "'comes out ahead', 'good deal'; for LOGIC_CAUSAL, 'that's "
            "why', 'that's because'.\n"
            "Set type='phrase'."
        ),
        "type_field": "phrase",
        "register_hint": "colloquial",
        "is_hard_negative": False,
        "target_count": 20,
    },
    "domain_specific": {
        "instructions": (
            "Generate items where THIS category's function appears in a "
            "specialised register (legal, academic, scientific, "
            "political, business). The item must still perform THIS "
            "category's rhetorical function — not a different one that "
            "happens to share the domain.\n\n"
            "CRITICAL: Do NOT mechanically reach for examples from other "
            "PI categories (e.g., academic stance verbs like 'postulate' "
            "or 'we contend' are ARG_CLAIM, not LOGIC_CAUSAL). Re-read "
            "the FUNCTION block above and confirm the candidate satisfies "
            "it. Mark the source domain in the rationale (e.g., 'legal', "
            "'academic'). type may be 'single' or 'phrase'."
        ),
        "type_field": "single_or_phrase",
        "register_hint": "domain",
        "is_hard_negative": False,
        "target_count": 20,
    },
    "archaic_literary": {
        "instructions": (
            "Generate items that perform the category function in a "
            "GENUINELY archaic, literary, or historically-marked register. "
            "Targets: items still encountered in religious, legal, or "
            "literary text but rare in modern conversational/journalistic "
            "prose.\n\n"
            "CRITICAL: Do NOT relabel modern, high-frequency items as "
            "archaic. 'therefore', 'hence', 'thus', 'reward', 'prosperity', "
            "'advantage' are common modern words; they are not archaic and "
            "should NOT appear in this slice. True archaic examples: "
            "'wherefore', 'verily', 'forsooth', 'whence', 'henceforth', "
            "'inasmuch as', 'thereupon', 'hereby'. If the category has no "
            "genuine archaic-register variants, output an EMPTY list — "
            "this is the correct answer for many categories. Quality over "
            "count. type='single' or 'phrase'."
        ),
        "type_field": "single_or_phrase",
        "register_hint": "archaic",
        "is_hard_negative": False,
        "target_count": 15,
    },
    "inflectional": {
        "instructions": (
            "Generate INFLECTIONAL / DERIVATIONAL VARIANTS of the canonical "
            "seeds and other category members. Include third-person -s, "
            "past -ed, gerund -ing, agent -er/-or, negation prefixes when "
            "they preserve function.\n\n"
            "CRITICAL: If the canonical seeds are CLOSED-CLASS items "
            "(connectives, modals, demonstratives, fixed phrases) that do "
            "not inflect, output an EMPTY list. Examples of categories "
            "where you should output nothing: LOGIC_CAUSAL ('because' / "
            "'therefore' / 'hence' do not inflect); LOGIC_CONTRAST; "
            "LOGIC_REFERENCE; SPEC_PSYCH_NEAR (deictic 'now' / 'here'); "
            "PROP_BANDWAGON ('everyone' as quantifier).\n"
            "Never invent non-existent forms like 'therefored' or "
            "'consequentlying'. Zero output is the correct answer when "
            "the category is non-inflectional.\n\n"
            "Only items whose function is genuinely preserved. Set "
            "type='inflection'."
        ),
        "type_field": "inflection",
        "register_hint": "neutral",
        "is_hard_negative": False,
        "target_count": 25,
    },
}


# ---------------------------------------------------------------------------
# System message
# ---------------------------------------------------------------------------
SYSTEM_MSG = """\
You are a computational linguist and corpus lexicographer. You are building lexicons for the Persuasion Index (PI) framework, which organises 50+ rhetorical categories under Aristotle's Logos / Ethos / Pathos.

Your task is theory-driven lexicon generation. For a given category, you receive:
  (1) the operational definition,
  (2) inclusion criteria,
  (3) exclusion criteria,
  (4) common drift traps,
  (5) canonical seed words,
  (6) a slice instruction telling you which subset to enumerate this turn.

Generate as many high-quality items as you can within the slice. Quality means: each item must satisfy the inclusion criteria AND not match any exclusion criterion.

Output STRICT JSON only — an object with a single key "items" containing an array. No prose, no markdown fences."""


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _format_list(items: List[str], indent: str = "  ") -> str:
    return "\n".join(f"{indent}- {x}" for x in items) if items else f"{indent}(none)"


def _format_traps(traps: List[Dict], indent: str = "  ") -> str:
    if not traps:
        return f"{indent}(none recorded)"
    lines = [f"{indent}- '{t['word']}' ({t['drift_type']}): {t['why']}" for t in traps]
    return "\n".join(lines)


def build_user_message(category: str, theory_def: Dict, slice_name: str) -> str:
    spec = SLICE_SPECS[slice_name]
    is_hn = spec["is_hard_negative"]

    # Hard-negative slices use a softer "hard-negative spec" framing,
    # admit-anchor / strict-exclude rules don't apply since we WANT
    # boundary violations.
    rule_block = (
        "[HARD-NEGATIVE GENERATION MODE]\n"
        "This slice intentionally generates items that DO NOT belong in the "
        "category. They are stored separately for downstream analysis. "
        "Be diverse and adversarial: probe the boundary."
    ) if is_hn else (
        "[ADMISSION RULE]\n"
        "Every item you produce MUST satisfy the INCLUSION CRITERIA above "
        "AND must not match any EXCLUSION CRITERION. If you are unsure, "
        "set confidence='low' rather than skipping — low-confidence items "
        "go to human audit."
    )

    return f"""\
[CATEGORY]
Code: {category}
Aristotelian appeal: {theory_def["parent_appeal"]}
PI dimension: {theory_def["parent_dimension"]}
PI sub-feature: {theory_def["parent_subfeature"]}

[FUNCTION]
{theory_def["function"]}

[THEORETICAL ANCHOR]
{theory_def["theory_anchor"]}

[INCLUSION CRITERIA]
{_format_list(theory_def["include"])}

[EXCLUSION CRITERIA]
{_format_list(theory_def["exclude"])}

[KNOWN DRIFT TRAPS]
{_format_traps(theory_def["common_drift_traps"])}

[CANONICAL SEEDS]
{', '.join(theory_def["canonical_seeds"])}

[SLICE: {slice_name}]
{spec["instructions"]}

Target output count: ~{spec["target_count"]} items (more is fine if quality holds; fewer is fine if the category is genuinely small).

{rule_block}

[OUTPUT SCHEMA]
Return STRICT JSON in exactly this shape — no prose, no fences:
{{
  "items": [
    {{
      "word": "<the lexicon item, lowercase unless capitalisation is intrinsic>",
      "register": "<formal | colloquial | domain | archaic | neutral>",
      "type": "<single | phrase | inflection | antonym | boundary>",
      "confidence": "<high | medium | low>",
      "rationale": "<one sentence; cite the specific INCLUDE or EXCLUDE rule that applies>"
    }},
    ...
  ]
}}

Field rules:
- "word" must be the surface form (not a regex pattern, not a list).
- "type" must equal "{spec["type_field"]}" for this slice unless the slice is "domain_specific" or "archaic_literary" (in which case use "single" or "phrase").
- "register" should reflect the dominant register for the item.
- "confidence": use "high" only when no reasonable linguist would dispute admission; use "low" for borderline items that should go to human review.
- "rationale": one sentence. Cite the operative rule by paraphrase. No hedging.

Do not include items already given by the canonical seeds list — those are inputs, not outputs."""


def build_messages(category: str, theory_def: Dict, slice_name: str) -> Tuple[str, str]:
    if slice_name not in SLICE_SPECS:
        raise ValueError(f"Unknown slice: {slice_name}. Valid: {list(SLICE_SPECS.keys())}")
    return SYSTEM_MSG, build_user_message(category, theory_def, slice_name)


def all_slice_names() -> List[str]:
    return list(SLICE_SPECS.keys())


def is_hard_negative_slice(slice_name: str) -> bool:
    return SLICE_SPECS[slice_name]["is_hard_negative"]
