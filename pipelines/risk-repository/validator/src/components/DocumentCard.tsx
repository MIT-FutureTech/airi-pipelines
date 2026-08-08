import {
  Alert,
  Badge,
  Button,
  Group,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import type { Decision, ManifestEntry } from "@shared/screening";
import { Fragment, useMemo, useState } from "react";
import { submitDecision } from "@/lib/api";
import { type HighlightGroup, highlightText } from "@/lib/highlight";
import { DECISION_COLORS } from "@/lib/theme";

const DECISION_OPTIONS: { decision: Decision; key: string; label: string }[] = [
  { decision: "include", key: "1", label: "Include" },
  { decision: "exclude", key: "2", label: "Exclude" },
  { decision: "uncertain", key: "3", label: "Uncertain" },
];

interface Props {
  reviewer: string;
  entry: ManifestEntry;
  position: number;
  total: number;
  highlightGroups: HighlightGroup[];
  onSubmitted: (
    documentId: string,
    decision: Decision,
    comments: string | null,
    decisionId: string,
  ) => void;
}

export function DocumentCard({
  reviewer,
  entry,
  position,
  total,
  highlightGroups,
  onSubmitted,
}: Props) {
  const [decision, setDecision] = useState<Decision | null>(entry.decision);
  const [comments, setComments] = useState<string>(entry.comments ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (decision === null || submitting) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitDecision({
        reviewer,
        documentId: entry.id,
        decisionId: entry.decisionId,
        decision,
        comments: comments.trim() === "" ? null : comments,
      });
      onSubmitted(
        entry.id,
        response.decision,
        response.comments,
        response.decisionId,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  useHotkeys([
    ["1", () => setDecision("include")],
    ["2", () => setDecision("exclude")],
    ["3", () => setDecision("uncertain")],
    ["i", () => setDecision("include")],
    ["e", () => setDecision("exclude")],
    ["u", () => setDecision("uncertain")],
    ["Enter", submit],
  ]);

  return (
    <Stack gap="md" h="100%">
      <Group justify="space-between" align="center">
        <Text size="sm" c="dimmed">
          {position} / {total} · {entry.readableId}
        </Text>
        {entry.decision !== null && (
          <Badge color={DECISION_COLORS[entry.decision]} variant="light">
            previously {entry.decision}
          </Badge>
        )}
      </Group>
      <Stack gap="md" style={{ flex: 1, minHeight: 0 }}>
        <Title order={2}>
          <HighlightedText
            text={entry.title ?? entry.readableId}
            groups={highlightGroups}
          />
        </Title>
        <ScrollArea style={{ flex: 1, minHeight: 0 }}>
          {entry.abstract === null ? (
            <Text c="dimmed" fs="italic">
              No abstract on file.
            </Text>
          ) : (
            <Text style={{ whiteSpace: "pre-wrap" }}>
              <HighlightedText text={entry.abstract} groups={highlightGroups} />
            </Text>
          )}
        </ScrollArea>
        <Stack gap="xs">
          <Group gap="xs">
            {DECISION_OPTIONS.map((opt) => {
              const style: Record<string, string> = {};
              if (decision === opt.decision && decision === "exclude") {
                style.color = "#000000";
              }
              return (
                <Button
                  key={opt.decision}
                  variant={decision === opt.decision ? "filled" : "light"}
                  color={DECISION_COLORS[opt.decision]}
                  style={style}
                  onClick={() => {
                    setDecision(opt.decision);
                  }}
                  disabled={submitting}
                >
                  {opt.label} ({opt.key})
                </Button>
              );
            })}
            <Button
              ml="auto"
              onClick={submit}
              loading={submitting}
              disabled={decision === null}
            >
              Submit (Enter)
            </Button>
          </Group>
          <Textarea
            placeholder="Comments (optional)"
            value={comments}
            onChange={(event) => {
              setComments(event.currentTarget.value);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
            autosize
            minRows={2}
            maxRows={5}
            disabled={submitting}
          />
          {error !== null && (
            <Alert color="red" title="Submission failed">
              {error}
            </Alert>
          )}
        </Stack>
      </Stack>
    </Stack>
  );
}

interface HighlightedTextProps {
  text: string;
  groups: HighlightGroup[];
}

function HighlightedText({ text, groups }: HighlightedTextProps) {
  const chunks = useMemo(() => highlightText(text, groups), [text, groups]);
  return (
    <>
      {chunks.map((chunk, idx) => {
        const key = `${idx}-${chunk.text}`;
        if (chunk.color === null) {
          return <Fragment key={key}>{chunk.text}</Fragment>;
        }
        return (
          <mark
            key={key}
            style={{
              backgroundColor: `var(--mantine-color-${chunk.color}-3)`,
              color: "#000",
              padding: 0,
              borderRadius: 2,
            }}
          >
            {chunk.text}
          </mark>
        );
      })}
    </>
  );
}
