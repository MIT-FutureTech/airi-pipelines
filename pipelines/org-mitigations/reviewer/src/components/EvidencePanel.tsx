import { CloseButton, Group, Stack, Text, Title } from "@mantine/core";
import type { CellSelection } from "@/lib/cells";

interface EvidencePanelProps {
  selection: CellSelection;
  onClose: () => void;
}

export function EvidencePanel({ selection, onClose }: EvidencePanelProps) {
  const { company, code } = selection;
  return (
    <Stack>
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <div>
          <Title order={3}>{company.name}</Title>
          <Text fw={600}>{`${code.code} ${code.name}`}</Text>
        </div>
        <CloseButton aria-label="Close evidence" onClick={onClose} />
      </Group>
      <Text>{code.definition}</Text>
    </Stack>
  );
}
