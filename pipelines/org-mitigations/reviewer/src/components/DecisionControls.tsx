import { Group, Radio } from "@mantine/core";
import {
  type Decision,
  DISCLOSURE_LABELS,
  DISCLOSURES,
  parseDisclosure,
} from "@/lib/decisions";

interface DecisionControlsProps {
  companyName: string;
  decision: Decision;
  onChange: (decision: Decision) => void;
}

export function DecisionControls({
  companyName,
  decision,
  onChange,
}: DecisionControlsProps) {
  return (
    <Radio.Group
      label={`Does ${companyName} disclose a mitigation of this kind?`}
      value={decision.disclosure}
      onChange={(value) =>
        onChange({ ...decision, disclosure: parseDisclosure(value) })
      }
    >
      <Group mt="xs">
        {DISCLOSURES.map((disclosure) => (
          <Radio
            key={disclosure}
            value={disclosure}
            label={DISCLOSURE_LABELS[disclosure]}
          />
        ))}
      </Group>
    </Radio.Group>
  );
}
