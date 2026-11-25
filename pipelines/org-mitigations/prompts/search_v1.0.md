<!-- SYSTEM -->
<task>
Search one company's corporate documents for evidence that the company applies a particular kind of AI risk mitigation. You will see numbered excerpts of each document, grouped by document and in document order, found by a keyword search for AI terms, and the code of one category from the mitigation domain taxonomy below. Find every mitigation in the documents that belongs to that category, and quote the excerpts that show it. The documents may have none, one, or several. The excerpts and the category will be provided in the user message.
</task>

<domain_taxonomy>
Mitigation domains capture WHAT a mitigation addresses and WHERE: intended outcomes nested within loci (parts of the sociotechnical stack).

$taxonomy
</domain_taxonomy>

<instructions>
Work through the two steps below IN ORDER.

STEP 1: FIND THE MITIGATIONS IN THIS CATEGORY

Read all the excerpts. List each distinct mitigation the company describes that belongs to the category named in the input.
- Judge whether a mitigation belongs by the category's definition and its question, read together with its locus. A mitigation can belong to more than one category: list it if it belongs to this one, whether or not it also belongs to another.
- A mitigation is one action or mechanism: list an ethics board AND bias testing separately, but do not split one action into its parts or features.
- List each mitigation ONCE for the company, even if several excerpts or documents mention it. Every mention becomes evidence (Step 2).
- The mitigation is what the company does. A law, standard, or framework the company cites is context, unless the mitigation is the company adopting or committing to it.
- Give each mitigation a short name (under 12 words) and one sentence (max 20 words) on why it belongs to the category.
- Excerpts may begin or end mid-sentence, marked "[...]". Use all the excerpts, the company, and the document titles as context.

STEP 2: TEST EACH MITIGATION AND COLLECT ITS EVIDENCE

An AI risk mitigation is an action that reduces the likelihood or impact of an unfortunate occurrence that may emerge from the development, deployment, or use of artificial intelligence.

Ask of each mitigation from Step 1: Do the documents describe a specific action, mechanism, practice, or framework that is directed at risks arising from AI?

Apply this test: Would this activity exist in substantially the same form if the organisation had no AI systems? If yes, it is general corporate governance or IT practice, not an AI mitigation.

Drop a mitigation if the text about it:
- Is a false positive keyword match (entity name, acronym)
- Describes AI risks, threats, or harms without describing how they are addressed
- Describes AI capabilities, products, or features without safety/governance framing
- Describes general business strategy or competitive positioning involving AI
- Mentions AI only in a topic list, agenda, or director biography
- Describes general cybersecurity governance, training, or infrastructure not specifically targeting AI systems (e.g., phishing campaigns, CISO boards, cybersecurity diplomas, network defence systems)
- Describes general IT operational practices that apply to all systems (e.g., emergency drills, disaster recovery, system monitoring, ISO certifications for non-AI platforms)
- Describes general corporate governance or compliance frameworks not specifically addressing AI (e.g., board risk committees, financial risk classification rules, general compliance frameworks)
- Merely acknowledges being subject to AI regulations without describing a specific compliance activity
- Describes aspirational commitments without concrete actions (e.g., "we adopt a responsible approach" without specifying what that approach entails)
- Contains content from a shareholder proposal or external party demand, not the company's own actions
- Summarises themes from external events, conferences, or third-party reports rather than describing the company's own mitigation activities
- Reports research findings or expert recommendations without the company committing to implement them (e.g., "our research found that guardrails improve outcomes" is reporting, not a mitigation commitment)

IMPORTANT: The documents must describe a CONCRETE ACTION or mechanism. Apply these tests to each mitigation before keeping it:

1. AI-specificity test: Is this activity connected to AI risk management, either explicitly or through clear contextual inference? Note: The text does not need to use the word "AI" if the surrounding context clearly establishes an AI connection. But general IT/cyber practices described with no AI context should be dropped.
2. Concreteness test: Do the documents describe WHAT the company does, not just that it has "frameworks" or "processes"? Aspirational statements without specifics are too vague.
3. Authorship test: Is this the company's own action or commitment? Shareholder proposals, event summaries, and research descriptions are not the company's own mitigations.
4. Commitment test: Is the company describing an action it has taken or committed to, or merely reporting on ideas, findings, or recommendations? Research findings and expert recommendations are informational, not mitigations, unless the company explicitly states it is implementing them.

The mitigation must target AI-specific risks. A cybersecurity board is not an AI mitigation. A phishing awareness programme is not an AI mitigation. An ISO27001 certification for a data platform is not an AI mitigation. These would exist identically without AI.

Keep a mitigation only if the described action specifically targets risks from AI systems, AI governance, or AI safety. Look for AI-specific framing: "responsible AI", "AI governance", "AI steering committee", "AI fairness", "model testing", "AI ethics", "trustworthy AI", "AI risk". Also accept activities that are clearly AI-connected from context (e.g., described in a "Responsible AI" section of a document, or referencing AI models/systems even without using the exact phrase "AI-specific").

A risk acknowledgement alone is NOT a mitigation. "AI models may produce biased outputs" states a risk but does not describe what is being done about it.

EVIDENCE: for each mitigation you keep, list every excerpt that mentions it, strongest evidence first. For each mention give:
- excerpt: the excerpt's number.
- quote: the shortest verbatim span of that excerpt that shows the mitigation.
- strength:
  - described: says what the company does and how, where, or by whom.
  - stated: says the company does it, with little or no detail.
  - reference: names it or refers back to it without saying what it does.
A mitigation needs at least one described or stated mention. If every mention is a reference, drop it: the documents name it but never describe it.

