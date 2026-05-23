import { Center, Stack, Text, Title } from "@mantine/core";

interface Props {
  total: number;
}

export function DoneScreen({ total }: Props) {
  return (
    <Center h="100%" p="md">
      <Stack gap="sm" align="center">
        <Title order={2}>All done</Title>
        <Text c="dimmed">
          You've recorded a decision for all {total} documents in this set.
        </Text>
        <Text c="dimmed" size="sm">
          You can still revisit any document via the sidebar to revise your
          decision.
        </Text>
      </Stack>
    </Center>
  );
}
