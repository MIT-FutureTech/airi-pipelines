import {
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
import {
  STRENGTH_COLORS,
  STRENGTH_LABELS,
  sortByStrength,
} from "@/lib/strength";
import type { LocatedEvidence } from "@/lib/types";

interface EvidencePanelProps {
  selection: CellSelection;
  onClose: () => void;
}

export function EvidencePanel({ selection, onClose }: EvidencePanelProps) {
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
        <Stack>
          {sortByStrength(evidence).map((item) => (
            <QuoteCard
              key={`${item.excerpt_id} ${item.mitigation} ${item.quote}`}
              item={item}
            />
          ))}
        </Stack>
      </AppShell.Section>
    </>
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
