import {
  Anchor,
  Button,
  Container,
  Group,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { navigate } from "@/lib/route";

interface Props {
  reviewer: string;
  onChangeName: () => void;
}

export function TaskLauncher({ reviewer, onChangeName }: Props) {
  return (
    <Container size="xs" pt="xl">
      <Stack gap="md">
        <Title order={2}>Risk Repository Validator</Title>
        <Group gap="xs">
          <Text c="dimmed" size="sm">
            Signed in as {reviewer}.
          </Text>
          <Anchor
            component="button"
            type="button"
            size="sm"
            onClick={onChangeName}
          >
            Change name
          </Anchor>
        </Group>
        <Text fw={500}>Choose a task</Text>
        <Group>
          <Button onClick={() => navigate({ name: "screening" })}>
            Abstract screening
          </Button>
          <Button onClick={() => navigate({ name: "papers" })}>
            Classification review
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}
