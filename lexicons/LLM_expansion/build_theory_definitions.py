"""
Builds theory_definitions.json — full 57 PI lexicon categories.

Each category encodes:
  parent_appeal / parent_dimension / parent_subfeature   (LaTeX provenance)
  function                                                (1-line operational def)
  theory_anchor                                           (citation key, ELM/Toulmin/etc.)
  include / exclude                                       (admit / reject rules)
  common_drift_traps                                      (concrete failure modes)
  canonical_seeds                                         (in-context anchors)

NOTE on COMMITMENT, RAPPORT, ARG_STYLE.analogy:
  Seeds in CSV under-cover the LaTeX function. We keep the LaTeX-faithful
  definition; the LLM judge is expected to REJECT many candidates here.
  These rejected items are intentional Hard Negatives for downstream
  ablation analysis (they demonstrate embedding's failure to capture
  rhetorical function).
"""
import json
from pathlib import Path


def cat(appeal, dim, sub, function, anchor, include, exclude, traps, seeds):
    return {
        "parent_appeal": appeal,
        "parent_dimension": dim,
        "parent_subfeature": sub,
        "function": function,
        "theory_anchor": anchor,
        "include": include,
        "exclude": exclude,
        "common_drift_traps": traps,
        "canonical_seeds": seeds,
    }


def trap(word, drift, why):
    return {"word": word, "drift_type": drift, "why": why}


D = {}

# ============================================================
# LOGOS — Evidence
# ============================================================

D["EVI_UNITS"] = cat(
    "Logos", "Evidence", "statistical",
    "Units of measurement, statistical markers, currencies, and quantitative indicators that ground claims in verifiable numerical evidence.",
    "Zebregs et al. (2015) on statistical evidence; targets cognitive belief change via factual grounding.",
    [
        "SI / imperial units of measure (kg, mi, ml, ft, °C, mph)",
        "Currency symbols and codes (USD, EUR, $, £, JPY)",
        "Statistical indicators (p-value, percentage, ratio, coefficient, significance)",
        "Magnitude words used in numerical context (million, billion, thousand)",
    ],
    [
        "Polysemous letters with non-measurement meanings in dominant English use",
        "Generic quantifiers without measurement function (some, many, several) — those belong to SPEC_VAGUE",
        "Number words used as ordinals/names (first, second as ranks)",
    ],
    [
        trap("size", "HYPERNYM_DILUTION", "Generic noun, not a measurement unit"),
        trap("many", "TOPICAL_NEIGHBOR", "Vague quantifier; belongs to SPEC_VAGUE"),
    ],
    ["%", "kg", "million", "percentage", "p-value", "USD"],
)

D["REPORTING_VERBS"] = cat(
    "Logos", "Evidence", "attribution",
    "Verbs used to report or attribute findings, claims, or evidence to a source (e.g., 'the study showed', 'they argued').",
    "Hyland (2002) reporting verbs; attribution as central-route credibility cue.",
    [
        "Past- and present-tense reporting verbs (showed, found, reported, argued, concluded, noted)",
        "Verbs marking knowledge claims attributable to a source (estimated, confirmed, demonstrated, observed)",
    ],
    [
        "Pure communication verbs without epistemic content (talked, chatted)",
        "Stance-taking performative verbs without reporting function (assert, contend) — belong to ARG_CLAIM",
        "General factive verbs not tied to source attribution (knew, realized)",
    ],
    [
        trap("talked", "HYPERNYM_DILUTION", "Generic communication verb; no epistemic attribution"),
        trap("claim", "TOPICAL_NEIGHBOR", "Stance-taking verb, not source attribution; belongs to ARG_CLAIM"),
    ],
    ["showed", "found", "reported", "argued", "concluded"],
)

# ============================================================
# LOGOS — Logic and Cohesion
# ============================================================

LOGIC_SHARED_EXCLUDE = [
    "Content words masquerading as connectives (e.g., 'reason' as a noun)",
    "Connectives from a different logical relation (contrastive 'but' should not enter LOGIC_CAUSAL)",
    "Lexicalized phrases that have lost connective function in modern usage",
]

D["LOGIC_CAUSAL"] = cat(
    "Logos", "Logic and Cohesion", "structural_reasoning",
    "Closed-class connectives that mark a CAUSAL relation between propositions (cause→effect, reason→consequence).",
    "Kaakinen & Hyönä (2011) cohesion; Heuristic-Systematic Model (Chaiken 1980).",
    [
        "Causal subordinators (because, since, as)",
        "Causal coordinators / inferential adverbs (therefore, thus, hence, consequently, accordingly)",
        "Causal phrasal markers (due to, owing to, as a result, that is why)",
    ],
    LOGIC_SHARED_EXCLUDE + [
        "Contrastive markers (however, but, although) — belong to LOGIC_CONTRAST",
    ],
    [
        trap("but", "VALENCE_FLIP", "Contrastive, not causal"),
        trap("reason", "POS_DRIFT", "Noun, not connective"),
        trap("cause", "POS_DRIFT", "Verb/noun; only 'because' is the connective"),
    ],
    ["because", "therefore", "thus", "since", "consequently"],
)

D["LOGIC_CONTRAST"] = cat(
    "Logos", "Logic and Cohesion", "discourse_cohesion",
    "Closed-class connectives marking a CONTRASTIVE / adversative relation (concession, opposition, exception).",
    "Cohesion theory (Halliday & Hasan); ELM systematic processing.",
    [
        "Adversative coordinators / adverbs (but, however, yet, nevertheless, nonetheless)",
        "Concessive subordinators (although, though, even though, whereas, while [contrastive])",
        "Contrastive phrasal markers (on the other hand, in contrast, by contrast)",
    ],
    LOGIC_SHARED_EXCLUDE + [
        "Causal markers (because, therefore) — belong to LOGIC_CAUSAL",
        "Pure additives (also, moreover) — belong to LOGIC_ADDITIVE",
        "Temporal 'while' without contrastive function",
    ],
    [
        trap("while", "POS_DRIFT", "Polysemous: contrastive vs. temporal — only contrastive use qualifies"),
        trap("and", "VALENCE_FLIP", "Additive, not contrastive"),
    ],
    ["however", "but", "although", "yet", "nevertheless"],
)

D["LOGIC_ADDITIVE"] = cat(
    "Logos", "Logic and Cohesion", "discourse_cohesion",
    "Closed-class connectives marking ADDITIVE / elaborative relations (and-type extensions of an argument).",
    "Cohesion theory; chains of related propositions.",
    [
        "Additive coordinators / adverbs (also, moreover, furthermore, additionally, plus, besides)",
        "Enumerative additives (firstly, secondly, finally as list-extenders)",
        "Phrasal additive markers (in addition, what is more)",
    ],
    LOGIC_SHARED_EXCLUDE + [
        "Contrastive markers — belong to LOGIC_CONTRAST",
        "Causal markers — belong to LOGIC_CAUSAL",
    ],
    [
        trap("however", "VALENCE_FLIP", "Contrastive, not additive"),
        trap("because", "VALENCE_FLIP", "Causal, not additive"),
    ],
    ["also", "moreover", "furthermore", "additionally", "in addition"],
)

