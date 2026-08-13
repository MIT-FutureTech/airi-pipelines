import type { RiskManifestResponse } from "@shared/classification";

// Frozen response from /api/risks/manifest for Chen2025, so the tour can drive
// the real classification screen without touching Airtable.
export const DEMO_PAPER: RiskManifestResponse = {
  quickRef: "Chen2025",
  title:
    "A unified ontological and explainable framework for decoding AI risks from news data",
  mode: "anchored",
  risks: [
    {
      id: "recB9GNlpyi2lUvfB",
      readableId: "Chen2025.01",
      name: "Harm attributes",
      parentId: null,
      codable: false,
      origin: "model-added, human-approved",
      description:
        "Harm attributes provide a detailed framework for understanding the diverse types of harm associated with AI incidents, offering a comprehensive perspective on the potential negative impacts of AI technologies.",
      descriptionPage: 5,
      supportingQuote:
        "Harm attributes provide a detailed framework for understanding the diverse types of harm associated with AI incidents, offering a comprehensive perspective on the potential negative impacts of AI technologies.",
      additionalEvidence: [],
      responses: [],
      pipelineResponses: [],
    },
    {
      id: "recrVRVsFbQ8fWxfD",
      readableId: "Chen2025.01.01",
      name: "Psychological Harm",
      parentId: "recB9GNlpyi2lUvfB",
      codable: true,
      origin: "model-added, human-edited",
      description: "",
      descriptionPage: 5,
      supportingQuote:
        "For Psychological Harm, multiple specific attributes are meticulously defined to capture the complexity of such harm.",
      additionalEvidence: [
        {
          index: 0,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                'The attribute "Severity" is categorized into one of five levels, indicating the intensity and acuteness of the harm experienced by individuals. "Reversibility" measures the extent to which the psychological damage can be undone, emphasizing the potential for recovery and healing. In contrast, "Persistence" assesses the duration and enduring nature of the harm, highlighting how long-lasting and possibly permanent the effects can be.',
            },
          ],
        },
        {
          index: 1,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                'The attribute "Characteristics of Vulnerable Groups" identifies individuals who are at a disadvantage in social, economic, or cultural contexts, underscoring the disproportionate impact AI incidents may have on marginalized populations. Additionally, "Influential Attributes of Self-identity and Values" refer to the profound ways in which psychological harm can disrupt and alter people\'s core self-identity and personal values, affecting their sense of self and moral compass.',
            },
          ],
        },
      ],
      responses: [],
      pipelineResponses: [
        {
          id: "rec2HAAopn8dam0Hm",
          field: "intent",
          value: "other",
          mode: "blind",
          comment:
            "The risk focuses on psychological harm experienced by individuals as a result of AI incidents. While the harm is caused by the AI system's actions or outputs, the description does not specify if these incidents stem from malicious human intent or AI-driven behavior, nor does it specify the deployment phase, making 'other' the most accurate classification for all categories.",
        },
        {
          id: "recHCkmLkdlyJF5lw",
          field: "subdomain",
          value: "5.1",
          mode: "blind",
          comment:
            "The risk describes psychological harm, specifically mentioning how AI incidents can disrupt a person's core self-identity, values, and sense of self, which aligns with the concepts of anthropomorphizing or developing emotional dependence and relationships that lead to emotional harm.",
        },
        {
          id: "recgn4fI8Db6DuFBu",
          field: "timing",
          value: "other",
          mode: "blind",
          comment:
            "The risk focuses on psychological harm experienced by individuals as a result of AI incidents. While the harm is caused by the AI system's actions or outputs, the description does not specify if these incidents stem from malicious human intent or AI-driven behavior, nor does it specify the deployment phase, making 'other' the most accurate classification for all categories.",
        },
        {
          id: "recuBYGaIl1y8ZvlS",
          field: "entity",
          value: "other",
          mode: "blind",
          comment:
            "The risk focuses on psychological harm experienced by individuals as a result of AI incidents. While the harm is caused by the AI system's actions or outputs, the description does not specify if these incidents stem from malicious human intent or AI-driven behavior, nor does it specify the deployment phase, making 'other' the most accurate classification for all categories.",
        },
      ],
    },
    {
      id: "recZ4U362bF7qTrhP",
      readableId: "Chen2025.01.02",
      name: "Physical Harm",
      parentId: "recB9GNlpyi2lUvfB",
      codable: true,
      origin: "model-added, human-edited",
      description: "",
      descriptionPage: 5,
      supportingQuote:
        'For Physical Harm, the attribute "Severity" is similarly categorized into one of five levels, ensuring consistency with the assessment of psychological harm.',
      additionalEvidence: [
        {
          index: 0,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                '"Reversibility" measures the extent to which physical harm can be undone, while "Persistence" assesses the duration of the harm. The "Detectability" attribute determines the probability of detecting the physical harm caused by the incident, highlighting the challenges in recognizing and addressing such injuries promptly.',
            },
          ],
        },
      ],
      responses: [],
      pipelineResponses: [
        {
          id: "rec0XsQF2XE4hzTu0",
          field: "intent",
          value: "other",
          mode: "blind",
          comment:
            "The risk describes physical harm resulting from AI incidents. Since the harm occurs during the usage of the system, it is post-deployment. The cause and intent are not specified in the excerpt, as it focuses on the attributes of the harm (severity, reversibility) rather than the causal agent or motivation.",
        },
        {
          id: "recP6oWhvKBCeebPS",
          field: "subdomain",
          value: "7.3",
          mode: "blind",
          comment:
            "The risk describes physical harm resulting from AI incidents, focusing on severity, reversibility, and persistence. Within the provided taxonomy, physical harm from unintended failures or lack of robustness in critical situations is best captured by the category for systems that fail to perform reliably or safely under varying conditions.",
        },
        {
          id: "recdtXoO94OfcsJQs",
          field: "timing",
          value: "post-deployment",
          mode: "blind",
          comment:
            "The risk describes physical harm resulting from AI incidents. Since the harm occurs during the usage of the system, it is post-deployment. The cause and intent are not specified in the excerpt, as it focuses on the attributes of the harm (severity, reversibility) rather than the causal agent or motivation.",
        },
        {
          id: "recvoNfcJRlTpDL7y",
          field: "entity",
          value: "other",
          mode: "blind",
          comment:
            "The risk describes physical harm resulting from AI incidents. Since the harm occurs during the usage of the system, it is post-deployment. The cause and intent are not specified in the excerpt, as it focuses on the attributes of the harm (severity, reversibility) rather than the causal agent or motivation.",
        },
      ],
    },
    {
      id: "rec5u7RfVcK2HyTRE",
      readableId: "Chen2025.01.03",
      name: "Economic Loss",
      parentId: "recB9GNlpyi2lUvfB",
      codable: true,
      origin: "model-added, human-edited",
      description: "",
      descriptionPage: 5,
      supportingQuote:
        'Economic Loss attributes include "Severity" which is categorized into one of five levels to indicate the financial impact, and "Persistence" which assesses how long the economic loss lasts.',
      additionalEvidence: [
        {
          index: 0,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                "These attributes help quantify the economic ramifications of AI incidents, providing insight into the financial burdens that may arise.",
            },
          ],
        },
      ],
      responses: [],
      pipelineResponses: [
        {
          id: "recEUF21Iz04loMMt",
          field: "entity",
          value: "other",
          mode: "blind",
          comment:
            "Economic loss is a general outcome of AI incidents that can be caused by either human actors (e.g., mismanagement, malicious use) or the AI system itself (e.g., algorithmic errors, market disruption). It can result from intentional attacks or unintentional malfunctions and can manifest at any stage of the lifecycle.",
        },
        {
          id: "recOPH7ZmUluywojN",
          field: "timing",
          value: "other",
          mode: "blind",
          comment:
            "Economic loss is a general outcome of AI incidents that can be caused by either human actors (e.g., mismanagement, malicious use) or the AI system itself (e.g., algorithmic errors, market disruption). It can result from intentional attacks or unintentional malfunctions and can manifest at any stage of the lifecycle.",
        },
        {
          id: "receNTeLQK8aQLlOX",
          field: "intent",
          value: "other",
          mode: "blind",
          comment:
            "Economic loss is a general outcome of AI incidents that can be caused by either human actors (e.g., mismanagement, malicious use) or the AI system itself (e.g., algorithmic errors, market disruption). It can result from intentional attacks or unintentional malfunctions and can manifest at any stage of the lifecycle.",
        },
        {
          id: "recjpxkGTrVcoyNW8",
          field: "subdomain",
          value: "6.2",
          mode: "blind",
          comment:
            "The risk specifically describes the financial impact and economic burdens arising from AI incidents, which aligns with the socioeconomic impacts of AI, specifically increased inequality and decline in economic standing for affected parties.",
        },
      ],
    },
    {
      id: "recKCxdxmNE08eLei",
      readableId: "Chen2025.01.04",
      name: "Human Rights Violations",
      parentId: "recB9GNlpyi2lUvfB",
      codable: false,
      origin: "model-added, human-approved",
      description:
        "human rights violations are categorized as privacy violations and equal rights violations.",
      descriptionPage: 11,
      supportingQuote:
        "human rights violations are categorized as privacy violations and equal rights violations.",
      additionalEvidence: [],
      responses: [],
      pipelineResponses: [],
    },
    {
      id: "rec8OVVyB83dUfBbg",
      readableId: "Chen2025.01.04.01",
      name: "Privacy Violations",
      parentId: "recKCxdxmNE08eLei",
      codable: true,
      origin: "model-added, human-edited",
      description: "",
      descriptionPage: 5,
      supportingQuote:
        'For Privacy Violation, the attribute "Severity" is again categorized into one of five levels, reflecting the intensity of the privacy breach.',
      additionalEvidence: [
        {
          index: 0,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                '"Sensitivity" measures the degree of privacy sensitivity according to EU standards, indicating the potential impact on personal data and privacy. This highlights the critical importance of safeguarding personal information in the digital age.',
            },
          ],
        },
      ],
      responses: [],
      pipelineResponses: [
        {
          id: "rec2zUFvgFD31qX5K",
          field: "entity",
          value: "other",
          mode: "blind",
          comment:
            "Privacy violations typically occur due to how an AI system processes data or is utilized by humans (entity), often as an unintended byproduct of data collection or model inference (intent) once the system is active in the world (timing), though it could also stem from intentional misuse.",
        },
        {
          id: "recJMaWfIqrbEjKP1",
          field: "intent",
          value: "other",
          mode: "blind",
          comment:
            "Privacy violations typically occur due to how an AI system processes data or is utilized by humans (entity), often as an unintended byproduct of data collection or model inference (intent) once the system is active in the world (timing), though it could also stem from intentional misuse.",
        },
        {
          id: "recPDIIEXss7VgBV6",
          field: "subdomain",
          value: "2.1",
          mode: "blind",
          comment:
            "The risk specifically describes privacy violations, breaches of sensitive personal data, and the importance of safeguarding personal information, which directly aligns with the domain of obtaining or leaking sensitive information.",
        },
        {
          id: "reckUDK2UDI4uYJEh",
          field: "timing",
          value: "post-deployment",
          mode: "blind",
          comment:
            "Privacy violations typically occur due to how an AI system processes data or is utilized by humans (entity), often as an unintended byproduct of data collection or model inference (intent) once the system is active in the world (timing), though it could also stem from intentional misuse.",
        },
      ],
    },
    {
      id: "rec7KcI2KCIvQQHH1",
      readableId: "Chen2025.01.04.02",
      name: "Equal Rights Violations",
      parentId: "recKCxdxmNE08eLei",
      codable: true,
      origin: "model-added, human-edited",
      description: "",
      descriptionPage: 5,
      supportingQuote:
        'In the context of Equal Rights Violation, "Severity" is categorized into one of five levels to indicate the impact on equal rights.',
      additionalEvidence: [
        {
          index: 0,
          fields: [
            {
              key: "page",
              value: "5",
            },
            {
              key: "quote",
              value:
                'The "Characteristics of Vulnerable Groups" attribute considers whether the violations are specifically targeted at vulnerable groups, emphasizing the necessity of recognizing and addressing the unique challenges faced by these populations. Such consideration helps ensure that AI technologies do not exacerbate existing inequalities or create new forms of discrimination.',
            },
          ],
        },
      ],
      responses: [],
      pipelineResponses: [
        {
          id: "recCSnqam7LAe63WI",
          field: "timing",
          value: "post-deployment",
          mode: "blind",
          comment:
            "The risk describes discrimination and equal rights violations resulting from the use of AI technologies. This is typically an unintentional outcome caused by the AI system's logic or training data biases during its active use phase.",
        },
        {
          id: "recFBXUBB61TAsAU2",
          field: "intent",
          value: "unintentional",
          mode: "blind",
          comment:
            "The risk describes discrimination and equal rights violations resulting from the use of AI technologies. This is typically an unintentional outcome caused by the AI system's logic or training data biases during its active use phase.",
        },
        {
          id: "recPbDRgNif4CbrzP",
          field: "entity",
          value: "ai",
          mode: "blind",
          comment:
            "The risk describes discrimination and equal rights violations resulting from the use of AI technologies. This is typically an unintentional outcome caused by the AI system's logic or training data biases during its active use phase.",
        },
        {
          id: "recTIRDVceAcf0jDd",
          field: "subdomain",
          value: "1.1",
          mode: "blind",
          comment:
            "The risk description specifically focuses on ensuring AI does not exacerbate existing inequalities or create new forms of discrimination, particularly against vulnerable groups, which directly aligns with unfair discrimination and misrepresentation.",
        },
      ],
    },
  ],
};
