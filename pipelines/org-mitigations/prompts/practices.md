<!-- SYSTEM -->
<task>
Tag one AI risk mitigation with the practices it shows. The mitigation was found in one company's corporate documents. You will see the company's name and numbered quotes from its documents, all about that one mitigation. Decide which practices from the list below the quotes show the company carrying out: several, one, or none. For each one, note any of its subtypes the quotes show. Separately, list any named external commitments the quotes say the company has signed and any named external bodies they say it belongs to. The company and the quotes will be provided in the user message.
</task>

<practices>
Each practice has a definition, then what counts as evidence for it and what does not. Where "Does not count" names another practice in brackets, that practice fits instead. Some practices list subtypes: narrower kinds of the practice.
$practices
</practices>

<named_commitments_and_bodies>
Separately from the practices, list:
- each named external commitment, pledge or code of conduct on AI that the quotes say the company has signed or joined, such as the Frontier AI Safety Commitments, the EU AI Pact or a joint public commitment to red lines. Relation: "signed".
- each named external body, alliance, forum or consortium on AI safety or AI standards that the quotes say the company belongs to, including as a founding member, such as the Frontier Model Forum, the US AI Safety Institute Consortium, the MLCommons AI safety working group or C2PA. Relation: "member".
Give each one's full name, as the quotes write it. Do not list pledges the company makes on its own with no named external commitment, events it attended, industry associations not about AI safety, laws or regulations it is subject to, standards it follows or is certified to, or bodies it only cites, collaborates with or reports to.
</named_commitments_and_bodies>

<instructions>
- Judge only from the quotes. They are verbatim from the company's documents and are all you know about the mitigation.
- Tag a practice only if the quotes show the company itself carrying it out or having it in place. Do not tag plans, intentions, promises to do it in future, descriptions of risks, or laws and regulations the company is subject to.
- Tag a practice only if the quotes fit its definition and what counts, and not what does not count. If you are unsure, leave it out.
- One mitigation can show several practices. Tag each one that fits, and give the numbers of the quotes that show it.
- For each practice you tag, list the subtypes from that practice's list that the quotes show. List none if the quotes don't show one, or if the practice has no subtypes.
- Use each practice's and subtype's name exactly as the list writes it.
</instructions>

<output_format>
Respond with ONLY a JSON object. No preamble. Fields in this order:
{
  "match_id": "<match_id>",
  "classifications": [
    {"practice": "Practice name from the list", "subtypes": ["Subtype from that practice's list"], "quotes": [1, 2], "reasoning": "One sentence, max 20 words: how the quotes fit the definition."}
  ],
  "named": [
    {"name": "Full name of the commitment or body", "relation": "signed or member", "quotes": [1]}
  ]
}
Use an empty list for "classifications" if no practice fits, for "subtypes" if the quotes show none of the practice's subtypes, and for "named" if the quotes name no commitment or body. Set match_id to the value provided in the input.
</output_format>

<examples>
<input>
<company>Example Bank</company>
<quotes>
<quote id="1">Before release, each model is attacked by our internal red team and by external specialists who try to make it produce harmful or misleading answers.</quote>
<quote id="2">We also compare its error rates across age, gender and ethnic groups, and fix gaps before launch.</quote>
</quotes>
<match_id>Example_Bank__1.4__1</match_id>
</input>
{
  "match_id": "Example_Bank__1.4__1",
  "classifications": [
    {"practice": "Red teaming", "subtypes": ["External red teaming"], "quotes": [1], "reasoning": "Internal and external specialists try to make each model produce harmful answers before release."},
    {"practice": "Pre-deployment testing and evaluation", "subtypes": ["Bias and fairness testing"], "quotes": [2], "reasoning": "Error rates are compared across demographic groups and gaps fixed before launch."}
  ],
  "named": []
}

<input>
<company>Example Bank</company>
<quotes>
<quote id="1">The Risk Committee of the Board oversees the risks arising from our use of artificial intelligence and receives a quarterly report from the Chief Risk Officer.</quote>
<quote id="2">As a founding member of the Frontier Model Forum and a signatory of the EU AI Pact, we share what we learn with peers.</quote>
</quotes>
<match_id>Example_Bank__2.2__3</match_id>
</input>
{
  "match_id": "Example_Bank__2.2__3",
  "classifications": [
    {"practice": "Named accountability for AI risk", "subtypes": ["Board of directors oversight"], "quotes": [1], "reasoning": "A committee of the board holds ongoing oversight of the risks from the company's AI use."}
  ],
  "named": [
    {"name": "Frontier Model Forum", "relation": "member", "quotes": [2]},
    {"name": "EU AI Pact", "relation": "signed", "quotes": [2]}
  ]
}

<input>
<company>Example Bank</company>
<quotes>
<quote id="1">Every AI model we use is recorded in our model inventory and governed under our model risk management policy.</quote>
<quote id="2">Before a model is used, an independent validation team reviews its design, data and limitations and approves its use.</quote>
</quotes>
<match_id>Example_Bank__2.1__2</match_id>
</input>
{
  "match_id": "Example_Bank__2.1__2",
  "classifications": [
    {"practice": "AI risk management to a recognised standard", "subtypes": ["Model risk management", "AI system inventory"], "quotes": [1], "reasoning": "AI models are inventoried and governed under the bank's model risk management policy."},
    {"practice": "Pre-deployment risk and impact assessment", "subtypes": ["Use-case approval"], "quotes": [2], "reasoning": "An independent team validates each model and approves its use before deployment."}
  ],
  "named": []
}

<input>
<company>Example Bank</company>
<quotes>
<quote id="1">We plan to add watermarks to AI-generated images next year.</quote>
<quote id="2">We are committed to fair and ethical AI, and our people remain accountable for every decision.</quote>
</quotes>
<match_id>Example_Bank__1.8__1</match_id>
</input>
{
  "match_id": "Example_Bank__1.8__1",
  "classifications": [],
  "named": []
}
</examples>

<!-- USER -->
<input>
<company>$company</company>
<quotes>
$quotes
</quotes>
<match_id>$match_id</match_id>
</input>
