import {
  Alert,
  Anchor,
  Button,
  Center,
  Container,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { Suspense, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { PaperPicker } from "@/components/PaperPicker";
import type { TaskSelection } from "@/lib/task";

interface Props {
  reviewer: string;
  onSelect: (selection: TaskSelection) => void;
  onChangeName: () => void;
}

export function TaskLauncher({ reviewer, onSelect, onChangeName }: Props) {
  const [configuring, setConfiguring] = useState(false);

  if (configuring) {
    return (
      <ErrorBoundary
        fallbackRender={(props) => (
          <SetupError {...props} onBack={() => setConfiguring(false)} />
        )}
      >
        <Suspense
          fallback={
            <Center h="100vh">
              <Loader />
            </Center>
          }
        >
          <PaperPicker
            reviewer={reviewer}
            onStart={onSelect}
            onBack={() => setConfiguring(false)}
          />
        </Suspense>
      </ErrorBoundary>
    );
  }

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
          <Button onClick={() => onSelect({ task: "screening" })}>
            Abstract screening
          </Button>
          <Button onClick={() => setConfiguring(true)}>
            Classification review
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}

function SetupError({ error, onBack }: FallbackProps & { onBack: () => void }) {
  return (
    <Container size="xs" pt="xl">
      <Stack gap="md">
        <Alert color="red" title="Failed to load papers">
          {error instanceof Error ? error.message : String(error)}
        </Alert>
        <Button variant="default" onClick={onBack}>
          Back
        </Button>
      </Stack>
    </Container>
  );
}