D["LOGIC_INFERENCE"] = cat(
    "Logos", "Logic and Cohesion", "structural_reasoning",
    "Inferential markers that signal a logical conclusion drawn from prior content (so X, hence X, it follows that X).",
    "Toulmin warrant→claim transitions; ELM systematic chain.",
    [
        "Inferential adverbs (so, hence, thus, ergo, accordingly)",
        "Inferential phrases (it follows that, this implies, therefore we can conclude)",
        "Logical-derivation markers (consequently, as a result)",
    ],
    LOGIC_SHARED_EXCLUDE + [
        "Pure causal connectives (because, since) — those mark cause, not inference; belong to LOGIC_CAUSAL",
        "Conclusion summary phrases ('in conclusion', 'to sum up') — belong to ARG_CONCLUSION",
    ],
    [
        trap("because", "TOPICAL_NEIGHBOR", "Marks cause, not inferential conclusion"),
        trap("finally", "TOPICAL_NEIGHBOR", "Temporal/enumerative, not inferential"),
    ],
    ["thus", "hence", "so", "ergo", "it follows that"],
)

D["LOGIC_REFERENCE"] = cat(
    "Logos", "Logic and Cohesion", "structural_reasoning",
    "Referential markers that bind discourse via anaphora/cataphora to prior or upcoming content (this, that, the aforementioned, the latter).",
    "Halliday & Hasan reference cohesion; reduces processing load.",
    [
        "Demonstrative referential pronouns/determiners with discourse-tracking function (this, that, these, those, such)",
        "Anaphoric phrasal markers (the former, the latter, the aforementioned, said [argument])",
        "Cataphoric / forward-reference markers (the following, as below)",
    ],
    LOGIC_SHARED_EXCLUDE + [
        "Demonstratives in deictic spatial/temporal use ('this room' physical reference) — that's SPEC_PSYCH_NEAR",
        "Personal pronouns (he, she, they)",
    ],
    [
        trap("this", "POS_DRIFT", "Polysemous: spatial deixis vs. discourse anaphora — judge contextual function"),
    ],
    ["this", "that", "the aforementioned", "the former", "the latter"],
)

# ============================================================
# LOGOS — Argumentation
# ============================================================

D["ARG_CLAIM"] = cat(
    "Logos", "Argumentation", "conclusion_explicitness",
    "Stance-taking illocutionary verbs that explicitly mark a CLAIM or assertion as a speech act in argumentative discourse.",
    "Toulmin (1958) claim node; O'Keefe (1997) standpoint explicitness; ELM central-route processing.",
    [
        "Verbs marking the speech act of claiming/asserting (claim, argue, assert, contend, maintain, hold)",
        "First-person performative formulations (I argue, I'd contend, I claim)",
        "Stance verbs that commit the speaker to a proposition (insist, posit, postulate)",
    ],
    [
        "Nominal forms denoting OUTCOME or PROCESS rather than the speech act (negotiation, agreement, settlement)",
        "Antonymous stance markers — refutation rather than claim (reject, refuse, oppose, deny)",
        "Generic communication verbs without stance commitment (discuss, mention, talk, comment)",
        "Topical neighbors of the debate domain (proposal, deal, position [as noun])",
    ],
    [
        trap("negotiation", "POS_DRIFT", "Process noun, not stance-marking verb"),
        trap("reject", "VALENCE_FLIP", "Refutation; opposite illocutionary direction"),
        trap("discuss", "TOPICAL_NEIGHBOR", "Communication without stance commitment"),
        trap("agreement", "POS_DRIFT", "Outcome noun, not speech act"),
    ],
    ["claim", "argue", "assert", "contend", "maintain"],
)

D["ARG_PREMISE"] = cat(
    "Logos", "Argumentation", "premise_density",
    "Linguistic introducers that explicitly mark a proposition as a PREMISE supporting a claim.",
    "Toulmin grounds/warrant; premise density as ELM peripheral 'length-is-strength' heuristic (Petty 1984).",
    [
        "Premise subordinators (because, since, given that, on the grounds that, for)",
        "Premise-introducing phrases (the reason is, due to the fact that, as evidenced by)",
        "Warrant-introducing markers (after all, considering that)",
    ],
    [
        "Pure causal markers without premise function (consequently, therefore — those introduce conclusions)",
        "Inferential markers (thus, hence — they follow from premises, not introduce them)",
    ],
    [
        trap("therefore", "VALENCE_FLIP", "Introduces conclusion, not premise"),
        trap("reason", "POS_DRIFT", "Noun, not premise introducer"),
    ],
    ["because", "since", "given that", "for"],
)

D["ARG_CONCLUSION"] = cat(
    "Logos", "Argumentation", "conclusion_explicitness",
    "Markers that explicitly signal the START of a conclusion or summary statement closing an argument.",
    "O'Keefe (1997) standpoint explicitness; conclusion explicitness reduces audience misinterpretation.",
    [
        "Conclusion-introducing connectives (therefore, hence, thus, so, in conclusion)",
        "Summative phrases (in summary, to sum up, in short, all in all, overall)",
        "Explicit conclusion markers (we can conclude that, the upshot is, the bottom line is)",
    ],
    [
        "Pure premise-markers (because, since) — they introduce supporting reasons, not conclusions",
        "Mid-argument additives (furthermore) — not conclusion markers",
    ],
    [
        trap("because", "VALENCE_FLIP", "Introduces premise, not conclusion"),
        trap("moreover", "TOPICAL_NEIGHBOR", "Additive, not conclusive"),
    ],
    ["therefore", "in conclusion", "thus", "to sum up", "in summary"],
)

D["ARG_STYLE.analogy"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Markers introducing ANALOGICAL reasoning patterns (X is like Y, analogous to, by analogy, similarly to).",
    "Argument schemes (Walton); analogy as a high-sophistication move.",
    [
        "Analogy connectives (analogous to, by analogy, similar to, similarly, akin to, just as)",
        "Comparison-by-analogy phrasal markers (in the same way, much like, parallel to)",
        "Simile-anchoring 'like' ONLY when introducing a structural analogy (not preposition or stalling 'like')",
    ],
    [
        "Polysemous 'like' as preposition / verb / discourse stalling marker — those are POS_DRIFT",
        "Pure example markers (for example, e.g.) — belong to ARG_STYLE.example",
        "Generic similarity adjectives without analogical-reasoning function",
    ],
    [
        trap("for example", "TOPICAL_NEIGHBOR", "Example, not analogy"),
        trap("liked", "POS_DRIFT", "Verb sense of 'like'; not analogy connective"),
        trap("likely", "POS_DRIFT", "Probability adverb; not analogy"),
    ],
    ["analogous to", "by analogy", "similarly", "akin to", "just as"],
)

D["ARG_STYLE.cause_effect"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Markers introducing CAUSE-EFFECT explanatory moves within an argument body (different from logical connectives — these announce a causal explanation).",
    "Argument schemes (Walton); cause-effect as sophistication.",
    [
        "Causal explanatory phrases (this leads to, results in, brings about, causes, produces)",
        "Effect-announcing markers (the effect of X is, has the consequence that)",
    ],
    [
        "Pure single-token connectives that fit LOGIC_CAUSAL better (because, since)",
        "Mere temporal sequence (then, after that)",
    ],
    [
        trap("after", "TOPICAL_NEIGHBOR", "Temporal, not necessarily causal"),
    ],
    ["leads to", "results in", "causes", "brings about"],
)

