import {
  Badge,
  NavLink,
  ScrollArea,
  Stack,
  Text,
  useMantineTheme,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
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
  const theme = useMantineTheme();
  const rail = !useMediaQuery(`(min-width: ${theme.breakpoints.lg})`, false, {
    getInitialValueInEffect: false,
  });
  const index = useMemo(() => indexRisks(risks), [risks]);
  const codable = codableRisks(risks);
  const codedCount = codable.filter((risk) => isCoded(risk.responses)).length;

  return (
    <Stack gap="sm" h="100%" data-tour="risk-list">
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
                rail={rail}
                active={entry.id === activeId}
                dirty={dirtyIds.has(entry.id)}
                onClick={() => {
                  onSelect(entry.id);
                }}
              />
            ) : (
              <GroupingRow
                key={entry.id}
                entry={entry}
                indent={indent}
                rail={rail}
              />
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
  rail: boolean;
  active: boolean;
  dirty: boolean;
  onClick: () => void;
}

function CodableRow({
  entry,
  indent,
  rail,
  active,
  dirty,
  onClick,
}: CodableRowProps) {
  const notARisk = isNotARisk(entry.responses);
  const coded = isCoded(entry.responses);
  const marker = (
    <Badge
      size="sm"
      variant={dirty ? "filled" : "light"}
      color={dirty ? "orange" : coded && !notARisk ? "green" : "gray"}
      w={MARKER_WIDTH}
      title={markerHint(dirty, coded, notARisk)}
    >
      {notARisk ? "NR" : coded ? "✓" : "—"}
    </Badge>
  );
  const readableId = (
    <Text size="xs" c="dimmed" truncate="start" ta="left">
      {entry.readableId}
    </Text>
  );
  return (
    <NavLink
      data-risk-id={entry.id}
      active={active}
      onClick={onClick}
      pl={indentStyle(indent)}
      title={rail ? entry.name : undefined}
      label={
        rail ? (
          <Stack gap={2}>
            {marker}
            {readableId}
          </Stack>
        ) : (
          <Text size="sm" lineClamp={2}>
            {entry.name}
          </Text>
        )
      }
      description={rail ? undefined : readableId}
      leftSection={rail ? undefined : marker}
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

interface GroupingRowProps {
  entry: RiskEntry;
  indent: number;
  rail: boolean;
}

function GroupingRow({ entry, indent, rail }: GroupingRowProps) {
  const rejected = entry.origin === REJECTED_ORIGIN;
  const struck = rejected ? "line-through" : undefined;
  return (
    <Stack
      gap={0}
      py={8}
      pl={indentStyle(indent)}
      pr="xs"
      opacity={rejected ? 0.6 : 1}
      title={rail ? entry.name : undefined}
    >
      {rail ? null : (
        <Text size="sm" fw={600} lineClamp={2} td={struck}>
          {entry.name}
        </Text>
      )}
      <Text
        size="xs"
        c="dimmed"
        truncate="start"
        ta="left"
        td={rail ? struck : undefined}
      >
        {entry.readableId}
      </Text>
    </Stack>
  );
}
