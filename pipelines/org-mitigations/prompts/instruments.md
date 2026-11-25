<!-- SYSTEM -->
<task>
Classify an AI risk mitigation by its MITIGATION INSTRUMENT: the broad tool, lever, or mechanism used to create change. The mitigation was found in one company's corporate documents, and its evidence is quotes from them. The mitigation will be provided in the user message.

Note: this taxonomy classifies HOW the mitigation creates change (its lever), not what it addresses. A law mandating interpretability and an interpretability software library address the same domain but use different instruments (Law vs Technical).
</task>

<taxonomy>
The taxonomy has 3 substantive instrument modalities (Inform, Govern, Implement) plus Other. Always classify at level 2.

$instruments
</taxonomy>

<instructions>
Follow these two reasoning steps IN ORDER:

STEP 1 — LEVER: what is the PRIMARY lever this mitigation uses?
- Building/sharing knowledge, evidence, or information? -> Inform (1)
- Setting rules an actor is expected to follow? -> Govern (2)
- A built artefact, a carried-out procedure, ongoing observation, or a test/check? -> Implement (3)

STEP 2 — INSTRUMENT: within that modality, which specific instrument? Classify by the mitigation's OWN primary lever — the thing the mitigation itself IS. For "a regulation requiring audits", the mitigation IS a binding rule -> 2.1.

NOTE ON MARKET/INCENTIVE MECHANISMS: there is no Market instrument. Pricing/subsidy/funding/tax mechanisms are captured on the DOMAIN axis (Ecosystem Coordination). On THIS axis, code by the lever that delivers them: created by statute -> 2.1 Law; a voluntary commitment/pledge -> 2.2 Standards; a self-authored program -> 2.3 Policies; a program carried out -> 3.2 Practices. If none fit, the market lever itself -> O.A.

BOUNDARY TESTS — KEY CONFUSIONS:

2.1 (Law) vs 2.2 (Standards) vs 2.3 (Policies): source of the rule.
- 2.1 = rules created/adopted by an EXTERNAL authority with jurisdiction (statute, regulation, licensing, court rulings, contracts, liability regimes).
- 2.2 = SHARED rules an actor adopts from a peer/industry body (external, voluntary): technical standards, codes of practice, industry pledges, shared frameworks.
- 2.3 = rules an actor authors FOR ITSELF (internal, self-authored): internal policies, public commitments, named plans/frameworks the actor writes.
- A standard mandated by regulation stays 2.2; the mandating regulation is 2.1. A named framework the org authors itself is 2.3; a shared industry framework it adopts is 2.2.

CREATE/ADOPT vs DO (Govern vs 3.2 Practices):
- Govern (2.1/2.2/2.3) = creating a rule, or voluntarily committing to / adopting one (the decision to be bound), where the substance IS a named rule/policy/standard/commitment/plan/framework.
- 3.2 = following/implementing/operating — carrying out a procedure that is not itself a named rule. "Adopt the NCSC code of practice" -> 2.2; "run the review workflow" -> 3.2.
- Do NOT default to Govern just because "policy"/"plan" is mentioned: "deploy content filters per our safety policy" is Technical (3.1); the policy is context.

MONITORING vs EVALUATION vs PRACTICES vs TECHNICAL (within Implement):
- 3.3 Monitoring = CONTINUOUS, ongoing observation to surface problems over time (run-time monitoring, logging, drift detection). A built monitor is Monitoring by FUNCTION, not Technical.
- 3.4 Evaluation = a DISCRETE evaluative act checking against a standard/expectation (audit, benchmark, red-team exercise, capability evaluation).
- 3.2 Practices = a one-off or repeated procedure people carry out that is not itself continuous observation or a discrete test.
- 3.1 Technical = a built tool/feature whose purpose is to operate as part of the system/defenses.

1.1 (Research) vs 1.2 (Disclosure) vs 3.4 (Evaluation): knowledge, sharing, or checking.
- 1.1 = open-ended knowledge GENERATION with no criterion (studies, datasets, foresight scanning).
- 1.2 = open communication/SHARING of information across actors (incident disclosure, reporting, registries) — not generating new knowledge, not a rule.
- 3.4 = checking AGAINST a standard/expectation (audit, evaluation, benchmarks, compliance checking).
- Education/training/literacy -> Training domain (an ex-instrument -> O.A on this axis), not Research.

FUNCTION OVER FORM (3.1 vs 3.4): when a mitigation is a built tool, ask its FUNCTION.
- Purpose is testing/evaluating/benchmarking -> 3.4 (test harnesses, benchmark suites, evaluation environments).
- Purpose is to operate as part of the system/defenses -> 3.1 (content filters, sandboxes, encryption, access controls).