D["ARG_STYLE.concession_refute"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Two-part markers that first concede an opposing point and then refute it — the central pattern of refutational two-sided argumentation.",
    "O'Keefe (1999) refutational two-sided messages; Allen (1991) meta-analysis.",
    [
        "Concession openers (admittedly, granted, true that, while it is true)",
        "Refutation pivots that follow concession (however, nevertheless, but, still)",
        "Combined fixed-phrase patterns ('it may be that X, but Y')",
    ],
    [
        "Pure contrastive markers without prior concession (just 'however' alone — that's LOGIC_CONTRAST)",
        "Counter-claim openers without concession (instead, on the contrary)",
    ],
    [
        trap("instead", "TOPICAL_NEIGHBOR", "Counter-claim opener, no concession move"),
        trap("however", "HYPERNYM_DILUTION", "Standalone contrast; admit only as the refutation pivot in concession+refute pattern"),
    ],
    ["admittedly", "granted", "true that", "while it is true"],
)

D["ARG_STYLE.conditional"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Conditional reasoning markers that introduce hypothetical or counterfactual argumentation (if X then Y).",
    "Conditional reasoning as deductive sophistication marker.",
    [
        "Conditional subordinators (if, unless, provided that, assuming that, in case)",
        "Counterfactual markers (had it been, were it not for, suppose that)",
        "Apodosis introducers (then, would, would have)",
    ],
    [
        "Pure temporal 'when' without hypothetical force",
        "'Whether' as alternative-listing rather than conditional",
    ],
    [
        trap("when", "POS_DRIFT", "Temporal use is more common; admit only when clearly conditional"),
    ],
    ["if", "unless", "provided that", "suppose that"],
)

D["ARG_STYLE.counter"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Markers that introduce a counter-argument or alternative perspective (acknowledging opposing views as part of argumentative balance).",
    "Refutational two-sided messages (O'Keefe 1999); preemptive resolution of receiver objections.",
    [
        "Counter-introducers (although, though, however, granted, while [contrastive])",
        "Phrasal counter-markers (on the other hand, by contrast, that said, even so)",
        "Acknowledgment-style openers (admittedly, of course)",
    ],
    [
        "Pure additive markers (also, moreover) — no counter function",
        "Pure causal markers",
    ],
    [
        trap("moreover", "VALENCE_FLIP", "Additive, not counter"),
    ],
    ["although", "however", "granted", "though"],
)

D["ARG_STYLE.definition"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Markers that introduce a DEFINITIONAL or clarificatory move within an argument (X is defined as, by X we mean).",
    "Definition as argument scheme (Walton); reduces ambiguity.",
    [
        "Definitional copular markers ('is defined as', 'means', 'refers to', 'is a')",
        "Clarification markers (in other words, that is, i.e., namely)",
        "Term-introduction phrases (we call this, by X we mean)",
    ],
    [
        "Generic copula 'is' without definitional function (e.g., 'the sky is blue' is not a definition move)",
        "Examplification markers (for example, e.g.) — those belong to ARG_STYLE.example",
    ],
    [
        trap("for example", "TOPICAL_NEIGHBOR", "Exemplification, not definition"),
    ],
    ["is defined as", "means", "refers to", "in other words", "namely"],
)

D["ARG_STYLE.example"] = cat(
    "Logos", "Argumentation", "style_sophistication",
    "Markers that introduce a concrete EXAMPLE or instance to support a general claim.",
    "Exemplification Theory (Bigsby 2019); vivid examples enhance perceived issue severity.",
    [
        "Example introducers (for example, for instance, e.g., such as, including)",
        "Case introducers (a case in point, take X for instance, consider the case of)",
        "Illustration markers (to illustrate, by way of illustration)",
    ],
    [
        "Definitional markers (i.e., namely) — those belong to ARG_STYLE.definition",
        "Pure additive markers without exemplifying function",
    ],
    [
        trap("i.e.", "TOPICAL_NEIGHBOR", "Definitional clarification, not exemplification"),
    ],
    ["for example", "for instance", "e.g.", "such as"],
)

# ============================================================
# LOGOS — Specificity
# ============================================================

D["SPEC_ANCHORS"] = cat(
    "Logos", "Specificity", "lexical_concreteness",
    "Specification anchors that bind a general claim to a CONCRETE referent or instance (specifically, namely, particularly).",
    "Construal Level Theory (Trope & Liberman); concrete language increases perceived truth (Hansen & Wänke 2010).",
    [
        "Specificity adverbs (specifically, namely, particularly, especially, notably, in particular)",
        "Concretization phrases (to be specific, more precisely, in concrete terms)",
        "Instance-introducers when used to specify rather than exemplify (such as)",
    ],
    [
        "Pure exemplification (for example, e.g.) — belongs to ARG_STYLE.example unless specifying",
        "Pure additive markers",
    ],
    [
        trap("for example", "TOPICAL_NEIGHBOR", "Exemplification, not specification anchor"),
    ],
    ["specifically", "namely", "particularly", "in particular"],
)

D["SPEC_PSYCH_NEAR"] = cat(
    "Logos", "Specificity", "psychological_nearness",
    "Markers of psychological PROXIMITY in time, space, or social distance (now, here, this, today, immediate).",
    "Construal Level Theory; near-construal triggers concrete processing.",
    [
        "Temporal nearness (now, today, currently, presently, this minute/hour/day/week)",
        "Spatial nearness (here, nearby, local, this place)",
        "Demonstrative-near (this, these) when used in deictic spatial/temporal sense",
    ],
    [
        "Distance markers (someday, distant, that, those) — belong to SPEC_PSYCH_FAR",
        "Vague quantifiers (often, many) — belong to SPEC_VAGUE",
        "Discourse anaphora 'this/that' (referring to prior text) — belong to LOGIC_REFERENCE",
    ],
    [
        trap("future", "VALENCE_FLIP", "Far-distant temporal marker"),
        trap("often", "TOPICAL_NEIGHBOR", "Vague frequency, not proximity"),
    ],
    ["now", "here", "today", "this", "immediately"],
)

D["SPEC_PSYCH_FAR"] = cat(
    "Logos", "Specificity", "psychological_nearness",
    "Markers of psychological DISTANCE in time, space, or social distance (someday, distant, those, eventually). Inverse signal of psychological nearness.",
    "Construal Level Theory; far-construal triggers abstract processing.",
    [
        "Temporal distance (eventually, someday, in the long run, decades from now, century)",
        "Spatial distance (distant, far, remote, abroad)",
        "Demonstrative-far (that, those) when used in deictic distancing sense",
    ],
    [
        "Near markers — belong to SPEC_PSYCH_NEAR",
        "Discourse anaphora 'that/those' (referring to prior text) — belong to LOGIC_REFERENCE",
    ],
    [
        trap("now", "VALENCE_FLIP", "Near, not far"),
        trap("this", "VALENCE_FLIP", "Near deixis"),
    ],
    ["distant", "eventually", "someday", "decades", "century"],
)

D["SPEC_VAGUE"] = cat(
    "Logos", "Specificity", "lexical_concreteness",
    "Vague quantifiers and indefinite expressions that REDUCE specificity (some, many, often, several, various). Negative signal in the specificity dimension.",
    "Construal Level Theory; vague language increases abstraction.",
    [
        "Vague indefinite quantifiers (some, several, many, few, most, various)",
        "Vague frequency adverbs (often, usually, sometimes, occasionally, rarely)",
        "Approximators (about, around, roughly, approximately, nearly)",
    ],
    [
        "Concrete numerical quantifiers (three, five, half) — those are specific, opposite signal",
        "Hedges that are epistemic rather than quantificational (might, could) — belong to HEDGES",
        "Specification markers (specifically, particularly) — belong to SPEC_ANCHORS",
    ],
    [
        trap("specifically", "VALENCE_FLIP", "Specification, not vagueness"),
        trap("three", "VALENCE_FLIP", "Concrete number, not vague"),
    ],
    ["some", "many", "often", "several", "various"],
)

