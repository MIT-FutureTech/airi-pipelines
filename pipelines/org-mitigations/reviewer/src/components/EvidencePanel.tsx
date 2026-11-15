import {
  AccordionChevron,
  ActionIcon,
  Anchor,
  AppShell,
  Checkbox,
  CloseButton,
  Collapse,
  Group,
  Mark,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { DecisionControls } from "@/components/DecisionControls";
import { type CellSelection, quoteKey } from "@/lib/cells";
import { formatDate } from "@/lib/dates";
import type { Decision } from "@/lib/decisions";
import { type DocumentGroup, groupByDocument } from "@/lib/grouping";
import { highlightWindow } from "@/lib/highlight";
import { STRENGTH_COLORS, STRENGTH_LABELS } from "@/lib/strength";
import type {
  CompanyDocument,
  Excerpt,
  LocatedEvidence,
  Span,
} from "@/lib/types";

const CONTEXT_CHARACTERS = 300;
const CONTEXT_BORDER = {
  borderLeft: "3px solid var(--mantine-color-default-border)",
};
const FOOTER_BORDER = {
  borderTop: "1px solid var(--mantine-color-default-border)",
};

interface EvidencePanelProps {
  selection: CellSelection;
  documents: Map<string, CompanyDocument>;
  excerpts: Map<string, Excerpt>;
  decision: Decision;
  onDecisionChange: (decision: Decision) => void;
  onClose: () => void;
}

export function EvidencePanel({
  selection,
  documents,
  excerpts,
  decision,
  onDecisionChange,
  onClose,
}: EvidencePanelProps) {
  const { company, domain, evidence } = selection;
  const toggleSupporting = (key: string) => {
    const supportingQuotes = new Set(decision.supportingQuotes);
    if (supportingQuotes.has(key)) {
      supportingQuotes.delete(key);
    } else {
      supportingQuotes.add(key);
    }
    onDecisionChange({ ...decision, supportingQuotes });
  };
  return (
    <>
      <AppShell.Section>
        <Stack>
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <div>
              <Title order={3}>{company.name}</Title>
              <Text fw={600}>{`${domain.code} ${domain.name}`}</Text>
            </div>
            <CloseButton aria-label="Close evidence" onClick={onClose} />
          </Group>
          <Text>{domain.definition}</Text>
          <Text fw={600}>{formatQuoteCount(evidence.length)}</Text>
        </Stack>
      </AppShell.Section>
      <AppShell.Section grow component={ScrollArea} mt="md">
        <Stack gap="lg">
          {groupByDocument(evidence).map((group) => (
            <DocumentQuotes
              key={group.documentId}
              group={group}
              documents={documents}
              excerpts={excerpts}
              supportingQuotes={decision.supportingQuotes}
              onToggleSupporting={toggleSupporting}
            />
          ))}
        </Stack>
      </AppShell.Section>
      <AppShell.Section mt="md" pt="md" style={FOOTER_BORDER}>
        <DecisionControls
          companyName={company.name}
          decision={decision}
          onChange={onDecisionChange}
        />
      </AppShell.Section>
    </>
  );
}

interface DocumentQuotesProps {
  group: DocumentGroup;
  documents: Map<string, CompanyDocument>;
  excerpts: Map<string, Excerpt>;
  supportingQuotes: ReadonlySet<string>;
  onToggleSupporting: (key: string) => void;
}

function DocumentQuotes({
  group,
  documents,
  excerpts,
  supportingQuotes,
  onToggleSupporting,
}: DocumentQuotesProps) {
  const [isOpen, { toggle }] = useDisclosure(true);
  const source = documents.get(group.documentId);
  if (source === undefined) {
    throw new Error(`Evidence refers to unknown document ${group.documentId}`);
  }
  return (
    <Stack gap="xs">
      <Group gap="xs" wrap="nowrap" align="flex-start">
        <ActionIcon
          variant="subtle"
          color="gray"
          aria-expanded={isOpen}
          aria-label={isOpen ? "Hide quotes" : "Show quotes"}
          onClick={toggle}
        >
          <AccordionChevron
            style={{
              transform: isOpen ? undefined : "rotate(-90deg)",
              transition: "transform 150ms",
            }}
          />
        </ActionIcon>
        <Text fw={600}>
          <Anchor
            href={source.link}
            target="_blank"
            rel="noopener noreferrer"
            inherit
          >
            {source.title}
          </Anchor>
          {`, ${source.doc_type}, ${formatDate(source.date, source.date_precision)}`}
          {` · ${formatQuoteCount(group.evidence.length)}`}
        </Text>
      </Group>
      <Collapse in={isOpen}>
        <Stack gap="xs">
          {group.evidence.map((item) => (
            <QuoteCard
              key={quoteKey(item)}
              item={item}
              excerpts={excerpts}
              isSupporting={supportingQuotes.has(quoteKey(item))}
              onToggleSupporting={() => onToggleSupporting(quoteKey(item))}
            />
          ))}
        </Stack>
      </Collapse>
    </Stack>
  );
}

interface QuoteCardProps {
  item: LocatedEvidence;
  excerpts: Map<string, Excerpt>;
  isSupporting: boolean;
  onToggleSupporting: () => void;
}

function QuoteCard({
  item,
  excerpts,
  isSupporting,
  onToggleSupporting,
}: QuoteCardProps) {
  const [isExpanded, { toggle }] = useDisclosure(false);
  const excerpt = excerpts.get(item.excerpt_id);
  if (excerpt === undefined) {
    throw new Error(`Evidence refers to unknown excerpt ${item.excerpt_id}`);
  }
  return (
    <Paper withBorder p="sm">
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Text fw={600}>{item.mitigation_name}</Text>
          <Text
            px="xs"
            style={{ ...STRENGTH_COLORS[item.strength], borderRadius: 4 }}
          >
            {STRENGTH_LABELS[item.strength]}
          </Text>
        </Group>
        <Text>{`“${item.quote}”`}</Text>
        <Group justify="space-between" wrap="nowrap">
          <Anchor component="button" type="button" onClick={toggle}>
            {isExpanded ? "Hide context" : "Show context"}
          </Anchor>
          <Checkbox
            label="Supports the decision"
            checked={isSupporting}
            onChange={onToggleSupporting}
          />
        </Group>
        {isExpanded && (
          <ExcerptContext excerpt={excerpt} location={item.location} />
        )}
      </Stack>
    </Paper>
  );
}

interface ExcerptContextProps {
  excerpt: Excerpt;
  location: Span | null;
}

function ExcerptContext({ excerpt, location }: ExcerptContextProps) {
  const [isWhole, { toggle }] = useDisclosure(false);
  if (location === null) {
    return (
      <Stack gap="xs" pl="sm" style={CONTEXT_BORDER}>
        <Text fs="italic">
          This quote wasn't found word for word in its excerpt, so the whole
          excerpt is shown.
        </Text>
        <Text>{excerpt.text}</Text>
        <PassageIds excerpt={excerpt} />
      </Stack>
    );
  }
  const fitsInWindow =
    location.start <= CONTEXT_CHARACTERS &&
    excerpt.text.length - location.end <= CONTEXT_CHARACTERS;
  const parts = highlightWindow(
    excerpt.text,
    location,
    isWhole ? excerpt.text.length : CONTEXT_CHARACTERS,
  );
  return (
    <Stack gap="xs" pl="sm" style={CONTEXT_BORDER}>
      <Text>
        {parts.before}
        <Mark color="yellow.1">{parts.highlight}</Mark>
        {parts.after}
      </Text>
      {!fitsInWindow && (
        <Anchor component="button" type="button" ta="left" onClick={toggle}>
          {isWhole ? "Show less of the excerpt" : "Show the whole excerpt"}
        </Anchor>
      )}
      <PassageIds excerpt={excerpt} />
    </Stack>
  );
}

function PassageIds({ excerpt }: { excerpt: Excerpt }) {
  const label = excerpt.passage_ids.length === 1 ? "Passage" : "Passages";
  return <Text>{`${label}: ${excerpt.passage_ids.join(", ")}`}</Text>;
}

function formatQuoteCount(count: number): string {
  return count === 1 ? "1 quote" : `${count} quotes`;
}