3.1 (Technical) vs 3.2 (Practices): built vs carried out — judge by SUBSTANCE.
- 3.1 = the operative content is something BUILT (tool, filter, architecture, encryption) even when phrased as "handling/management".
- 3.2 = the operative content is a procedure PEOPLE carry out (workflow, process, guidance).

GUIDES/FRAMEWORKS/CATALOGUES: classify by the SUBSTANCE delivered. A red-teaming guide -> 3.4; a catalogue of technical controls -> 3.1; a guide of operational procedures -> 3.2; a shared norm-setting principles document -> 2.2; a self-authored named framework -> 2.3.

UMBRELLA MITIGATIONS: choose the DOMINANT lever across the concrete examples; do not default to Other. A specific code with lower confidence beats an Other code.

SPECIFICITY & OTHER:
- Always classify at level 2.
- Clear mitigation, an ex-instrument lever (training, advocacy, market mechanism) or otherwise no modality fits -> O.A (Additional).
- Too vague to identify a lever, or broad/ambiguous/cross-modality -> O.C (Cross-cutting/unclassifiable). Prefer O.C over a weak guess.

SINGLE CLASSIFICATION: return exactly ONE code — the dominant instrument.

DOCUMENT CONTEXT: <document_context> lists ALL mitigations found in the same documents as the one in <mitigation>; classify ONLY the mitigation in <mitigation>.
</instructions>

<output_format>
Respond with ONLY a JSON object. No preamble. Fields in this order:
{
  "lever": "One sentence: what is the primary lever this mitigation uses?",
  "modality": "1, 2, 3, or O",
  "instrument_code": "CODE",
  "reasoning": "One sentence, max 20 words."
}
</output_format>

<examples>
Name: "AI incident database for researchers"
{
  "lever": "Builds a shared evidence resource with no test criterion.",
  "modality": "1",
  "instrument_code": "1.1",
  "reasoning": "Knowledge/evidence resource — Research & Evidence."
}

Name: "Disclose incidents to a regulator / publish a transparency report"
{
  "lever": "Openly communicates information to other actors.",
  "modality": "1",
  "instrument_code": "1.2",
  "reasoning": "Sharing/reporting of information — Information Sharing & Disclosure."
}

Name: "EU AI Act"
{
  "lever": "Binding legal rules from an external authority.",
  "modality": "2",
  "instrument_code": "2.1",
  "reasoning": "Binding legislation — Law & Regulation."
}

Name: "Adopt the NIST AI RMF / sign an industry safety pledge"
{
  "lever": "Voluntarily adopting a shared peer/industry rule.",
  "modality": "2",
  "instrument_code": "2.2",
  "reasoning": "Shared external voluntary standard — External Standards."
}

Name: "Author an internal responsible-AI policy / named safety framework"
{
  "lever": "Creating a rule for itself, internally.",
  "modality": "2",
  "instrument_code": "2.3",
  "reasoning": "Self-authored internal rule — Internal Policies."
}

Name: "Content filter / sandboxing / watermarking"
{
  "lever": "Something built into the technical system.",
  "modality": "3",
  "instrument_code": "3.1",
  "reasoning": "Built technical control — Technical Artifacts."
}

Name: "Incident-response procedure / pre-deployment checklist"
{
  "lever": "A procedure people carry out.",
  "modality": "3",
  "instrument_code": "3.2",
  "reasoning": "Carried-out procedure — Practices & Processes."
}

Name: "Continuous run-time behaviour monitoring / drift detection"
{
  "lever": "Ongoing observation of the system to surface problems over time.",
  "modality": "3",
  "instrument_code": "3.3",
  "reasoning": "Continuous ongoing observation — Monitoring."
}

Name: "Third-party audit / benchmark suite / red-teaming exercise"
{
  "lever": "Checking systems against a standard or expectation.",
  "modality": "3",
  "instrument_code": "3.4",
  "reasoning": "Discrete evaluative act — Evaluation & Audit."
}

Name: "Red-team / evaluator training program for staff"
{
  "lever": "An education/training lever folded into the domain axis.",
  "modality": "O",
  "instrument_code": "O.A",
  "reasoning": "Training is an ex-instrument — tag the instrument as Other (Additional)."
}

Name: "Safety culture"
{
  "lever": "Too vague to identify a specific lever.",
  "modality": "O",
  "instrument_code": "O.C",
  "reasoning": "No identifiable instrument from the name — broad/unclassifiable."
}
</examples>

<!-- USER -->
<document_context>
All mitigations found in the same documents as the one to classify:
$context_mitigations
</document_context>

<mitigation>
<name>$name</name>
<description>$description</description>
<evidence>
$evidence
</evidence>
</mitigation>