# ============================================================
# ETHOS — Authority and Credibility
# ============================================================

D["AUTHORITY_PHRASE"] = cat(
    "Ethos", "Authority and Credibility", "phrases",
    "Lexical anchors used in authority-attribution phrases (e.g., 'according to a study', 'the data shows', 'verified report').",
    "Hovland & Weiss (1951) source credibility; institutional anchors as heuristic credibility cues.",
    [
        "Evidence-anchoring nouns (study, data, report, evidence, finding, statistic, testimony)",
        "Verification markers (verified, confirmed, documented, certified)",
        "Authoritative source nouns (authority, expert, specialist, scientist, researcher)",
    ],
    [
        "Reporting verbs (showed, argued) — belong to REPORTING_VERBS",
        "Generic communication nouns without authority-bearing function (note, comment)",
    ],
    [
        trap("argued", "POS_DRIFT", "Reporting verb; belongs to REPORTING_VERBS"),
        trap("comment", "HYPERNYM_DILUTION", "Generic communication noun without authority weight"),
    ],
    ["data", "study", "report", "verified", "testimony"],
)

D["HEDGES"] = cat(
    "Ethos", "Authority and Credibility", "speech_power_inverse",
    "Hedging expressions that soften claims and signal epistemic uncertainty or imprecision (kind of, sort of, possibly, around). INVERSE signal — penalizes speech_power.",
    "Powerless language (Hosman 1989); reduces perceived authority.",
    [
        "Approximators (around, approximately, roughly, almost, nearly, broadly)",
        "Quantity hedges (somewhat, kind of, sort of, a bit)",
        "Epistemic softeners (apparently, seemingly, more or less)",
    ],
    [
        "Strong epistemic uncertainty (might, may, could) — overlap with UNCERTAINTY; admit only as approximation softener",
        "Hesitations (uh, um) — belong to HESITATIONS",
        "Non-imposition softeners (please) — belong to PLEASE",
    ],
    [
        trap("definitely", "VALENCE_FLIP", "Booster, not hedge"),
        trap("uh", "TOPICAL_NEIGHBOR", "Hesitation marker; belongs to HESITATIONS"),
    ],
    ["around", "kind of", "approximately", "roughly", "somewhat"],
)

D["HESITATIONS"] = cat(
    "Ethos", "Authority and Credibility", "speech_power_inverse",
    "Disfluencies and hesitation markers that signal speaker uncertainty in real-time production (uh, um, well, you know).",
    "Powerless language (Erickson et al. 1978); disfluency reduces perceived competence.",
    [
        "Filled-pause disfluencies (uh, um, er, ah, hmm)",
        "Stalling discourse markers (well, like [stalling], you know [stalling])",
        "Restart markers (I mean, that is to say [as restart])",
    ],
    [
        "Approximators (around, kind of) — belong to HEDGES",
        "Politeness fillers (excuse me, sorry) — belong to Apology / COURTESY",
    ],
    [
        trap("around", "TOPICAL_NEIGHBOR", "Approximator hedge, not hesitation"),
    ],
    ["uh", "um", "well", "you know", "I mean"],
)

D["UNCERTAINTY"] = cat(
    "Ethos", "Authority and Credibility", "speech_power_inverse",
    "Epistemic uncertainty markers that signal the speaker's lack of full commitment to a proposition (allegedly, may, might, possibly, seem). INVERSE signal — reduces speech_power.",
    "Powerless language; epistemic modality as commitment-reduction cue.",
    [
        "Epistemic modal verbs (may, might, could, would, should as epistemic, can as epistemic)",
        "Epistemic adverbs (allegedly, apparently, perhaps, possibly, presumably, seemingly)",
        "Epistemic verbs (seem, appear, indicate, suggest, suspect, presume, suppose)",
        "Uncertainty adjectives (uncertain, unsure, possible, probable, questionable)",
    ],
    [
        "Quantity hedges (around, kind of) — belong to HEDGES",
        "Disfluencies (uh, um) — belong to HESITATIONS",
        "Pure deontic modals (must, should as obligation) — those are DOMINEERING",
        "Booster adverbs (definitely, certainly, surely) — belong to Actually",
    ],
    [
        trap("definitely", "VALENCE_FLIP", "Booster (high commitment), opposite of uncertainty"),
        trap("must", "VALENCE_FLIP", "Deontic obligation, not epistemic uncertainty"),
    ],
    ["may", "might", "perhaps", "possibly", "allegedly", "seem"],
)

D["Actually"] = cat(
    "Ethos", "Authority and Credibility", "speech_power_positive",
    "Assertive / asseverative discourse markers that boost epistemic commitment and project speaker confidence (actually, honestly, really, surely). Positive end of speech_power.",
    "Powerful language (Hosman 1989); booster adverbs increase perceived authority.",
    [
        "Truth-asseverative adverbs (actually, really, truly, honestly, frankly)",
        "Certainty boosters (surely, certainly, definitely, undoubtedly, indeed, absolutely)",
        "Reality-anchoring markers (in fact, in truth, no doubt)",
    ],
    [
        "Epistemic uncertainty markers (perhaps, maybe) — belong to UNCERTAINTY",
        "Hedges (kind of, around) — belong to HEDGES",
        "Generic intensifiers (very, so) — belong to SENT_INTENSITY.weak",
    ],
    [
        trap("perhaps", "VALENCE_FLIP", "Uncertainty marker, opposite valence"),
        trap("very", "TOPICAL_NEIGHBOR", "Generic intensifier, not assertive booster"),
    ],
    ["actually", "really", "honestly", "surely", "in fact"],
)

# ============================================================
# ETHOS — Politeness
# ============================================================

D["COURTESY"] = cat(
    "Ethos", "Politeness", "professional_courtesy",
    "Generic professional courtesy markers expressing respect, deference, or polite attention (sir, ma'am, kindly, respectfully, dear).",
    "Brown & Levinson (1987) face-saving; mitigates Face Threatening Acts.",
    [
        "Honorifics and address terms (sir, ma'am, madam, dear, respected)",
        "Polite adverbs (kindly, respectfully, graciously, courteously)",
        "Deferential phrasal markers (with all due respect, if I may)",
    ],
    [
        "Apologies — belong to Apology",
        "Thanks — belong to THANKS",
        "Greetings — belong to Greeting",
        "Polite request softeners (please) — belong to PLEASE",
    ],
    [
        trap("thanks", "TOPICAL_NEIGHBOR", "Belongs to THANKS"),
    ],
    ["sir", "kindly", "respectfully", "with all due respect"],
)

D["Apology"] = cat(
    "Ethos", "Politeness", "professional_courtesy",
    "Apology markers and regret expressions that mitigate face-threatening moves (sorry, apologize, my apologies, regret).",
    "Brown & Levinson face-redress.",
    [
        "Direct apology verbs / nouns (apologize, sorry, regret, my bad)",
        "Apology phrasal forms (I apologize, my apologies, please forgive)",
        "Excuse-me variants (excuse me, pardon, beg your pardon)",
    ],
    [
        "Generic courtesy (kindly, sir) — belong to COURTESY",
        "Sympathy without speaker fault (condolences) — borderline; reject if no apology function",
    ],
    [
        trap("thanks", "TOPICAL_NEIGHBOR", "Gratitude, not apology"),
    ],
    ["sorry", "apologize", "my apologies", "excuse me"],
)

