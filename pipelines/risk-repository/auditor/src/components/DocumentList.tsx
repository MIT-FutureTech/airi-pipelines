import {
  Badge,
  Chip,
  Group,
  NavLink,
  ScrollArea,
  Stack,
  Text,
} from "@mantine/core";
import { useMemo, useState } from "react";
import {
  countOutcomes,
  OUTCOME_COLORS,
  OUTCOME_LABELS,
  OUTCOME_ORDER,
} from "@/lib/outcomes";
import type { AuditBundle, AuditDocument, OutcomeClass } from "@/lib/types";

interface Props {
  bundle: AuditBundle;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function DocumentList({ bundle, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState<OutcomeClass[]>([...OUTCOME_ORDER]);

  const counts = useMemo(
    () => countOutcomes(bundle.documents.map((d) => d.screening.outcome_class)),
    [bundle.documents],
  );

  const visible = useMemo(() => {
    const allowed = new Set(filter);
    return bundle.documents.filter((d) =>
      allowed.has(d.screening.outcome_class),
    );
  }, [bundle.documents, filter]);

  return (
    <Stack gap="sm" h="100%">
      <Chip.Group
        multiple
        value={filter}
        onChange={(value) => {
          setFilter(value as OutcomeClass[]);
        }}
      >
        <Group gap={6}>
          {OUTCOME_ORDER.map((outcome) => (
            <Chip
              key={outcome}
              value={outcome}
              color={OUTCOME_COLORS[outcome]}
              size="xs"
            >
              {OUTCOME_LABELS[outcome]} ({counts[outcome]})
            </Chip>
          ))}
        </Group>
      </Chip.Group>
      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        {visible.length === 0 ? (
          <Text c="dimmed" size="sm">
            No documents match the current filter.
          </Text>
        ) : (
          <Stack gap={0}>
            {visible.map((doc) => (
              <DocumentItem
                key={doc.readable_id}
                document={doc}
                active={doc.readable_id === selectedId}
                onClick={() => {
                  onSelect(doc.readable_id);
                }}
              />
            ))}
          </Stack>
        )}
      </ScrollArea>
    </Stack>
  );
}

interface ItemProps {
  document: AuditDocument;
  active: boolean;
  onClick: () => void;
}

function DocumentItem({ document, active, onClick }: ItemProps) {
  const outcome = document.screening.outcome_class;
  return (
    <NavLink
      active={active}
      onClick={onClick}
      label={document.title ?? document.readable_id}
      description={document.title !== null ? document.readable_id : undefined}
      leftSection={
        <Badge color={OUTCOME_COLORS[outcome]} size="sm" variant="light">
          {OUTCOME_LABELS[outcome]}
        </Badge>
      }
    />
  );
}
