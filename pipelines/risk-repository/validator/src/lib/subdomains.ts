export interface SubdomainOption {
  value: string;
  label: string;
}

export interface SubdomainGroup {
  domain: string;
  items: SubdomainOption[];
}

export const SUBDOMAIN_GROUPS: SubdomainGroup[] = [
  {
    domain: "1. Discrimination & toxicity",
    items: [
      {
        value: "1.1",
        label: "1.1 Unfair discrimination and misrepresentation",
      },
      { value: "1.2", label: "1.2 Exposure to toxic content" },
      { value: "1.3", label: "1.3 Unequal performance across groups" },
    ],
  },
  {
    domain: "2. Privacy & security",
    items: [
      { value: "2.1", label: "2.1 Compromise of privacy" },
      { value: "2.2", label: "2.2 AI system security vulnerabilities" },
    ],
  },
  {
    domain: "3. Misinformation",
    items: [
      { value: "3.1", label: "3.1 False or misleading information" },
      { value: "3.2", label: "3.2 Pollution of information ecosystem" },
    ],
  },
  {
    domain: "4. Malicious actors & misuse",
    items: [
      {
        value: "4.1",
        label: "4.1 Disinformation, surveillance, and influence at scale",
      },
      { value: "4.2", label: "4.2 Cyberattacks, weapons, and mass harm" },
      { value: "4.3", label: "4.3 Fraud, scams, and targeted manipulation" },
    ],
  },
  {
    domain: "5. Human-computer interaction",
    items: [
      { value: "5.1", label: "5.1 Overreliance and unsafe use" },
      { value: "5.2", label: "5.2 Loss of human agency and autonomy" },
    ],
  },
  {
    domain: "6. Socioeconomic & environmental harms",
    items: [
      {
        value: "6.1",
        label: "6.1 Power centralization and unfair distribution",
      },
      { value: "6.2", label: "6.2 Increased inequality, worse employment" },
      { value: "6.3", label: "6.3 Devaluation of human effort" },
      { value: "6.4", label: "6.4 Competitive dynamics" },
      { value: "6.5", label: "6.5 Governance failure" },
      { value: "6.6", label: "6.6 Environmental harm" },
    ],
  },
  {
    domain: "7. AI system safety, failures & limitations",
    items: [
      { value: "7.1", label: "7.1 AI pursuing its own goals" },
      { value: "7.2", label: "7.2 AI possessing dangerous capabilities" },
      { value: "7.3", label: "7.3 Lack of capability or robustness" },
      { value: "7.4", label: "7.4 Lack of transparency or interpretability" },
      { value: "7.5", label: "7.5 AI welfare and rights" },
      { value: "7.6", label: "7.6 Multi-agent risks" },
    ],
  },
  {
    domain: "Unclassified",
    items: [{ value: "X.1", label: "X.1 Unclassified / not a concrete risk" }],
  },
];