D["THANKS"] = cat(
    "Ethos", "Politeness", "professional_courtesy",
    "Gratitude and appreciation markers (thanks, thank you, appreciate, grateful).",
    "Brown & Levinson positive politeness.",
    [
        "Direct gratitude expressions (thanks, thank you, thank-you, ty)",
        "Appreciation verbs (appreciate, am grateful, am thankful)",
        "Phrasal gratitude (much obliged, many thanks)",
    ],
    [
        "Apologies — belong to Apology",
        "Greetings — belong to Greeting",
    ],
    [
        trap("sorry", "TOPICAL_NEIGHBOR", "Apology, not gratitude"),
    ],
    ["thanks", "thank you", "appreciate", "grateful"],
)

D["Greeting"] = cat(
    "Ethos", "Politeness", "professional_courtesy",
    "Greeting and salutation markers that open or close interactions (hello, hi, good morning, regards).",
    "Brown & Levinson positive politeness; phatic communion.",
    [
        "Opening greetings (hello, hi, hey, greetings, good morning/afternoon/evening)",
        "Closing salutations (regards, sincerely, best, cheers, take care)",
        "Vocative-style address openers (dear sir/madam)",
    ],
    [
        "Honorifics not in salutation context — belong to COURTESY",
        "Filler interjections without greeting function",
    ],
    [
        trap("kindly", "TOPICAL_NEIGHBOR", "Courtesy adverb, not greeting"),
    ],
    ["hello", "hi", "good morning", "regards"],
)

D["PLEASE"] = cat(
    "Ethos", "Politeness", "non_imposition",
    "Request softeners that mitigate imposition on the addressee (please, kindly, would you mind, could you).",
    "Brown & Levinson negative politeness; non-imposition strategies.",
    [
        "Direct softeners (please, kindly, do please)",
        "Indirect request frames (would you mind, could you possibly, if you could)",
        "Phrasal politeness (if it's not too much trouble, when you have a moment)",
    ],
    [
        "Hedges that are not request-bound (around, kind of) — belong to HEDGES",
        "Apologies — belong to Apology",
    ],
    [
        trap("kind of", "TOPICAL_NEIGHBOR", "Quantity hedge, not request softener"),
    ],
    ["please", "kindly", "would you mind", "could you"],
)

D["RAPPORT"] = cat(
    "Ethos", "Politeness", "rapport_building",
    "Rapport-building markers that signal positive solidarity, alignment, or appreciation of the addressee's contribution (great point, well said, that's helpful, supportive).",
    "Spencer-Oatey (2008) rapport management; positive politeness solidarity strategies.",
    [
        "Positive evaluation tokens directed at the interlocutor's contribution (great, excellent, wonderful, amazing, helpful, supportive)",
        "Solidarity-building phrases (well said, good point, fair point, I see what you mean)",
        "Encouragement markers (keep it up, that's a good idea, nicely put)",
    ],
    [
        "Pure positive sentiment about non-interlocutor topics (a great day, wonderful weather) — those have no rapport function",
        "Generic positive adjectives without addressee-direction (beautiful, lovely, fine)",
        "Conversational fillers (you know, right?) — belong to Filler",
        "Greetings — belong to Greeting",
    ],
    [
        trap("beautiful", "TOPICAL_NEIGHBOR", "Generic positive evaluation, not rapport-building"),
        trap("nice", "HYPERNYM_DILUTION", "Too generic; lacks addressee-directed solidarity function"),
    ],
    ["amazing", "excellent", "great", "supportive", "wonderful"],
)

D["Filler"] = cat(
    "Ethos", "Politeness", "rapport_building",
    "Conversational fillers and rapport-oriented discourse markers that build interpersonal rapport (you know, right?, I see, yeah).",
    "Rapport management (Spencer-Oatey 2008).",
    [
        "Phatic conversational fillers (you know, you see, I mean [non-restart], right?, okay)",
        "Backchannel-style markers (yeah, mhm, mm)",
        "Acknowledgment markers in conversational mode (alright, sure)",
    ],
    [
        "Hesitation disfluencies (uh, um) — belong to HESITATIONS",
        "Topic-shift connectives (by the way) — belong to By.The.Way",
        "Substantive discourse markers (so, anyway as topic-shifters)",
    ],
    [
        trap("uh", "TOPICAL_NEIGHBOR", "Hesitation, not rapport filler"),
        trap("btw", "TOPICAL_NEIGHBOR", "Topic-shifter; belongs to By.The.Way"),
    ],
    ["you know", "right?", "I see", "yeah", "okay"],
)

D["By.The.Way"] = cat(
    "Ethos", "Politeness", "rapport_building",
    "Topic-shift and parenthetical conversational connectors (by the way, btw, incidentally, anyway).",
    "Discourse management for rapport (Schiffrin 1987).",
    [
        "Topic-shifters (by the way, btw, incidentally)",
        "Parenthetical openers (speaking of which, on a side note, that reminds me)",
        "Closing topic-managers (anyway, anyhow [topic-shift use])",
    ],
    [
        "Pure conversational fillers without topic-shift function — belong to Filler",
        "Logical connectives (however, therefore)",
    ],
    [
        trap("however", "TOPICAL_NEIGHBOR", "Logical contrast, not topic-shift"),
    ],
    ["by the way", "btw", "incidentally", "anyway"],
)

D["DOMINEERING"] = cat(
    "Ethos", "Politeness", "domineering_inverse",
    "Coercive / commanding language that imposes on the addressee (must, have to, you should, I demand). INVERSE signal — penalizes politeness.",
    "Brown & Levinson; coercive force triggers psychological reactance (Brehm 1966).",
    [
        "Strong deontic modals (must, have to, has to, ought to, need to)",
        "Direct imperative formulations (you should, I demand, I insist, you will)",
        "Coercive verb phrases (require, force, compel, mandate)",
    ],
    [
        "Polite request forms (please, kindly) — belong to PLEASE",
        "Epistemic 'must' (he must be tired) — admit only deontic / commanding use",
        "Modal advice without coercion (you might want to)",
    ],
    [
        trap("please", "VALENCE_FLIP", "Polite softener, not coercive"),
        trap("may", "VALENCE_FLIP", "Permissive, opposite of coercive"),
    ],
    ["must", "have to", "ought to", "I demand"],
)

# ============================================================
# ETHOS — Commitment
# ============================================================

D["COMMITMENT"] = cat(
    "Ethos", "Commitment", "statements",
    "Explicit commitment markers signalling speaker resolve and prior investment (I promise, I will, we pledge, we commit, count on me).",
    "Foot-in-the-Door consistency mechanism (Burger 1999); Pallak et al. (1980) verifiable commitment.",
    [
        "First-person commitment performatives (I promise, I pledge, I commit, I assure, I guarantee, I vow)",
        "Plural-collective commitment (we promise, we will, we commit ourselves to)",
        "Investment-of-effort markers (we have invested, we are dedicated to, we stand by)",
    ],
    [
        "Pure collective-identity markers without commitment performative (together, jointly) — those mark mutuality not commitment",
        "Generic positive future statements without speaker-binding force",
        "Mutual exchange framings (win-win, mutual) — belong to REC_MUTUAL_EXCHANGE",
    ],
    [
        trap("together", "TOPICAL_NEIGHBOR", "Collective identity, not commitment performative"),
        trap("mutual", "TOPICAL_NEIGHBOR", "Mutuality framing; belongs to REC_MUTUAL_EXCHANGE"),
        trap("partnership", "TOPICAL_NEIGHBOR", "Mutual exchange noun, not commitment statement"),
    ],
    ["I promise", "I pledge", "I commit", "we will", "I guarantee"],
)

