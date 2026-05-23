import type { Decision, ManifestEntry } from "@api/_shared";
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
import { DECISION_COLORS } from "@/lib/theme";

const DECISION_LABELS: Record<Decision, string> = {
  include: "Inc",
  exclude: "Exc",
  uncertain: "Unc",
};

interface Props {
  manifest: ManifestEntry[];
  activeId: string | null;
  onSelect: (id: string) => void;
  search: string;
  onSearchChange: (value: string) => void;
}

export function Sidebar({
  manifest,
  activeId,
  onSelect,
  search,
  onSearchChange,
}: Props) {
  const decidedCount = useMemo(
    () => manifest.filter((m) => m.decision !== null).length,
    [manifest],
  );

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (q === "") {
      return manifest;
    }
    return manifest.filter((m) => {
      if (m.readableId.toLowerCase().includes(q)) {
        return true;
      }
      if (m.title?.toLowerCase().includes(q)) {
        return true;
      }
      return false;
    });
  }, [manifest, search]);

  return (
    <Stack gap="sm" h="100%">
      <Text size="sm" c="dimmed">
        {decidedCount} / {manifest.length} decided
      </Text>
      <TextInput
        size="sm"
        placeholder="Search title or ID"
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
            No documents match.
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
  entry: ManifestEntry;
  active: boolean;
  onClick: () => void;
}

function SidebarRow({ entry, active, onClick }: RowProps) {
  return (
    <NavLink
      data-doc-id={entry.id}
      active={active}
      onClick={onClick}
      label={entry.title ?? entry.readableId}
      description={entry.title !== null ? entry.readableId : undefined}
      leftSection={
        <Badge
          size="sm"
          variant="light"
          color={entry.decision ? DECISION_COLORS[entry.decision] : "gray"}
          w="3rem"
        >
          {entry.decision ? DECISION_LABELS[entry.decision] : "—"}
        </Badge>
      }
    />
  );
}
