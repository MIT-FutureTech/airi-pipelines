import type { RiskEntry } from "@api/_classification";
import {
  Badge,
  NavLink,
  ScrollArea,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import { useMemo } from "react";
import { isNotARisk, isRiskCoded } from "@/lib/coding";

interface Props {
  risks: RiskEntry[];
  activeId: string | null;
  onSelect: (id: string) => void;
  search: string;
  onSearchChange: (value: string) => void;
}

export function RiskSidebar({
  risks,
  activeId,
  onSelect,
  search,
  onSearchChange,
}: Props) {
  const codedCount = useMemo(
    () => risks.filter((risk) => isRiskCoded(risk.responses)).length,
    [risks],
  );

  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (query === "") {
      return risks;
    }
    return risks.filter((risk) => {
      if (risk.readableId.toLowerCase().includes(query)) {
        return true;
      }
      return risk.description.toLowerCase().includes(query);
    });
  }, [risks, search]);

  return (
    <Stack gap="sm" h="100%">
      <Text size="sm" c="dimmed">
        {codedCount} / {risks.length} coded
      </Text>
      <TextInput
        size="sm"
        placeholder="Search ID or description"
        value={search}
        leftSection={<IconSearch size={14} />}
        onChange={(event) => {
          onSearchChange(event.currentTarget.value);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onSearchChange("");
          }
        }}
      />
      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        {visible.length === 0 ? (
          <Text c="dimmed" size="sm">
            No risks match.
          </Text>
        ) : (
          <Stack gap={0}>
            {visible.map((entry) => (
              <SidebarRow
                key={entry.id}
                entry={entry}
                active={entry.id === activeId}
                onClick={() => {
                  onSelect(entry.id);
                }}
              />
            ))}
          </Stack>
        )}
      </ScrollArea>
    </Stack>
  );
}

interface RowProps {
  entry: RiskEntry;
  active: boolean;
  onClick: () => void;
}

function SidebarRow({ entry, active, onClick }: RowProps) {
  const notARisk = isNotARisk(entry.responses);
  const coded = isRiskCoded(entry.responses);
  const badge = notARisk ? "NR" : coded ? "✓" : "—";
  return (
    <NavLink
      data-risk-id={entry.id}
      active={active}
      onClick={onClick}
      label={entry.readableId}
      description={truncate(entry.description, 64)}
      leftSection={
        <Badge
          size="sm"
          variant="light"
          color={coded && !notARisk ? "green" : "gray"}
          w="2.5rem"
        >
          {badge}
        </Badge>
      }
    />
  );
}

function truncate(text: string, max: number): string {
  if (text.length <= max) {
    return text;
  }
  return `${text.slice(0, max)}…`;
}
