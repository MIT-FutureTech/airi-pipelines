import {
  Anchor,
  AppShell,
  CloseButton,
  Group,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import type { CellSelection } from "@/lib/cells";
import { formatDate } from "@/lib/dates";
import { type DocumentGroup, groupByDocument } from "@/lib/grouping";
import { STRENGTH_COLORS, STRENGTH_LABELS } from "@/lib/strength";
import type { CompanyDocument, LocatedEvidence } from "@/lib/types";

interface EvidencePanelProps {
  selection: CellSelection;
  documents: Map<string, CompanyDocument>;
  onClose: () => void;
}

export function EvidencePanel({
  selection,
  documents,
  onClose,
}: EvidencePanelProps) {
  const { company, code, evidence } = selection;
  return (
    <>
      <AppShell.Section>
        <Stack>
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <div>
              <Title order={3}>{company.name}</Title>
              <Text fw={600}>{`${code.code} ${code.name}`}</Text>
            </div>
            <CloseButton aria-label="Close evidence" onClick={onClose} />
          </Group>
          <Text>{code.definition}</Text>
          <Text fw={600}>
            {evidence.length === 1 ? "1 quote" : `${evidence.length} quotes`}
          </Text>
        </Stack>
      </AppShell.Section>
      <AppShell.Section grow component={ScrollArea} mt="md">
        <Stack gap="lg">
          {groupByDocument(evidence).map((group) => (
            <DocumentQuotes
              key={group.documentId}
              group={group}
              documents={documents}
            />
          ))}
        </Stack>
      </AppShell.Section>
    </>
  );
}

interface DocumentQuotesProps {
  group: DocumentGroup;
  documents: Map<string, CompanyDocument>;
}

function DocumentQuotes({ group, documents }: DocumentQuotesProps) {
  const source = documents.get(group.documentId);
  if (source === undefined) {
    throw new Error(`Evidence refers to unknown document ${group.documentId}`);
  }
  return (
    <Stack gap="xs">
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
      </Text>
      {group.evidence.map((item) => (
        <QuoteCard
          key={`${item.excerpt_id} ${item.mitigation} ${item.quote}`}
          item={item}
        />
      ))}
    </Stack>
  );
}

function QuoteCard({ item }: { item: LocatedEvidence }) {
  return (
    <Paper withBorder p="sm">
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Text fw={600}>{item.mitigation}</Text>
          <Text
            px="xs"
            style={{ ...STRENGTH_COLORS[item.strength], borderRadius: 4 }}
          >
            {STRENGTH_LABELS[item.strength]}
          </Text>
        </Group>
        <Text>{`“${item.quote}”`}</Text>
      </Stack>
    </Paper>
  );
}
