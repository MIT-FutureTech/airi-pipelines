import {
  Anchor,
  Badge,
  Code,
  Divider,
  Group,
  Stack,
  Text,
  Title,
  TypographyStylesProvider,
} from "@mantine/core";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { OUTCOME_COLORS, OUTCOME_LABELS } from "@/lib/outcomes";
import type { AuditDocument, Decision } from "@/lib/types";

const DECISION_COLORS: Record<Decision, string> = {
  include: "green",
  exclude: "gray",
  uncertain: "yellow",
};

interface Props {
  document: AuditDocument;
}

export function DocumentDetail({ document }: Props) {
  const outcome = document.screening.outcome_class;
  return (
    <Stack gap="md">
      <Stack gap={4}>
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Title order={2}>{document.title ?? document.readable_id}</Title>
          <Badge color={OUTCOME_COLORS[outcome]} variant="light" size="lg">
            {OUTCOME_LABELS[outcome]}
          </Badge>
        </Group>
        {document.title !== null && (
          <Text c="dimmed" size="sm">
            {document.readable_id}
          </Text>
        )}
        {document.url !== null && (
          <Anchor
            href={document.url}
            target="_blank"
            rel="noreferrer"
            size="sm"
          >
            {document.url}
          </Anchor>
        )}
      </Stack>

      <DecisionSummary document={document} />

      {document.abstract !== null && (
        <Section title="Abstract">
          <Markdown content={document.abstract} />
        </Section>
      )}

      {document.screening.abstract_result !== null && (
        <Section
          title="Abstract screening"
          trailing={
            <DecisionBadge
              decision={document.screening.abstract_result.decision}
            />
          }
        >
          <Markdown
            content={document.screening.abstract_result.criteria_breakdown}
          />
        </Section>
      )}

      {document.screening.full_text_result !== null && (
        <Section
          title="Full-text screening"
          trailing={
            <DecisionBadge
              decision={document.screening.full_text_result.decision}
            />
          }
        >
          <Markdown
            content={document.screening.full_text_result.criteria_breakdown}
          />
        </Section>
      )}

      {document.pdf_path !== null && (
        <>
          <Divider />
          <Text size="sm" c="dimmed">
            Local PDF: <Code>{document.pdf_path}</Code>
          </Text>
        </>
      )}
    </Stack>
  );
}

function DecisionSummary({ document }: Props) {
  return (
    <Group gap="xl">
      <DecisionRow
        label="Ground truth"
        decision={document.screening.ground_truth_decision}
      />
      <DecisionRow
        label="Abstract"
        decision={document.screening.abstract_result?.decision ?? null}
      />
      <DecisionRow
        label="Full-text"
        decision={document.screening.full_text_result?.decision ?? null}
      />
    </Group>
  );
}

interface DecisionRowProps {
  label: string;
  decision: Decision | null;
}

function DecisionRow({ label, decision }: DecisionRowProps) {
  return (
    <Group gap="xs">
      <Text size="sm" c="dimmed">
        {label}:
      </Text>
      {decision === null ? (
        <Text size="sm" c="dimmed">
          —
        </Text>
      ) : (
        <DecisionBadge decision={decision} />
      )}
    </Group>
  );
}

function DecisionBadge({ decision }: { decision: Decision }) {
  return (
    <Badge color={DECISION_COLORS[decision]} variant="light">
      {decision}
    </Badge>
  );
}

interface SectionProps {
  title: string;
  trailing?: React.ReactNode;
  children: React.ReactNode;
}

function Section({ title, trailing, children }: SectionProps) {
  return (
    <div>
      <Divider mb="sm" />
      <Group gap="sm" mb="xs">
        <Title order={4}>{title}</Title>
        {trailing}
      </Group>
      {children}
    </div>
  );
}

function Markdown({ content }: { content: string }) {
  return (
    <TypographyStylesProvider>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </TypographyStylesProvider>
  );
}
