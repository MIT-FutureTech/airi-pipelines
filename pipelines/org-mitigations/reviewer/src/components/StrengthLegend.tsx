import { Box, Group, Stack, Text } from "@mantine/core";
import { STRENGTH_COLORS, STRENGTHS } from "@/lib/strength";
import type { Strength } from "@/lib/types";

const LABELS: Record<Strength, string> = {
  described: "Described",
  stated: "Stated",
  reference: "Reference",
};

const DEFINITIONS: Record<Strength, string> = {
  described: "says what the company does and how, where or by whom",
  stated: "says the company does it, with little or no detail",
  reference: "names it or refers back to it without saying what it does",
};

export function StrengthLegend() {
  return (
    <Stack gap={4}>
      <Text fw={600}>Shading shows the strongest quote in each cell</Text>
      {STRENGTHS.map((strength) => (
        <Group key={strength} gap="xs" wrap="nowrap">
          <Box
            w={16}
            h={16}
            style={{
              backgroundColor: STRENGTH_COLORS[strength].backgroundColor,
              borderRadius: 4,
              flexShrink: 0,
            }}
          />
          <Text>
            <Text span fw={600}>
              {LABELS[strength]}
            </Text>{" "}
            {DEFINITIONS[strength]}
          </Text>
        </Group>
      ))}
    </Stack>
  );
}
