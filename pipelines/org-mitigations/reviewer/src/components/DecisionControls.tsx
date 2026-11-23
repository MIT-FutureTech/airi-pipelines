import { Group, Radio, Stack, Textarea } from "@mantine/core";
import { getHotkeyHandler } from "@mantine/hooks";
import { DECISIONS, type Judgement } from "@shared/judgements";
import { type RefObject, useRef } from "react";
import { DECISION_LABELS, parseDecision } from "@/lib/judgements";

interface DecisionControlsProps {
  companyName: string;
  judgement: Judgement;
  commentRef: RefObject<HTMLTextAreaElement | null>;
  onChange: (judgement: Judgement) => void;
  onSave: (judgement: Judgement) => void;
}

export function DecisionControls({
  companyName,
  judgement,
  commentRef,
  onChange,
  onSave,
}: DecisionControlsProps) {
  const commentWhenFocused = useRef(judgement.comment);
  return (
    <Stack gap="sm">
      <Radio.Group
        label={`Does ${companyName} disclose a mitigation of this kind?`}
        value={judgement.decision}
        onChange={(value) =>
          onSave({ ...judgement, decision: parseDecision(value) })
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
        ref={commentRef}
        label="Comment"
        autosize
        minRows={2}
        maxRows={6}
        value={judgement.comment}
        onChange={(event) =>
          onChange({ ...judgement, comment: event.currentTarget.value })
        }
        onKeyDown={getHotkeyHandler([
          ["Escape", () => commentRef.current?.blur()],
        ])}
        onFocus={() => {
          commentWhenFocused.current = judgement.comment;
        }}
        onBlur={() => {
          if (judgement.comment !== commentWhenFocused.current) {
            onSave(judgement);
          }
        }}
      />
    </Stack>
  );
}
