import type { PaperEntry, ReviewMode } from "@api/_classification";
import {
  Badge,
  Button,
  Container,
  Group,
  SegmentedControl,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { use, useMemo, useState } from "react";
import { getPapers } from "@/lib/api";
import type { ClassificationSelection } from "@/lib/task";

interface Props {
  reviewer: string;
  onStart: (selection: ClassificationSelection) => void;
  onBack: () => void;
}

const UNASSIGNED = "Unassigned";

export function PaperPicker({ reviewer, onStart, onBack }: Props) {
  const { papers } = use(getPapers(reviewer));
  const [mode, setMode] = useState<ReviewMode>("blind");

  const groups = useMemo(() => groupByAssignee(papers), [papers]);

  return (
    <Container size="sm" pt="xl" pb="xl">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <Stack gap={2}>
            <Title order={2}>Classification review</Title>
            <Text size="sm" c="dimmed">
              Reviewing as {reviewer}
            </Text>
          </Stack>
          <Button variant="default" size="xs" onClick={onBack}>
            Back
          </Button>
        </Group>

        <Stack gap={4}>
          <Text size="sm" fw={500}>
            Mode
          </Text>
          <SegmentedControl
            value={mode}
            onChange={(value) => setMode(value as ReviewMode)}
            data={[
              { value: "blind", label: "Blind" },
              { value: "anchored", label: "Anchored" },
            ]}
          />
          <Text size="xs" c="dimmed">
            {mode === "blind"
              ? "Code each risk without seeing the pipeline's classification."
              : "Start from the pipeline's classification and correct it."}
          </Text>
        </Stack>

        {papers.length === 0 ? (
          <Text c="dimmed">No papers found.</Text>
        ) : (
          groups.map(([assignee, assigned]) => (
            <Stack key={assignee} gap="xs">
              <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                {assignee}
              </Text>
              {assigned.map((paper) => (
                <PaperRow
                  key={paper.quickRef}
                  paper={paper}
                  onOpen={() => {
                    onStart({
                      task: "classification",
                      quickRef: paper.quickRef,
                      mode,
                    });
                  }}
                />
              ))}
            </Stack>
          ))
        )}
      </Stack>
    </Container>
  );
}

interface RowProps {
  paper: PaperEntry;
  onOpen: () => void;
}

function PaperRow({ paper, onOpen }: RowProps) {
  const openable = paper.state !== "awaiting-extraction";
  return (
    <UnstyledButton
      onClick={openable ? onOpen : undefined}
      disabled={!openable}
      style={{
        border: "1px solid var(--mantine-color-default-border)",
        borderRadius: "var(--mantine-radius-sm)",
        padding: "var(--mantine-spacing-sm)",
        cursor: openable ? "pointer" : "not-allowed",
        opacity: openable ? 1 : 0.55,
      }}
    >
      <Group justify="space-between" wrap="nowrap" align="flex-start">
        <Stack gap={2} style={{ minWidth: 0 }}>
          <Text fw={500}>{paper.quickRef}</Text>
          <Text size="sm" c="dimmed" lineClamp={2}>
            {paper.title ?? "Untitled"}
          </Text>
        </Stack>
        <Group gap="xs" wrap="nowrap">
          {paper.progress !== null ? (
            <Badge variant="outline" color="gray">
              {paper.progress}
            </Badge>
          ) : null}
          <StateBadge paper={paper} />
        </Group>
      </Group>
    </UnstyledButton>
  );
}

function StateBadge({ paper }: { paper: PaperEntry }) {
  if (paper.state === "awaiting-extraction") {
    return (
      <Badge color="gray" variant="light">
        awaiting extraction
      </Badge>
    );
  }
  if (paper.state === "classifying") {
    return (
      <Badge color="yellow" variant="light">
        classifying…
      </Badge>
    );
  }
  return (
    <Badge
      color={paper.reviewerCodedCount === paper.codableCount ? "green" : "blue"}
      variant="light"
    >
      {paper.reviewerCodedCount} / {paper.codableCount} coded
    </Badge>
  );
}

function groupByAssignee(papers: PaperEntry[]): [string, PaperEntry[]][] {
  const groups = new Map<string, PaperEntry[]>();
  for (const paper of papers) {
    const key = paper.assignee ?? UNASSIGNED;
    const list = groups.get(key);
    if (list === undefined) {
      groups.set(key, [paper]);
    } else {
      list.push(paper);
    }
  }
  return [...groups.entries()].sort(([a], [b]) => {
    if (a === UNASSIGNED) {
      return 1;
    }
    if (b === UNASSIGNED) {
      return -1;
    }
    return a.localeCompare(b);
  });
}
