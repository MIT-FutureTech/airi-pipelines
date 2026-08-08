import type { PaperEntry, ReviewMode } from "@api/_classification";
import {
  Badge,
  Button,
  Container,
  Group,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { use, useMemo, useState } from "react";
import { getPapers } from "@/lib/api";
import { navigate } from "@/lib/route";
import {
  loadPaperPickerPrefs,
  type PaperPickerPrefs,
  savePaperPickerPrefs,
} from "@/lib/storage";

interface Props {
  reviewer: string;
}

const UNASSIGNED = "Unassigned";

const PAPER_STATUSES = [
  "Awaiting extraction",
  "Classifying",
  "Not started",
  "In progress",
  "Complete",
] as const;
type PaperStatus = (typeof PAPER_STATUSES)[number];

const STATUS_COLORS: Record<PaperStatus, string> = {
  "Awaiting extraction": "gray",
  Classifying: "yellow",
  "Not started": "gray",
  "In progress": "blue",
  Complete: "green",
};

export function PaperPicker({ reviewer }: Props) {
  const { papers } = use(getPapers(reviewer));
  const [prefs, setPrefs] = useState<PaperPickerPrefs>(loadPaperPickerPrefs);

  const assignees = useMemo(() => assigneeOptions(papers), [papers]);

  const update = (changes: Partial<PaperPickerPrefs>) => {
    const next = { ...prefs, ...changes };
    setPrefs(next);
    savePaperPickerPrefs(next);
  };

  const { mode } = prefs;
  const assignee =
    prefs.assignee !== null && assignees.includes(prefs.assignee)
      ? prefs.assignee
      : null;
  const status =
    prefs.status !== null &&
    (PAPER_STATUSES as readonly string[]).includes(prefs.status)
      ? prefs.status
      : null;

  const visible = papers.filter(
    (paper) =>
      (assignee === null || assigneeOf(paper) === assignee) &&
      (status === null || paperStatus(paper) === status),
  );
  const groups = groupByAssignee(visible);

  return (
    <Container size="md" pt="xl" pb="xl">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start">
          <Stack gap={2}>
            <Title order={2}>Classification review</Title>
            <Text size="sm" c="dimmed">
              Reviewing as {reviewer}
            </Text>
          </Stack>
          <Button
            variant="default"
            size="xs"
            onClick={() => navigate({ name: "tasks" })}
          >
            Back
          </Button>
        </Group>

        <Stack gap={4}>
          <Text size="sm" fw={500}>
            Mode
          </Text>
          <SegmentedControl
            value={mode}
            onChange={(value) => update({ mode: value as ReviewMode })}
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

        <Group grow align="flex-end">
          <Select
            label="Assignee"
            placeholder="All assignees"
            data={assignees}
            value={assignee}
            onChange={(value) => update({ assignee: value })}
            clearable
          />
          <Select
            label="Status"
            placeholder="All statuses"
            data={[...PAPER_STATUSES]}
            value={status}
            onChange={(value) => update({ status: value })}
            clearable
          />
        </Group>

        {visible.length === 0 ? (
          <Text c="dimmed">
            {papers.length === 0
              ? "No papers found."
              : "No papers match these filters."}
          </Text>
        ) : (
          groups.map(([groupName, assigned]) => (
            <Stack key={groupName} gap="xs">
              <Text size="sm" fw={600} c="dimmed" tt="uppercase">
                {groupName}
              </Text>
              {assigned.map((paper) => (
                <PaperRow
                  key={paper.quickRef}
                  paper={paper}
                  onOpen={() => {
                    navigate({
                      name: "classification",
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
      w="100%"
      style={{
        border: "1px solid var(--mantine-color-default-border)",
        borderRadius: "var(--mantine-radius-sm)",
        padding: "var(--mantine-spacing-sm)",
        cursor: openable ? "pointer" : "not-allowed",
        opacity: openable ? 1 : 0.6,
      }}
    >
      <Stack gap={4}>
        <Group justify="space-between" wrap="nowrap" gap="sm">
          <Text fw={500}>{paper.quickRef}</Text>
          <Group gap="xs" wrap="nowrap">
            {paper.progress !== null ? (
              <Badge variant="outline" color="gray">
                {paper.progress}
              </Badge>
            ) : null}
            <StatusBadge paper={paper} />
          </Group>
        </Group>
        <Text size="sm" lineClamp={2}>
          {paper.title ?? "Untitled"}
        </Text>
      </Stack>
    </UnstyledButton>
  );
}

function StatusBadge({ paper }: { paper: PaperEntry }) {
  const status = paperStatus(paper);
  const label =
    paper.state === "ready"
      ? `${paper.reviewerCodedCount} / ${paper.codableCount} coded`
      : status.toLowerCase();
  return (
    <Badge color={STATUS_COLORS[status]} variant="light">
      {label}
    </Badge>
  );
}

function paperStatus(paper: PaperEntry): PaperStatus {
  if (paper.state === "awaiting-extraction") {
    return "Awaiting extraction";
  }
  if (paper.state === "classifying") {
    return "Classifying";
  }
  if (paper.reviewerCodedCount === 0) {
    return "Not started";
  }
  return paper.reviewerCodedCount === paper.codableCount
    ? "Complete"
    : "In progress";
}

function assigneeOf(paper: PaperEntry): string {
  return paper.assignee ?? UNASSIGNED;
}

function assigneeOptions(papers: PaperEntry[]): string[] {
  const names = [...new Set(papers.map(assigneeOf))];
  return names.sort(compareAssignees);
}

function compareAssignees(a: string, b: string): number {
  if (a === UNASSIGNED) {
    return 1;
  }
  if (b === UNASSIGNED) {
    return -1;
  }
  return a.localeCompare(b);
}

function groupByAssignee(papers: PaperEntry[]): [string, PaperEntry[]][] {
  const groups = new Map<string, PaperEntry[]>();
  for (const paper of papers) {
    const key = assigneeOf(paper);
    const list = groups.get(key);
    if (list === undefined) {
      groups.set(key, [paper]);
    } else {
      list.push(paper);
    }
  }
  return [...groups.entries()].sort(([a], [b]) => compareAssignees(a, b));
}
