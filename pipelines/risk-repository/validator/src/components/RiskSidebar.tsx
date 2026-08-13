import { Badge, NavLink, ScrollArea, Stack, Text } from "@mantine/core";
import { REJECTED_ORIGIN, type RiskEntry } from "@shared/classification";
import { isCoded, isNotARisk } from "@shared/coding";
import { useMemo } from "react";
import { codableRisks } from "@/lib/risks";
import { depthOf, indexRisks } from "@/lib/tree";

interface Props {
  risks: RiskEntry[];
  activeId: string | null;
  dirtyIds: ReadonlySet<string>;
  onSelect: (id: string) => void;
}

const MARKER_WIDTH = "2.5rem";

export function RiskSidebar({ risks, activeId, dirtyIds, onSelect }: Props) {
  const index = useMemo(() => indexRisks(risks), [risks]);
  const codable = codableRisks(risks);
  const codedCount = codable.filter((risk) => isCoded(risk.responses)).length;

  return (
    <Stack gap="sm" h="100%">
      <Text size="sm" c="dimmed">
        {codedCount} / {codable.length} coded
      </Text>
      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        <Stack gap={0}>
          {risks.map((entry) => {
            const indent = depthOf(index, entry) * 14;
            return entry.codable ? (
              <CodableRow
                key={entry.id}
                entry={entry}
                indent={indent}
                active={entry.id === activeId}
                dirty={dirtyIds.has(entry.id)}
                onClick={() => {
                  onSelect(entry.id);
                }}
              />
            ) : (
              <GroupingRow key={entry.id} entry={entry} indent={indent} />
            );
          })}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}

function indentStyle(indent: number): string {
  return `calc(var(--mantine-spacing-xs) + ${indent}px)`;
}

interface CodableRowProps {
  entry: RiskEntry;
  indent: number;
  active: boolean;
  dirty: boolean;
  onClick: () => void;
}

function CodableRow({
  entry,
  indent,
  active,
  dirty,
  onClick,
}: CodableRowProps) {
  const notARisk = isNotARisk(entry.responses);
  const coded = isCoded(entry.responses);
  return (
    <NavLink
      data-risk-id={entry.id}
      active={active}
      onClick={onClick}
      pl={indentStyle(indent)}
      label={
        <Text size="sm" lineClamp={2}>
          {entry.name}
        </Text>
      }
      description={entry.readableId}
      leftSection={
        <Badge
          size="sm"
          variant={dirty ? "filled" : "light"}
          color={dirty ? "orange" : coded && !notARisk ? "green" : "gray"}
          w={MARKER_WIDTH}
          title={markerHint(dirty, coded, notARisk)}
        >
          {notARisk ? "NR" : coded ? "✓" : "—"}
        </Badge>
      }
    />
  );
}

function markerHint(dirty: boolean, coded: boolean, notARisk: boolean): string {
  if (dirty) {
    return "Unsaved changes";
  }
  if (notARisk) {
    return "Marked not a risk";
  }
  return coded ? "Coded" : "Not coded yet";
}

function GroupingRow({ entry, indent }: { entry: RiskEntry; indent: number }) {
  const rejected = entry.origin === REJECTED_ORIGIN;
  return (
    <Stack
      gap={0}
      py={8}
      pl={indentStyle(indent)}
      pr="xs"
      opacity={rejected ? 0.6 : 1}
    >
      <Text
        size="sm"
        fw={600}
        lineClamp={2}
        td={rejected ? "line-through" : undefined}
      >
        {entry.name}
      </Text>
      <Text size="xs" c="dimmed">
        {entry.readableId}
      </Text>
    </Stack>
  );
}
