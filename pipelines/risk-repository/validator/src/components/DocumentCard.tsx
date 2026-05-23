import type { Decision, ManifestEntry } from "@api/_shared";
import {
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { Suspense, use, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { getDocument, submitDecision } from "@/lib/api";
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
  onSubmitted,
}: Props) {
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
      <ErrorBoundary fallbackRender={renderError} resetKeys={[entry.id]}>
        <Suspense fallback={<Loader />}>
          <CardBody
            reviewer={reviewer}
            entry={entry}
            onSubmitted={onSubmitted}
          />
        </Suspense>
      </ErrorBoundary>
    </Stack>
  );
}

interface BodyProps {
  reviewer: string;
  entry: ManifestEntry;
  onSubmitted: Props["onSubmitted"];
}

function CardBody({ reviewer, entry, onSubmitted }: BodyProps) {
  const document = use(getDocument(entry.id));
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
    <Stack gap="md" style={{ flex: 1, minHeight: 0 }}>
      <Title order={2}>{document.title ?? document.readableId}</Title>
      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        {document.abstract === null ? (
          <Text c="dimmed" fs="italic">
            No abstract on file.
          </Text>
        ) : (
          <Text style={{ whiteSpace: "pre-wrap" }}>{document.abstract}</Text>
        )}
      </ScrollArea>
      <Stack gap="xs">
        <Group gap="xs">
          {DECISION_OPTIONS.map((opt) => (
            <Button
              key={opt.decision}
              variant={decision === opt.decision ? "filled" : "light"}
              color={DECISION_COLORS[opt.decision]}
              onClick={() => {
                setDecision(opt.decision);
              }}
              disabled={submitting}
            >
              {opt.label} ({opt.key})
            </Button>
          ))}
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
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Alert color="red" title="Failed to load document">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
