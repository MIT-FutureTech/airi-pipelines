# AGORA's Scope

> Source: CSET AGORA scoping and screening documentation (transcribed from
> screenshots supplied 2026-07-28). This file is the reference definition used by
> `assess_scope.py` to score OECD.AI policy initiatives for fit with the AGORA
> database.

---

## 1. Scoping definition

AGORA includes **laws, regulations, standards, and similar documents**
(collectively, "documents") that **directly and substantively address** the
**development, deployment, or use** of **artificial intelligence technology**.

We generally follow the EU AI Act's definition of artificial intelligence as
"machine-based system[s] designed to operate with varying levels of autonomy and
that may exhibit adaptiveness after deployment and that, for explicit or implicit
objectives, infers, from the input [they receive], how to generate outputs such as
predictions, content, recommendations, or decisions that can influence physical or
virtual environments."

AGORA's scoping definition and its elements (not least "directly and
substantively") are inescapably vague. Ultimately, whether or not a document is
within the scope of AGORA — an AGORA document — is a judgment call for the
analyst. Here are some rules of thumb to guide analyst judgment:

### 1.1 The "substantively" threshold — operative text

- For our purposes, a document does **not** "substantively" address artificial
  intelligence if it only mentions AI in **contextual or non-operative text**
  (e.g., "findings of Congress" provisions in bills, Federal Register
  supplementary text accompanying a new regulation).
  - Note, though: **"operative language" is broader than "has legal force."**
    Think of "operative text" as text that is meant to shape behavior in a
    particular way. An observation of fact ("AI is growing rapidly") is not
    operative, but even high-level norms and prescriptions ("The Department's AI
    systems should be safe and secure") are in.
  - Necessarily, a document that consists **entirely of non-operative text is out
    of scope**. Many government announcements, press releases, etc. are entirely
    non-operative — but not all; sometimes a government office will release actual
    policy in the form of a press release (for example).

- Beyond that threshold, the "substantively" requirement is **not meant to be an
  especially high bar**. Documents will ordinarily qualify even if they do
  something related to AI that seems relatively trivial, such as requiring a
  report or briefing. (However, such documents may be marked as *lower
  significance*.)

### 1.2 Subject-matter proximity to AI

- Documents addressing **related concepts such as machine learning, machine
  autonomy, or algorithmic decision making** will ordinarily qualify.
- Documents that address **broad concepts that *could* include AI** (e.g.,
  "emerging technologies," "data science") **do not qualify** without some other
  indication that AI specifically is at issue.
- Documents addressing **automated or algorithmic data processing, without more**,
  may or may not qualify depending on the complexity of the processing and the
  nature of the output.
  - It can be tricky to decide whether references to "algorithms" are enough on
    their own to make a document in scope. Consider the context and use case (to
    the extent they are indicated in the document). If it seems like the algorithm
    in question is being used for **complex judgment, autonomous action, or in
    other ways we tend to associate with AI**, that would support an in-scope
    determination. (Possible examples: "facial recognition algorithm,"
    "algorithms for autonomous driving.") But if there's just a vague reference to
    algorithms in general, or to algorithms less obviously overlapping with AI,
    the document may not be in scope. (Possible examples: "encryption algorithm,"
    "data processing algorithm.")

### 1.3 Downstream consequences

- Documents that **solely address downstream *consequences*** of the development,
  deployment, or use of AI (e.g., job loss) are **less likely to qualify**.

### 1.4 Proportion — the "directly and substantively" prong

- **Lengthy documents in which AI plays a small and isolated role are less likely
  to qualify**, given the "directly and substantively" prong of the scoping
  definition — assuming the AI-addressing provisions are not reasonably
  *separable*, in which case they may be separated and included individually.
  - An example of AI playing a role that is "small" but *not* "isolated" is if AI
    is used in only one section or definition of a longer document, but then that
    section or definition is referred to more widely in the document.
  - Another way to think of "directly and substantively" might be: **does AI play
    at least a somewhat significant or pervasive role in the document as a whole**
    (or a provision, in the case of a package)? A short mention of AI could
    definitely clear this bar.

### 1.5 Reports and recommendations

- Proposed legislation, lists of principles, etc. included in **think tank
  reports, reports of expert commissions, and similar documents may be in scope**,
  provided they take the form of **specific policy actions or actual draft
  legislation**. Treat such recommendations as the operative text of the document
  and **ignore the rest of the reports**.

### 1.6 Implementing documents of broad laws

Note that even if a broad law falls outside of the scope of AGORA because it fails
to directly and substantively address AI (e.g., the Civil Rights Act of 1964), its
**implementing or related documents may be in scope** (e.g., a regulation or
guidance document about applying the Civil Rights Act to racially discriminatory
AI).

---

## 2. AGORA's nominal scope (dataset documentation)

The AGORA dataset includes *laws, regulations, standards, and similar documents
that directly and substantively address the development, deployment, or use of
artificial intelligence technology*. The intent of this scoping definition is to
encompass the **large majority of documents created by lawmakers, regulators, and
standard-setters in direct response to advances in modern machine learning and
related technologies**.

Applying subjective elements of this definition, such as "directly and
substantively," inevitably involves judgment. When screening documents for
inclusion in AGORA, we try to constrain this judgment by defining heuristics
(Section 1 above).

### 2.1 The recency line

Critically, the requirement that documents "**directly**" address artificial
intelligence **generally excludes laws predating the rise of modern machine
learning**, even if they are broad enough in scope to bear on AI. We draw this
line to ensure that AGORA's scope is manageable in practice and to reinforce the
dataset's emphasis on **policies created in response to 21st century developments
in AI**, rather than the entire set of policy documents that may affect individual
sectors and governance writ large.

Note, however, that **more recent documents that tailor these broad laws to the
specific context of AI would qualify** for inclusion in AGORA. For example, while
the Civil Rights Act of 1964 would not be included in AGORA, a related federal
regulation or guidance document applying the Act to racially discriminatory AI is
within AGORA's scope.

---

## 3. Current coverage (collection priorities — *not* scope)

AGORA's nominal scope is broader than the set of documents collected to date. In
particular, the current dataset **skews toward U.S. law and policy**. New data are
added regularly and coverage is planned to broaden over time.

For now, AGORA aims to include the following documents (to the extent they are
within AGORA's scope) with a lag of no more than a few months:

- **United States federal documents** — all enacted and proposed federal laws
  since 2020; all enacted and proposed federal regulations since 2020; all enacted
  executive orders since 2020; other agency documents of major popular or
  scholarly interest.
- **United States state documents** — currently collected ad hoc; not necessarily
  comprehensive or representative.
- **Other documents** — currently collected ad hoc; not necessarily comprehensive
  or representative.

Next priorities are to broaden coverage of U.S. state documents, with the aim of
including all enacted, in-scope state laws on a going-forward basis, and to
broaden coverage of **Chinese central government documents** and **major corporate
commitments**.

> **Scoring note.** Section 3 describes *what AGORA has collected so far*, not
> what is *in scope*. A non-U.S. document is fully in scope even though current
> coverage skews U.S. Scoring must therefore be driven by Sections 1 and 2 —
> jurisdiction must **not** reduce a relevance score.

---

## 4. Scoring rubric (0–100) used by `assess_scope.py`

The score expresses **how well the document falls within AGORA's scope**, i.e. how
confidently an AGORA analyst would include it.

| Band | Meaning |
|---|---|
| **90–100** | Unambiguously in scope. A law, regulation, standard, or equivalent instrument whose central subject is AI, consisting substantially of operative text. |
| **75–89** | Clearly in scope. AI plays a significant or pervasive operative role, though the document may be broader than AI alone or lighter-touch (e.g. requires a report or briefing). |
| **60–74** | Probably in scope. Meets the definition on a reasonable reading, but with a real weakness — AI role is modest, operative content is thin, or "AI" is approached via adjacent concepts (ML, ADM). |
| **40–59** | Genuinely borderline. An analyst could decide either way. Typically: substantial non-operative content, or an algorithm/automation focus whose AI character is unclear. |
| **25–39** | Probably out of scope. AI is present but small and isolated in a lengthy document, or the content is largely announcement/description rather than operative. |
| **10–24** | Clearly out of scope. Entirely non-operative (press release, news item, project description), or AI is merely contextual. |
| **0–9** | Definitively out of scope. Not about AI at all, or addresses only "emerging technologies"/"data science" generally, or predates modern ML with no AI-specific tailoring. |

**Reminders that the model must apply:**

1. Judge the **document text**, not the initiative's title or the OECD summary.
2. **Funding programmes, research centres, networks, and public-sector AI
   projects** are common in this corpus. They are in scope only insofar as the
   document contains operative text governing AI development, deployment, or use.
   A description of a grant programme's existence is usually **not** operative
   policy; the terms and conditions governing it may be.
3. **Do not penalise non-U.S. jurisdiction or non-English language.**
4. If the supplied text is **truncated**, score on what is present and say so in
   the rationale.
