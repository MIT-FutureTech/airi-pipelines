import { Button, Container, Stack, Text, Title } from "@mantine/core";
import type { ClassificationSelection } from "@/lib/task";

interface Props {
  reviewer: string;
  selection: ClassificationSelection;
  onExit: () => void;
}

export function ClassificationReview({ reviewer, selection, onExit }: Props) {
  return (
    <Container size="sm" pt="xl">
      <Stack gap="md">
        <Title order={2}>Classification review</Title>
        <Text>Reviewer: {reviewer}</Text>
        <Text>Extraction run: {selection.extractionRun}</Text>
        <Text>Mode: {selection.mode}</Text>
        {selection.pipelineReviewer !== null ? (
          <Text>Anchored on: {selection.pipelineReviewer}</Text>
        ) : null}
        <Button variant="default" onClick={onExit}>
          Back to tasks
        </Button>
      </Stack>
    </Container>
  );
}