D["COMMITMENT_PROOF"] = cat(
    "Ethos", "Commitment", "power",
    "Markers indicating that a commitment statement is supported by VERIFIABLE proof of action (documented, recorded, on file, evidenced).",
    "Pallak et al. (1980) commitment is strongest when socially verifiable.",
    [
        "Documentation markers (documented, recorded, logged, on file, archived)",
        "Witness/verification markers (witnessed, verified, certified, signed-off)",
        "Public-record markers (published, registered, filed)",
    ],
    [
        "General authority markers without proof-of-commitment function — belong to AUTHORITY_PHRASE",
        "Commitment statements themselves (I promise) — belong to COMMITMENT",
    ],
    [
        trap("promise", "TOPICAL_NEIGHBOR", "Commitment statement, not proof of execution"),
    ],
    ["documented", "recorded", "verified", "on file"],
)

# ============================================================
# PATHOS — Sentiment
# ============================================================

D["SENT_INTENSITY.extreme"] = cat(
    "Pathos", "Sentiment", "language_intensity",
    "Words expressing EXTREME affective intensity at the top of the intensity scale (catastrophic, devastating, horrific, monstrous).",
    "Bowers (1964) language intensity; extreme intensity amplifies arousal.",
    [
        "Extreme negative-valence intensity (catastrophic, devastating, horrific, monstrous, atrocious, life-threatening)",
        "Extreme positive-valence intensity (miraculous, phenomenal, extraordinary, unprecedented, mind-blowing)",
        "Superlative-tier intensifiers (utterly, absolutely [+ extreme adj])",
    ],
    [
        "Strong but not extreme intensity (severe, intense) — belong to SENT_INTENSITY.strong",
        "Moderate intensity (significant, considerable) — belong to SENT_INTENSITY.moderate",
        "Weak intensifiers (very, pretty) — belong to SENT_INTENSITY.weak",
    ],
    [
        trap("severe", "HYPONYM_OVERSHOOT", "Strong, not extreme tier"),
        trap("very", "HYPONYM_OVERSHOOT", "Weak intensifier"),
    ],
    ["catastrophic", "devastating", "horrific", "monstrous", "outrageous"],
)

D["SENT_INTENSITY.strong"] = cat(
    "Pathos", "Sentiment", "language_intensity",
    "Words expressing STRONG affective intensity (severe, intense, powerful, dramatic).",
    "Language intensity scale.",
    [
        "Strong negative-valence intensity (severe, intense, drastic, grave, serious)",
        "Strong positive-valence intensity (powerful, profound, remarkable, striking)",
        "Strong tier intensifying adverbs (deeply, intensely, profoundly)",
    ],
    [
        "Extreme tier (catastrophic, devastating) — belong to SENT_INTENSITY.extreme",
        "Moderate / weak tier intensifiers",
    ],
    [
        trap("catastrophic", "HYPONYM_OVERSHOOT", "Extreme tier"),
        trap("moderate", "VALENCE_FLIP", "Moderate tier"),
    ],
    ["severe", "intense", "drastic", "powerful"],
)

D["SENT_INTENSITY.moderate"] = cat(
    "Pathos", "Sentiment", "language_intensity",
    "Words expressing MODERATE affective intensity (significant, considerable, substantial, notable).",
    "Language intensity scale.",
    [
        "Moderate intensifiers (significant, considerable, substantial, notable, marked)",
        "Moderate-tier adverbs (significantly, considerably, notably, markedly)",
        "Mid-scale evaluatives (important, meaningful, relevant)",
    ],
    [
        "Strong / extreme tier",
        "Weak tier (pretty, quite, very)",
    ],
    [
        trap("very", "HYPONYM_OVERSHOOT", "Weak tier"),
        trap("severe", "HYPONYM_OVERSHOOT", "Strong tier"),
    ],
    ["significant", "considerable", "substantial", "notable"],
)

D["SENT_INTENSITY.weak"] = cat(
    "Pathos", "Sentiment", "language_intensity",
    "Generic / weak intensifiers at the bottom of the intensity scale (very, pretty, quite, so, really).",
    "Language intensity scale; weak boosters carry low arousal.",
    [
        "Generic intensifiers (very, so, quite, pretty, really [as intensifier])",
        "Mild boosters (rather, fairly, somewhat [as booster])",
    ],
    [
        "Stronger tiers (significant, severe, catastrophic)",
        "Hedges with reductive function (around, kind of [as approximators]) — belong to HEDGES",
        "Asseverative markers (really [as truth marker]) — belong to Actually",
    ],
    [
        trap("really", "POS_DRIFT", "Polysemous: intensifier vs. asseverative — only intensifier use qualifies"),
        trap("significant", "HYPONYM_OVERSHOOT", "Moderate tier"),
    ],
    ["very", "quite", "pretty", "so"],
)

D["FIGHTING"] = cat(
    "Pathos", "Sentiment", "anger",
    "Combative / aggressive language (verbs of attack and slur-style insults) signaling hostile, anger-laden registers (annihilate, attack, idiot, garbage).",
    "LIWC anger; combative discourse as anger expression.",
    [
        "Aggressive action verbs (annihilate, attack, crush, destroy, obliterate, bulldoze, demolish)",
        "Pejorative epithets used as labels (idiot, fool, stupid, garbage, trash, nonsense, ridiculous)",
        "Hostility-coded adjectives (vicious, savage, brutal)",
    ],
    [
        "Pure name-calling labels with propaganda-target framing (traitor, terrorist, puppet) — belong to PROP_NAMECALL",
        "Loaded propaganda epithets with ideological cast (corrupt, evil) — belong to PROP_LOADED",
        "Neutral combat-domain words used non-pejoratively",
    ],
    [
        trap("traitor", "TOPICAL_NEIGHBOR", "Propaganda name-calling; belongs to PROP_NAMECALL"),
        trap("evil", "TOPICAL_NEIGHBOR", "Loaded ideological epithet; belongs to PROP_LOADED"),
    ],
    ["annihilate", "attack", "idiot", "garbage", "ridiculous"],
)

# ============================================================
# PATHOS — Impact
# ============================================================

D["IMPACT_GAIN"] = cat(
    "Pathos", "Impact", "gain_framing",
    "Words framing future or present consequences as GAINS, benefits, or improvements (benefit, advantage, improve, prosperity).",
    "Prospect Theory (Tversky & Kahneman 1981); gain-framed messages.",
    [
        "Gain nouns (benefit, advantage, gain, opportunity, growth, success, prosperity, reward, relief)",
        "Improvement verbs (improve, enhance, accomplish, flourish, thrive, win)",
        "Positive-direction quantitative verbs in gain context (increase [as gain], reduce [costs/risks])",
    ],
    [
        "Loss / cost language (loss, harm, damage) — belong to IMPACT_LOSS",
        "Threat language (catastrophic, deadly) — belong to IMPACT_THREAT",
        "Pure positive sentiment without consequence framing (happy, nice)",
    ],
    [
        trap("harm", "VALENCE_FLIP", "Loss frame"),
        trap("happy", "TOPICAL_NEIGHBOR", "Positive emotion, not consequence frame"),
    ],
    ["benefit", "advantage", "improve", "growth", "success"],
)

