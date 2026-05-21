import {
  Button,
  Container,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { type FormEvent, useState } from "react";

interface Props {
  onSubmit: (name: string) => void;
}

export function NamePrompt({ onSubmit }: Props) {
  const [name, setName] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed === "") {
      return;
    }
    onSubmit(trimmed);
  };

  return (
    <Container size="xs" pt="xl">
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <Title order={2}>Risk Repository Validator</Title>
          <Text c="dimmed">
            Enter your name to begin abstract screening. Your name identifies
            your decisions in Airtable and is saved locally so you don't have to
            re-enter it.
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
          <Button type="submit" disabled={name.trim() === ""}>
            Start screening
          </Button>
        </Stack>
      </form>
    </Container>
  );
}
