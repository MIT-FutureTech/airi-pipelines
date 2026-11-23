import {
  Anchor,
  AppShell,
  Checkbox,
  CloseButton,
  Group,
  Mark,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import type { Judgement } from "@shared/judgements";
import { DecisionControls } from "@/components/DecisionControls";
import { type CellSelection, cellQuotes } from "@/lib/cells";
import { fullLabel } from "@/lib/codes";
import { formatDate } from "@/lib/dates";
import { highlightWindow } from "@/lib/highlight";
import {
  STRENGTH_COLORS,
  STRENGTH_LABELS,
  sortByStrength,
  sortByStrongestQuote,
} from "@/lib/strength";
import type {
  CompanyDocument,
  Excerpt,
  Mitigation,
  Quote,
  Span,
} from "@/lib/types";

const CONTEXT_CHARACTERS = 300;
const CONTEXT_BORDER = {
  borderLeft: "3px solid var(--mantine-color-default-border)",
};
const QUOTE_BORDER = {
  borderTop: "1px solid var(--mantine-color-default-border)",
};
const FOOTER_BORDER = {
  borderTop: "1px solid var(--mantine-color-default-border)",
};

interface EvidencePanelProps {
  selection: CellSelection;
  quotes: Map<string, Quote[]>;
  documents: Map<string, CompanyDocument>;
  excerpts: Map<string, Excerpt>;
  judgement: Judgement;
  onJudgementChange: (judgement: Judgement) => void;
  onClose: () => void;
}

export function EvidencePanel({
  selection,
  quotes,
  documents,
  excerpts,
  judgement,
  onJudgementChange,
  onClose,
}: EvidencePanelProps) {
  const { company, code, mitigations } = selection;
  const quoteCount = cellQuotes(mitigations, quotes).length;
  const supporting = judgement.supportingMitigationRecordIds;
  const toggleSupporting = (recordId: string) => {
    onJudgementChange({
      ...judgement,
      supportingMitigationRecordIds: supporting.includes(recordId)
        ? supporting.filter((supportingId) => supportingId !== recordId)
        : [...supporting, recordId],
    });
  };
  return (
    <>
      <AppShell.Section>
        <Stack>
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <div>
              <Title order={3}>{company.name}</Title>
              <Text fw={600}>{fullLabel(code)}</Text>
            </div>
            <CloseButton aria-label="Close evidence" onClick={onClose} />
          </Group>
          <Text>{code.definition}</Text>
          <Text fw={600}>
            {`${formatMitigationCount(mitigations.length)}, ${formatQuoteCount(quoteCount)}`}
          </Text>
        </Stack>
      </AppShell.Section>
      <AppShell.Section grow component={ScrollArea} mt="md">
        <Stack gap="md">
          {sortByStrongestQuote(mitigations, quotes).map((mitigation) => (
            <MitigationCard
              key={mitigation.record_id}
              mitigation={mitigation}
              quotes={cellQuotes([mitigation], quotes)}
              documents={documents}
              excerpts={excerpts}
              isSupporting={supporting.includes(mitigation.record_id)}
              onToggleSupporting={() => toggleSupporting(mitigation.record_id)}
            />
          ))}
        </Stack>
      </AppShell.Section>
      <AppShell.Section mt="md" pt="md" style={FOOTER_BORDER}>
        <DecisionControls
          companyName={company.name}
          judgement={judgement}
          onChange={onJudgementChange}
        />
      </AppShell.Section>
    </>
  );
}

interface MitigationCardProps {
  mitigation: Mitigation;
  quotes: Quote[];
  documents: Map<string, CompanyDocument>;
  excerpts: Map<string, Excerpt>;
  isSupporting: boolean;
  onToggleSupporting: () => void;
}

function MitigationCard({
  mitigation,
  quotes,
  documents,
  excerpts,
  isSupporting,
  onToggleSupporting,
}: MitigationCardProps) {
  return (
    <Paper withBorder p="sm">
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Text fw={600}>{mitigation.name}</Text>
          <Checkbox
            label="Supports the decision"
            checked={isSupporting}
            onChange={onToggleSupporting}
          />
        </Group>
        {sortByStrength(quotes).map((quote) => (
          <QuoteBlock
            key={quote.evidence_id}
            quote={quote}
            documents={documents}
            excerpts={excerpts}
          />
        ))}
      </Stack>
    </Paper>
  );
}

interface QuoteBlockProps {
  quote: Quote;
  documents: Map<string, CompanyDocument>;
  excerpts: Map<string, Excerpt>;
}

function QuoteBlock({ quote, documents, excerpts }: QuoteBlockProps) {
  const [isExpanded, { toggle }] = useDisclosure(false);
  const source = documents.get(quote.document_id);
  if (source === undefined) {
    throw new Error(`Quote refers to unknown document ${quote.document_id}`);
  }
  const excerpt = excerpts.get(quote.excerpt_id);
  if (excerpt === undefined) {
    throw new Error(`Quote refers to unknown excerpt ${quote.excerpt_id}`);
  }
  return (
    <Stack gap="xs" pt="sm" style={QUOTE_BORDER}>
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <Text>
          <Anchor
            href={source.link}
            target="_blank"
            rel="noopener noreferrer"
            inherit
          >
            {source.title}
          </Anchor>
          {`, ${source.doc_type}, ${formatDate(source.date, source.date_precision)}`}
        </Text>
        <Text
          px="xs"
          style={{ ...STRENGTH_COLORS[quote.strength], borderRadius: 4 }}
        >
          {STRENGTH_LABELS[quote.strength]}
        </Text>
      </Group>
      <Text>{`“${quote.quote}”`}</Text>
      <Anchor component="button" type="button" ta="left" onClick={toggle}>
        {isExpanded ? "Hide context" : "Show context"}
      </Anchor>
      {isExpanded && (
        <ExcerptContext excerpt={excerpt} location={quote.location} />
      )}
    </Stack>
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

function formatMitigationCount(count: number): string {
  return count === 1 ? "1 mitigation" : `${count} mitigations`;
}

function formatQuoteCount(count: number): string {
  return count === 1 ? "1 quote" : `${count} quotes`;
}