D["IMPACT_LOSS"] = cat(
    "Pathos", "Impact", "loss_framing",
    "Words framing future or present consequences as LOSSES, costs, or harms (loss, cost, damage, harm, sacrifice).",
    "Prospect Theory; loss-framed messages and loss aversion.",
    [
        "Loss nouns (loss, cost, damage, harm, deficit, penalty, sacrifice, waste, suffering, pain)",
        "Loss verbs (lose, deprive, sacrifice, suffer)",
        "Negative-direction outcome words (failure, decline)",
    ],
    [
        "Threat / catastrophe language (deadly, catastrophic) — belong to IMPACT_THREAT",
        "Gain language — opposite frame",
        "Pure negative sentiment without consequence framing (sad, unhappy)",
    ],
    [
        trap("benefit", "VALENCE_FLIP", "Gain frame"),
        trap("catastrophic", "HYPONYM_OVERSHOOT", "Threat severity tier; belongs to IMPACT_THREAT"),
    ],
    ["cost", "loss", "damage", "harm", "sacrifice"],
)

D["IMPACT_THREAT"] = cat(
    "Pathos", "Impact", "threat_severity",
    "High-severity threat and harm markers signaling catastrophic / fatal consequences (catastrophic, deadly, disaster, crisis).",
    "Witte & Allen (2000) fear appeals; threat severity is a core EPPM input.",
    [
        "Catastrophe nouns (disaster, crisis, catastrophe, emergency, calamity, ruin)",
        "Severity adjectives (catastrophic, deadly, fatal, severe, devastating, terrible, dire)",
        "Collapse / destruction nouns (collapse, destruction, annihilation)",
    ],
    [
        "Generic loss markers without severity (cost, harm) — belong to IMPACT_LOSS",
        "Generic negative sentiment (bad, unfortunate)",
        "Fear-emotion words (afraid, scared) — belong to PROP_FEAR / Sentiment.fear",
    ],
    [
        trap("harm", "HYPERNYM_DILUTION", "Generic loss; not high-severity threat"),
        trap("afraid", "TOPICAL_NEIGHBOR", "Fear emotion, not threat severity marker"),
    ],
    ["catastrophic", "disaster", "crisis", "deadly", "devastating"],
)

D["IMPACT_WILL"] = cat(
    "Pathos", "Impact", "future_projection",
    "Future-tense markers and forward-projection cues that locate consequences in the future (will, shall, gonna, future, ahead, next).",
    "Kim et al. (2025) gain/loss framing × future certainty; future projection amplifies framing.",
    [
        "Future modal auxiliaries (will, shall, gonna, going to, 'll)",
        "Future-time nouns and adverbs (future, next, ahead, tomorrow, soon, later)",
        "Forward-projection phrasal markers (in the years to come, in the long run)",
    ],
    [
        "Past-tense markers (was, did, ago)",
        "Present markers (now, today) — belong to SPEC_PSYCH_NEAR",
        "Far-distant temporal (decades, century) — admit only in projection-frame",
    ],
    [
        trap("ago", "VALENCE_FLIP", "Past, not future"),
        trap("now", "TOPICAL_NEIGHBOR", "Present, not future"),
    ],
    ["will", "shall", "future", "ahead", "next"],
)

# ============================================================
# PATHOS — Reciprocity
# ============================================================

D["REC_CONCESSION"] = cat(
    "Pathos", "Reciprocity", "concession_framing",
    "Markers framing the speaker as making a CONCESSION or sacrifice to the addressee, triggering reciprocal obligation (compromise, give in, meet halfway).",
    "Door-in-the-Face (Cialdini 1975; O'Keefe 1998); reciprocal concession.",
    [
        "Concession verbs/nouns in reciprocal frame (concede, give in, yield, compromise, meet halfway)",
        "Sacrifice-framing markers (I'll sacrifice, willing to give up, make an exception for you)",
        "Soft-concession phrasal markers (this once, just for you, I can do this for you)",
    ],
    [
        "Argumentative concessions (admittedly, granted) — belong to ARG_STYLE.concession_refute",
        "Pure agreement without sacrifice signal (I agree)",
    ],
    [
        trap("admittedly", "TOPICAL_NEIGHBOR", "Argumentative concession, not reciprocal"),
    ],
    ["compromise", "meet halfway", "give in", "yield"],
)

D["REC_MUTUAL_EXCHANGE"] = cat(
    "Pathos", "Reciprocity", "mutual_benefit",
    "Words framing a proposal as mutually beneficial reciprocal exchange (win-win, mutual, reciprocal, both sides benefit, partnership).",
    "Reciprocity norm (Gouldner 1960); mutual exchange triggers compliance via fairness.",
    [
        "Mutuality adjectives / nouns (mutual, reciprocal, bilateral, two-way, win-win, partnership)",
        "Exchange-framing verbs (exchange, share, trade, partner)",
        "Both-parties phrasal markers (both sides, all of us, together [as partnership])",
    ],
    [
        "One-sided benefit markers — belong to IMPACT_GAIN",
        "Concession framings — belong to REC_CONCESSION",
        "Pure 'we' identification without exchange semantics",
    ],
    [
        trap("benefit", "TOPICAL_NEIGHBOR", "Generic gain, not mutual exchange"),
    ],
    ["mutual", "win-win", "reciprocal", "partnership", "both sides"],
)

# ============================================================
# PATHOS — Scarcity and Urgency
# ============================================================

D["SCARCITY_QUANTITY"] = cat(
    "Pathos", "Scarcity and Urgency", "exclusivity_quantity",
    "Markers of scarcity, exclusivity, and limited quantity that heighten perceived value (limited, exclusive, only, last few, while supplies last).",
    "Scarcity heuristic (Cialdini); Worchel et al. (1975); reactance under restricted choice.",
    [
        "Scarcity quantifiers (limited, scarce, rare, few, only, just X left)",
        "Exclusivity markers (exclusive, members-only, by invitation, restricted)",
        "Stock-depletion phrasal markers (while supplies last, last chance, final units)",
    ],
    [
        "Pure vague quantifiers (some, several) — belong to SPEC_VAGUE",
        "Concrete numerical quantities without scarcity framing (three units)",
        "Time-urgency markers (deadline, hurry) — belong to URGENCY_TIME",
    ],
    [
        trap("hurry", "TOPICAL_NEIGHBOR", "Time-urgency; belongs to URGENCY_TIME"),
        trap("many", "VALENCE_FLIP", "Abundance, not scarcity"),
    ],
    ["limited", "exclusive", "only", "rare", "scarce"],
)

D["URGENCY_TIME"] = cat(
    "Pathos", "Scarcity and Urgency", "temporal_urgency",
    "Time-urgency markers that compress decision time and intensify pressure (hurry, deadline, immediately, act now, expires).",
    "Reactance and decision pressure under deadlines (Brehm 1966).",
    [
        "Urgency directives (hurry, act now, don't wait, immediately, right away)",
        "Deadline markers (deadline, expires, by [date], before it's too late)",
        "Time-compression phrasal markers (running out, no time, last minute)",
    ],
    [
        "Quantity scarcity markers (limited, only) — belong to SCARCITY_QUANTITY",
        "Generic temporal nearness (today, now) — belong to SPEC_PSYCH_NEAR unless functioning as urgency directive",
    ],
    [
        trap("limited", "TOPICAL_NEIGHBOR", "Quantity scarcity; belongs to SCARCITY_QUANTITY"),
        trap("today", "POS_DRIFT", "Temporal nearness; admit only when functioning as urgency directive"),
    ],
    ["hurry", "deadline", "immediately", "act now", "expires"],
)

# ============================================================
# PATHOS — Propaganda
# ============================================================

