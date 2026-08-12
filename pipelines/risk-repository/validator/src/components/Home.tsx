import {
  Button,
  Container,
  Group,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useState } from "react";
import { navigate, type Route } from "@/lib/route";

interface Props {
  reviewer: string | null;
  resuming: boolean;
  onSubmit: (name: string) => void;
}

export function Home({ reviewer, resuming, onSubmit }: Props) {
  const [name, setName] = useState(reviewer ?? "");
  const trimmed = name.trim();

  const startTask = (route: Route) => {
    onSubmit(trimmed);
    navigate(route);
  };

  return (
    <Container size="xs" pt="xl">
      <Stack gap="md">
        <Title order={2}>Risk Repository Validator</Title>
        <Text c="dimmed">
          Enter your name to begin. Your name identifies your decisions in
          Airtable. Please always use the exact same name.
        </Text>
        <TextInput
          label="Your name"
          placeholder="e.g. Jane Doe"
          value={name}
          onChange={(event) => {
            setName(event.currentTarget.value);
          }}
          autoFocus
          required
        />
        {resuming ? (
          <Button
            disabled={trimmed === ""}
            onClick={() => {
              onSubmit(trimmed);
            }}
          >
            Continue
          </Button>
        ) : (
          <Group>
            <Button
              disabled={trimmed === ""}
              onClick={() => {
                startTask({ name: "screening" });
              }}
            >
              Abstract screening
            </Button>
            <Button
              disabled={trimmed === ""}
              onClick={() => {
                startTask({ name: "papers" });
              }}
            >
              Classification review
            </Button>
          </Group>
        )}
      </Stack>
    </Container>
  );
}
