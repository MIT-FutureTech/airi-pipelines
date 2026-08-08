import type { RiskEntry } from "@api/_classification";
import { Badge, NavLink, ScrollArea, Stack, Text } from "@mantine/core";
import { useMemo } from "react";
import { codableRisks, isNotARisk, isRiskCoded } from "@/lib/coding";
import { REJECTED_ORIGIN } from "@/lib/fields";
import { depthOf, indexRisks } from "@/lib/tree";

interface Props {
  risks: RiskEntry[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

export function RiskSidebar({ risks, activeId, onSelect }: Props) {
  const index = useMemo(() => indexRisks(risks), [risks]);
  const codable = codableRisks(risks);
  const codedCount = codable.filter((risk) =>
    isRiskCoded(risk.responses),
  ).length;

  return (
    <Stack gap="sm" h="100%">
      <Text size="sm" c="dimmed">
        {codedCount} / {codable.length} coded
      </Text>
      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        <Stack gap={0}>
          {risks.map((entry) => (
            <SidebarRow
              key={entry.id}
              entry={entry}
              depth={depthOf(index, entry)}
              active={entry.id === activeId}
              onClick={() => {
                onSelect(entry.id);
              }}
            />
          ))}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}

interface RowProps {
  entry: RiskEntry;
  depth: number;
  active: boolean;
  onClick: () => void;
}

function SidebarRow({ entry, depth, active, onClick }: RowProps) {
  const rejected = entry.origin === REJECTED_ORIGIN;
  return (
    <NavLink
      data-risk-id={entry.id}
      active={active}
      onClick={onClick}
      pl={`calc(var(--mantine-spacing-xs) + ${depth * 14}px)`}
      opacity={rejected ? 0.45 : 1}
      label={
        <Text size="sm" fw={entry.codable ? 400 : 600} lineClamp={2}>
          {entry.name}
        </Text>
      }
      description={entry.readableId}
      leftSection={<StatusBadge entry={entry} rejected={rejected} />}
    />
  );
}

function StatusBadge({
  entry,
  rejected,
}: {
  entry: RiskEntry;
  rejected: boolean;
}) {
  if (rejected) {
    return (
      <Badge size="sm" variant="light" color="red" w="2.5rem">
        ✕
      </Badge>
    );
  }
  if (!entry.codable) {
    return (
      <Badge size="sm" variant="transparent" color="gray" w="2.5rem">
        ⌄
      </Badge>
    );
  }
  const notARisk = isNotARisk(entry.responses);
  const coded = isRiskCoded(entry.responses);
  return (
    <Badge
      size="sm"
      variant="light"
      color={notARisk ? "gray" : coded ? "green" : "gray"}
      w="2.5rem"
    >
      {notARisk ? "NR" : coded ? "✓" : "—"}
    </Badge>
  );
}
