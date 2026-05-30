"""
Prompt builder for theory-grounded LLM-as-a-Judge.

Produces (system_msg, user_msg) tuples ready for OpenAI chat.completions.
Uses the user-specified output schema:

    {
      "is_valid": bool,
      "is_morphological_variant": bool,
      "semantic_drift_type": <enum>,
      "rationale": str
    }
"""
from typing import Dict, Tuple

DRIFT_TYPES = [
    "NONE",
    "POS_DRIFT",
    "VALENCE_FLIP",
    "TOPICAL_NEIGHBOR",
    "HYPONYM_OVERSHOOT",
    "HYPERNYM_DILUTION",
    "REGISTER_MISMATCH",
    "SYNTACTIC_FROZEN",
]

DRIFT_GLOSSARY = """\
- NONE                 The candidate preserves the rhetorical function (use this only when is_valid=true).
- POS_DRIFT            Use ONLY when the candidate is a DIFFERENT part of speech than the seed words (e.g., a stance verb nominalised into an outcome noun: agree -> agreement). Verb participles (-ing, -ed), gerunds, and infinitives are still verbs — do NOT label them POS_DRIFT.
- VALENCE_FLIP         Sentiment / stance / direction reversed (e.g., gain -> loss; near -> far; assertion -> refutation).
- TOPICAL_NEIGHBOR     Same topical domain but a different rhetorical function (e.g., agree -> negotiation: both about discussion, but negotiation is a process noun, not a stance act). Use this when the candidate is a verb or adjective that simply serves a different function, not a POS change.
- HYPONYM_OVERSHOOT    Too specific / belongs to a different intensity tier or sub-bucket (e.g., 'severe' admitted as extreme tier when it is actually strong tier).
- HYPERNYM_DILUTION    Too generic; loses the specific function (e.g., 'comment' admitted into AUTHORITY_PHRASE).
- REGISTER_MISMATCH    Formal / informal / domain register breaks the function (e.g., a slang term in a professional-courtesy lexicon).
- SYNTACTIC_FROZEN     Closed-class grammatical role broken (e.g., a connective replaced by a non-connective same-spelling word).\
"""

DRIFT_DECISION_ORDER = """\
Apply drift types in this priority order — stop at the first match:
1. POS_DRIFT        — candidate is a different grammatical category than the seeds (noun vs. verb, adjective vs. noun, etc.)
2. VALENCE_FLIP     — same POS, but sentiment/stance/direction is reversed
3. TOPICAL_NEIGHBOR — same POS and domain, different rhetorical function
4. HYPONYM_OVERSHOOT / HYPERNYM_DILUTION — wrong specificity tier
5. REGISTER_MISMATCH — right function, wrong register
6. SYNTACTIC_FROZEN  — closed-class structural role broken\
"""

SYSTEM_MSG = """\
You are a computational linguist specialising in argumentation mining and persuasion theory.

You evaluate whether a candidate word, expanded from a seed via word-embedding similarity, preserves the RHETORICAL FUNCTION of a theoretically-defined lexicon category in the Persuasion Index (PI) framework. The PI organises 50+ categories under Aristotle's three appeals: Logos, Ethos, Pathos.

You are NOT evaluating semantic similarity in general. You are evaluating FUNCTIONAL EQUIVALENCE in argumentative discourse, judged against a category's operational definition.

Be strict. Vector-space similarity is not your standard — the category's inclusion/exclusion criteria are. When in doubt, reject and label the drift type.

Output STRICT JSON only, matching the schema given by the user. Do not output prose, markdown fences, or any text outside the JSON object."""


def _format_list(items, indent="  "):
    return "\n".join(f"{indent}- {x}" for x in items) if items else f"{indent}(none)"


def _format_traps(traps, indent="  "):
    if not traps:
        return f"{indent}(none recorded)"
    lines = []
    for t in traps:
        lines.append(f"{indent}- '{t['word']}' ({t['drift_type']}): {t['why']}")
    return "\n".join(lines)


def build_user_message(
    category: str,
    seed_word: str,
    candidate: str,
    similarity: float,
    theory_def: Dict,
) -> str:
    drift_enum = ", ".join(f'"{d}"' for d in DRIFT_TYPES)

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

[CANONICAL SEEDS — prototypical members of this category]
{', '.join(theory_def["canonical_seeds"])}

[CANDIDATE TO EVALUATE]
Seed:               {seed_word}
Candidate:          {candidate}
Cosine similarity:  {similarity:.4f}

[DRIFT TYPE GLOSSARY]
{DRIFT_GLOSSARY}

[DRIFT DECISION ORDER]
{DRIFT_DECISION_ORDER}

[TASK]
ADMIT-ANCHOR RULE: Before applying any other criteria, check whether '{candidate}' is explicitly named in the INCLUSION CRITERIA block above. If it is, you MUST return is_valid=true and semantic_drift_type="NONE", regardless of other considerations.

Otherwise, decide whether '{candidate}' should be ADMITTED into category {category}.
Apply the inclusion / exclusion criteria above strictly.

Return STRICT JSON in exactly this shape (no extra keys, no prose):
{{
  "is_valid": <true | false>,
  "is_morphological_variant": <true | false>,
  "semantic_drift_type": <one of: {drift_enum}>,
  "rationale": "<one sentence, theory-grounded; cite which inclusion/exclusion rule applies>"
}}

Field rules:
- "is_valid": true iff '{candidate}' satisfies the inclusion criteria AND violates none of the exclusion criteria for category {category}.
- "is_morphological_variant": true iff '{candidate}' is a clear inflectional or derivational variant of '{seed_word}' (same root + productive affix), regardless of whether the function is preserved.
  Examples: agree -> agreed (true), agree -> agreement (true), agree -> negotiation (false).
- "semantic_drift_type": "NONE" if and only if is_valid=true. Otherwise the single best-matching drift type from the glossary.
- "rationale": one sentence. Reference the operative inclusion/exclusion rule. No hedging, no apologies."""


def build_messages(
    category: str,
    seed_word: str,
    candidate: str,
    similarity: float,
    theory_def: Dict,
) -> Tuple[str, str]:
    return SYSTEM_MSG, build_user_message(category, seed_word, candidate, similarity, theory_def)
