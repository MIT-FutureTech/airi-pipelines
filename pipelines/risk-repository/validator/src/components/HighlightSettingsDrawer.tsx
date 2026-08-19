import {
  ActionIcon,
  Button,
  ColorSwatch,
  Drawer,
  Group,
  Menu,
  Stack,
  Switch,
  Text,
  Textarea,
  Tooltip,
} from "@mantine/core";
import { IconHighlight, IconPlus, IconTrash } from "@tabler/icons-react";
import {
  HIGHLIGHT_PALETTE,
  type HighlightGroup,
  MAX_HIGHLIGHT_GROUPS,
} from "@/lib/highlight";

export function HighlightToggle({ onClick }: { onClick: () => void }) {
  return (
    <Tooltip label="Highlight keywords">
      <ActionIcon
        variant="subtle"
        aria-label="Highlight keywords"
        onClick={onClick}
      >
        <IconHighlight size={20} />
      </ActionIcon>
    </Tooltip>
  );
}

interface Props {
  opened: boolean;
  onClose: () => void;
  description: string;
  groups: HighlightGroup[];
  onChange: (groups: HighlightGroup[]) => void;
}

export function HighlightSettingsDrawer({
  opened,
  onClose,
  description,
  groups,
  onChange,
}: Props) {
  const updateGroup = (id: string, patch: Partial<HighlightGroup>) => {
    onChange(groups.map((g) => (g.id === id ? { ...g, ...patch } : g)));
  };

  const removeGroup = (id: string) => {
    onChange(groups.filter((g) => g.id !== id));
  };

  const addGroup = () => {
    if (groups.length >= MAX_HIGHLIGHT_GROUPS) {
      return;
    }
    const usedColors = new Set(groups.map((g) => g.color));
    const nextColor =
      HIGHLIGHT_PALETTE.find((c) => !usedColors.has(c)) ?? HIGHLIGHT_PALETTE[0];
    onChange([
      ...groups,
      {
        id: crypto.randomUUID(),
        color: nextColor,
        keywords: "",
        caseSensitive: false,
        wholeWord: false,
      },
    ]);
  };

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="left"
      size={320}
      title="Highlight Keywords"
      withOverlay={false}
      trapFocus={false}
      lockScroll={false}
      closeOnClickOutside={false}
      closeOnEscape={false}
    >
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          {description} Enter one keyword per line.
        </Text>
        {groups.map((g) => (
          <GroupRow
            key={g.id}
            group={g}
            onUpdate={(patch) => updateGroup(g.id, patch)}
            onRemove={() => removeGroup(g.id)}
          />
        ))}
        <Group>
          <Button
            onClick={addGroup}
            leftSection={<IconPlus size={16} />}
            disabled={groups.length >= MAX_HIGHLIGHT_GROUPS}
            variant="light"
            size="xs"
          >
            Add group
          </Button>
        </Group>
      </Stack>
    </Drawer>
  );
}

interface RowProps {
  group: HighlightGroup;
  onUpdate: (patch: Partial<HighlightGroup>) => void;
  onRemove: () => void;
}

function GroupRow({ group, onUpdate, onRemove }: RowProps) {
  return (
    <Stack
      gap="xs"
      p="xs"
      style={{
        border: "1px solid var(--mantine-color-gray-3)",
        borderRadius: "var(--mantine-radius-sm)",
      }}
    >
      <Group justify="space-between" align="center">
        <ColorPicker
          color={group.color}
          onChange={(color) => {
            onUpdate({ color });
          }}
        />
        <ActionIcon
          variant="subtle"
          color="red"
          onClick={onRemove}
          aria-label="Remove group"
        >
          <IconTrash size={16} />
        </ActionIcon>
      </Group>
      <Textarea
        placeholder="One keyword per line"
        value={group.keywords}
        onChange={(event) => {
          onUpdate({ keywords: event.currentTarget.value });
        }}
        autosize
        minRows={2}
        maxRows={8}
      />
      <Group gap="md">
        <Switch
          label="Match case"
          size="xs"
          checked={group.caseSensitive}
          onChange={(event) => {
            onUpdate({ caseSensitive: event.currentTarget.checked });
          }}
        />
        <Switch
          label="Whole word"
          size="xs"
          checked={group.wholeWord}
          onChange={(event) => {
            onUpdate({ wholeWord: event.currentTarget.checked });
          }}
        />
      </Group>
    </Stack>
  );
}

interface ColorPickerProps {
  color: string;
  onChange: (color: string) => void;
}

function ColorPicker({ color, onChange }: ColorPickerProps) {
  return (
    <Menu position="bottom-start" withinPortal>
      <Menu.Target>
        <ActionIcon variant="subtle" aria-label="Pick color">
          <ColorSwatch
            color={`var(--mantine-color-${color}-3)`}
            size={20}
            withShadow={false}
          />
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        <Group gap={6} p="xs" maw={220}>
          {HIGHLIGHT_PALETTE.map((c) => (
            <ColorSwatch
              key={c}
              color={`var(--mantine-color-${c}-3)`}
              size={20}
              withShadow={false}
              onClick={() => {
                onChange(c);
              }}
              style={{
                cursor: "pointer",
                outline:
                  c === color
                    ? "2px solid var(--mantine-color-blue-6)"
                    : "none",
                outlineOffset: 2,
              }}
            />
          ))}
        </Group>
      </Menu.Dropdown>
    </Menu>
  );
}
