import { Group, Kbd, Stack, Table, Text, Tooltip } from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import {
  IconArrowLeft,
  IconArrowRight,
  IconKeyboard,
} from "@tabler/icons-react";
import { type ReactNode, useState } from "react";

const ARROW_SIZE = 14;

const KEY_ICONS: Record<string, ReactNode> = {
  ArrowRight: <IconArrowRight size={ARROW_SIZE} />,
  ArrowLeft: <IconArrowLeft size={ARROW_SIZE} />,
};

const SHORTCUTS: { keys: string[]; action: string }[] = [
  { keys: ["Y", "N", "U"], action: "Decide yes, no or unsure" },
  { keys: ["ArrowRight", "J"], action: "Next cell" },
  { keys: ["ArrowLeft", "K"], action: "Previous cell" },
  { keys: ["1–9"], action: "Tick or untick a mitigation" },
  { keys: ["C"], action: "Write a comment" },
  { keys: ["Esc"], action: "Leave the comment, or close the cell" },
  { keys: ["?"], action: "Show or hide these shortcuts" },
];

export function ShortcutsHelp() {
  const [isPinned, setIsPinned] = useState(false);
  useHotkeys([["shift+?", () => setIsPinned((current) => !current)]]);
  return (
    <Tooltip
      label={<ShortcutList />}
      opened={isPinned || undefined}
      position="bottom-start"
    >
      <IconKeyboard
        aria-label="Keyboard shortcuts"
        size={24}
        style={{ display: "block" }}
      />
    </Tooltip>
  );
}

function ShortcutList() {
  return (
    <Stack gap="xs" p={4}>
      <Text fw={600} inherit>
        Keyboard shortcuts
      </Text>
      <Table withRowBorders={false} verticalSpacing={2} horizontalSpacing="xs">
        <Table.Tbody>
          {SHORTCUTS.map(({ keys, action }) => (
            <Table.Tr key={action}>
              <Table.Td>
                <Group gap={4} wrap="nowrap">
                  {keys.map((key) => (
                    <Kbd key={key} aria-label={key}>
                      {KEY_ICONS[key] ?? key}
                    </Kbd>
                  ))}
                </Group>
              </Table.Td>
              <Table.Td>
                <Text inherit>{action}</Text>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}
