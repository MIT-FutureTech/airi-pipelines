import { Group, Radio, Stack, Textarea } from "@mantine/core";
import { DECISIONS, type Judgement } from "@shared/judgements";
import { DECISION_LABELS, parseDecision } from "@/lib/judgements";

interface DecisionControlsProps {
  companyName: string;
  judgement: Judgement;
  onChange: (judgement: Judgement) => void;
}

export function DecisionControls({
  companyName,
  judgement,
  onChange,
}: DecisionControlsProps) {
  return (
    <Stack gap="sm">
      <Radio.Group
        label={`Does ${companyName} disclose a mitigation of this kind?`}
        value={judgement.decision}
        onChange={(value) =>
          onChange({ ...judgement, decision: parseDecision(value) })
        }
      >
        <Group mt="xs">
          {DECISIONS.map((decision) => (
            <Radio
              key={decision}
              value={decision}
              label={DECISION_LABELS[decision]}
            />
          ))}
        </Group>
      </Radio.Group>
      <Textarea
        label="Comment"
        autosize
        minRows={2}
        maxRows={6}
        value={judgement.comment}
        onChange={(event) =>
          onChange({ ...judgement, comment: event.currentTarget.value })
        }
      />
    </Stack>
  );
}