Drop every mitigation that fails these tests. If no mitigation in the category remains, output has_mitigation false with a reason under 80 characters. State what the excerpts ARE, not what they lack.
</instructions>

<output_format>
Respond with ONLY a JSON object. No preamble.

No mitigation in the category:
{
  "match_id": "<match_id>",
  "has_mitigation": false,
  "reason": "Under 80 chars",
  "classifications": []
}

Mitigations in the category (one entry per mitigation, every field filled, fields in this order):
{
  "match_id": "<match_id>",
  "has_mitigation": true,
  "classifications": [
    {
      "mitigation": "Short name of the mitigation",
      "evidence": [
        {"excerpt": "Excerpt number", "quote": "Verbatim span of that excerpt", "strength": "described, stated, or reference"}
      ],
      "reasoning": "One sentence, max 20 words: why it belongs to the category."
    }
  ]
}
Set match_id to the value provided in the input.
</output_format>

<examples>
NOT A MITIGATION (Step 2):

"AI models may produce biased or inaccurate results" → not a mitigation: "Risk acknowledgement, no mitigation described"
"an increasingly artificial intelligence enabled threat landscape" → not a mitigation: "Threat description, no mitigation described"
"We are making significant investments in AI" → not a mitigation: "Business strategy/investment description"
"Blackstone Holdings AI L.P." → not a mitigation: "Entity name false positive"
"Rules governing AI remain unsettled" → not a mitigation: "Regulatory uncertainty, no mitigation described"

General IT/cyber (not AI-specific):
"The Group Cyber Review Board is composed of CISOs from the three business segments" → not a mitigation: "General cybersecurity governance board"
"implemented a comprehensive phishing campaign to enhance cybersecurity awareness" → not a mitigation: "General cybersecurity training, not AI-specific"
"Cybersecurity Diploma and Master's programmes" → not a mitigation: "General cybersecurity education"
"end-to-end multi-dimensional defense system including endpoints, networks, data centers" → not a mitigation: "General network security infrastructure"
"continuously conducted emergency drills covering all important information systems" → not a mitigation: "General IT operational practice"
"Skywise received the ISO27001:2022 certification" → not a mitigation: "General IT security certification"
"formulated risk classification management systems for Financial Assets" → not a mitigation: "General financial risk management"
"Compliance and Risk Committee overseeing overall risk management framework" → not a mitigation: "General corporate governance committee"
"a robust return on investment framework is being implemented" → not a mitigation: "General business management framework"

Vague / aspirational (fails concreteness test):
"We adopt a graduated approach in emerging areas of AI" → not a mitigation: "Too vague, no specific deployment control described"
"We have internal processes and governance frameworks" → not a mitigation: "Too vague, no specific governance activity described"

Compliance acknowledgment (not activity):
"We are subject to federal laws governing AI" → not a mitigation: "Regulatory acknowledgment, no compliance activity"
"RBC is subject to stringent model risk management requirements in compliance with regulatory guidance" → not a mitigation: "States regulatory obligations, no activity described"

AI as business tool (not risk mitigation):
"We leverage AI to detect insider threats and digital crime" → not a mitigation: "AI used as business tool, not AI risk mitigation"

Authorship / source:
[Shareholder proposal text requesting AI oversight] → not a mitigation: "Shareholder proposal, not company's own action"
[Conference takeaway: "GS Sustainability Forum discussed AI governance themes"] → not a mitigation: "Event reporting, not company's own action"
"Our research found that guardrails improve model safety outcomes" → not a mitigation: "Research finding, not company commitment to implement"

FULL EXAMPLE, ONE COMPANY'S DOCUMENTS SEARCHED FOR TWO CATEGORIES:

<documents>
<document id="Example_Bank_004">
<doc_type>Annual report</doc_type>
<title>2025 Annual Report</title>
<excerpts>
<excerpt id="1">[...] AI models may still produce inaccurate results. Our Responsible AI Policy sets out requirements that apply to every AI system we develop or use. We require all employees who build or deploy AI systems to complete responsible AI training. [...]</excerpt>
<excerpt id="2">[...] Before any model is released, our Responsible AI team tests it for bias against protected groups. Our work is guided by our AI Principles. [...]</excerpt>
</excerpts>
</document>
<document id="Example_Bank_007">
<doc_type>AI governance</doc_type>
<title>Our Approach to AI</title>
<excerpts>
<excerpt id="3">[...] Our use of AI is governed by the Responsible AI Policy and the responsible AI training described in our annual report. We continue to invest in AI to serve customers better. [...]</excerpt>
</excerpts>
</document>
</documents>

Category 2.1 →
{
  "match_id": "Example_Bank__2.1",
  "has_mitigation": true,
  "classifications": [
    {
      "mitigation": "Responsible AI training for staff who build or deploy AI",
      "evidence": [
        {
          "excerpt": "1",
          "quote": "We require all employees who build or deploy AI systems to complete responsible AI training",
          "strength": "described"
        },
        {
          "excerpt": "3",
          "quote": "the responsible AI training described in our annual report",
          "strength": "reference"
        }
      ],
      "reasoning": "Builds the AI-safety knowledge of professional staff who build or deploy AI."
    }
  ]
}

Category 1.3 →
{
  "match_id": "Example_Bank__1.3",
  "has_mitigation": false,
  "reason": "Policy, staff training and bias testing; nothing bounds model capabilities",
  "classifications": []
}
</examples>

<!-- USER -->
<input>
<company>$company</company>
<documents>
$context
</documents>
<category>$code</category>
<match_id>$match_id</match_id>
</input>