D["PROP_LOADED"] = cat(
    "Pathos", "Propaganda Cues", "emotional_charge",
    "Emotionally loaded words with strong evaluative cast (positive or negative) used to bypass reasoning (corrupt, evil, glorious, heroic, traitor, patriot).",
    "SemEval propaganda (Da San Martino 2019); loaded language as emotional-charge cue.",
    [
        "Negative-loaded labels (corrupt, evil, disgusting, shameful, criminal, vile)",
        "Positive-loaded labels (glorious, heroic, noble, sacred, virtuous, pure)",
        "Ideologically charged epithets (traitor, patriot, martyr) when used as loaded labels",
    ],
    [
        "Person-targeted insult labels with name-calling function (idiot, fool, liar) — belong to PROP_NAMECALL",
        "Combative action verbs (attack, destroy) — belong to FIGHTING",
        "Generic positive/negative adjectives without high evaluative cast (good, bad, nice)",
    ],
    [
        trap("idiot", "TOPICAL_NEIGHBOR", "Name-calling label; belongs to PROP_NAMECALL"),
        trap("attack", "TOPICAL_NEIGHBOR", "Combative verb; belongs to FIGHTING"),
        trap("good", "HYPERNYM_DILUTION", "Generic, not strongly loaded"),
    ],
    ["corrupt", "evil", "glorious", "heroic", "traitor", "patriot"],
)

D["PROP_NAMECALL"] = cat(
    "Pathos", "Propaganda Cues", "emotional_charge",
    "Person-targeted insult labels and slurs that demean an opponent without argument (idiot, fool, liar, terrorist, puppet).",
    "Propaganda devices (Lee & Lee 1939); name-calling as ad hominem heuristic.",
    [
        "Direct insult labels (idiot, fool, moron, imbecile, coward)",
        "Truth-attacking labels (liar, fraud, fake, phony)",
        "Political demonization labels (terrorist, puppet, dictator) when used as ad hominem",
    ],
    [
        "Loaded ideological epithets without person-target (evil, glorious) — belong to PROP_LOADED",
        "Aggressive action verbs (attack, destroy) — belong to FIGHTING",
        "Generic negative adjectives (bad, awful)",
    ],
    [
        trap("evil", "TOPICAL_NEIGHBOR", "Loaded epithet, not person-target name-call; belongs to PROP_LOADED"),
        trap("attack", "POS_DRIFT", "Verb, not person-label"),
    ],
    ["idiot", "liar", "fool", "puppet", "terrorist"],
)

D["PROP_FEAR"] = cat(
    "Pathos", "Propaganda Cues", "emotional_charge",
    "Fear-appeal markers that invoke threat to self, family, or group to compel compliance (terrifying, nightmare, doom, attack on our way of life).",
    "Witte EPPM fear appeals; fear-arousal as compliance lever.",
    [
        "Fear-emotion words (terrifying, frightening, horrifying, nightmare, dread)",
        "Existential-threat phrasal markers (end of [X], doom, apocalypse, attack on our values)",
        "Personal-threat markers (your family, your children, our way of life [in fear context])",
    ],
    [
        "Threat-severity adjectives without fear-arousal emotional content (deadly, catastrophic) — belong to IMPACT_THREAT",
        "Loaded ideological labels (corrupt, evil) — belong to PROP_LOADED",
    ],
    [
        trap("catastrophic", "HYPERNYM_DILUTION", "Severity marker; belongs to IMPACT_THREAT"),
    ],
    ["terrifying", "nightmare", "doom", "frightening"],
)

D["PROP_WHATABOUT"] = cat(
    "Pathos", "Propaganda Cues", "logical_distortion",
    "Whataboutism markers that deflect criticism by redirecting to opponent's faults (what about, but they too, you also did).",
    "Propaganda devices; tu quoque fallacy as distortion.",
    [
        "Whataboutism phrasal markers (what about, but what about, you yourself, you too)",
        "Deflection openers (let's talk about your, why don't you mention)",
        "Tu-quoque retort framings (the same applies to you, you do it as well)",
    ],
    [
        "Pure counter-arguments without deflection (however, on the contrary)",
        "Doubt-sowing markers (allegedly, supposedly) — belong to PROP_DOUBT",
    ],
    [
        trap("however", "TOPICAL_NEIGHBOR", "Counter-argument, not whataboutism deflection"),
    ],
    ["what about", "you too", "but what about"],
)

D["PROP_DOUBT"] = cat(
    "Pathos", "Propaganda Cues", "logical_distortion",
    "Doubt-sowing markers that undermine credibility without direct refutation (alleged, so-called, questionable, supposedly, unreliable).",
    "Propaganda devices; manufacturing uncertainty as distortion.",
    [
        "Doubt-prefixing modifiers (alleged, so-called, supposed, purported)",
        "Discrediting adjectives (questionable, unreliable, dubious, suspect)",
        "Doubt-sowing adverbs (supposedly, ostensibly, allegedly when used to discredit)",
    ],
    [
        "Pure epistemic uncertainty without credibility-attack function (may, might) — belong to UNCERTAINTY",
        "Hedges (kind of, around) — belong to HEDGES",
    ],
    [
        trap("may", "TOPICAL_NEIGHBOR", "Epistemic modal without credibility-attack; belongs to UNCERTAINTY"),
        trap("kind of", "TOPICAL_NEIGHBOR", "Hedge, not doubt-attack"),
    ],
    ["alleged", "so-called", "questionable", "supposedly", "unreliable"],
)

D["PROP_FLAG"] = cat(
    "Pathos", "Propaganda Cues", "heuristic_identity_appeals",
    "Flag-waving / nationalism markers appealing to in-group patriotic identity (patriot, our nation, motherland, fatherland, our values).",
    "Propaganda devices (Lee & Lee 1939); nationalistic identity appeals (Shen 2025).",
    [
        "Nationalism nouns (nation, motherland, fatherland, homeland, our country)",
        "Patriotic identifiers (patriot, patriotic, our flag, our soldiers)",
        "Group-identity values phrasal markers (our way of life, our values, our heritage)",
    ],
    [
        "Bandwagon markers (everyone, majority) — belong to PROP_BANDWAGON",
        "Generic group reference without nationalist cast",
    ],
    [
        trap("everyone", "TOPICAL_NEIGHBOR", "Bandwagon; belongs to PROP_BANDWAGON"),
    ],
    ["patriot", "motherland", "our nation", "our values"],
)

D["PROP_BANDWAGON"] = cat(
    "Pathos", "Propaganda Cues", "heuristic_identity_appeals",
    "Bandwagon markers appealing to majority adoption / consensus heuristic (everyone, majority of, most people, join us, don't be left out).",
    "Propaganda devices; majority-influence heuristic.",
    [
        "Universal quantifiers in bandwagon framing (everyone, all of us, the world)",
        "Majority markers (majority, most people, everybody else, the masses)",
        "Join-the-crowd phrasal markers (join us, don't be left behind, get on board)",
    ],
    [
        "Flag-waving identity markers (patriot, our nation) — belong to PROP_FLAG",
        "Pure additive 'all' without bandwagon framing",
    ],
    [
        trap("our nation", "TOPICAL_NEIGHBOR", "Flag-waving; belongs to PROP_FLAG"),
    ],
    ["everyone", "majority", "most people", "join us"],
)

# ============================================================
# Dump
# ============================================================

if __name__ == "__main__":
    out = Path(__file__).parent / "theory_definitions.json"
    out.write_text(json.dumps(D, indent=2, ensure_ascii=False))
    print(f"Wrote {len(D)} categories to {out}")
    print(f"Categories: {sorted(D.keys())}")
