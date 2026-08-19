import { Group, Paper, Stack, Text } from "@mantine/core";
import { AXIS_FIELDS, type ReviewResponse } from "@shared/classification";
import { useMemo } from "react";
import { HighlightedText } from "@/components/HighlightedText";
import { FIELD_LABELS, valueLabel } from "@/lib/fields";
import type { HighlightGroup } from "@/lib/highlight";
import { groupReasoning, type ReasoningGroup } from "@/lib/reasoning";

interface Props {
  responses: ReviewResponse[];
  highlightGroups: HighlightGroup[];
}

export function PipelineCard({ responses, highlightGroups }: Props) {
  const groups = useMemo(() => groupReasoning(responses), [responses]);
  const byField = useMemo(
    () => new Map(responses.map((response) => [response.field, response])),
    [responses],
  );

  return (
    <Paper withBorder radius="md" p="md" data-tour="pipeline-card">
      <Stack gap="md">
        <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
          Pipeline classification
        </Text>
        <Stack gap={2}>
          {AXIS_FIELDS.map((field) => {
            const response = byField.get(field);
            if (response === undefined) {
              return null;
            }
            return (
              <Group key={field} gap="sm" wrap="nowrap" align="baseline">
                <Text size="sm" c="dimmed" miw="6rem" style={{ flexShrink: 0 }}>
                  {FIELD_LABELS[field]}
                </Text>
                <Text size="sm" fw={500}>
                  {valueLabel(field, response.value)}
                </Text>
              </Group>
            );
          })}
        </Stack>
        {groups.map((group) => (
          <Stack key={group.comment} gap={2}>
            <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
              {reasoningLabel(group, groups.length)}
            </Text>
            <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
              <HighlightedText text={group.comment} groups={highlightGroups} />
            </Text>
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
}

function reasoningLabel(group: ReasoningGroup, total: number): string {
  if (total === 1) {
    return "Reasoning";
  }
  const fields = group.fields
    .map((field) => FIELD_LABELS[field].toLowerCase())
    .join(", ");
  return `Reasoning for ${fields}`;
}
