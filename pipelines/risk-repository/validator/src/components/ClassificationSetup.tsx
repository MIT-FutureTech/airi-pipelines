import type { ReviewMode } from "@api/_classification";
import {
  Button,
  Container,
  Group,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { use, useState } from "react";
import { getRuns } from "@/lib/api";
import type { ClassificationSelection } from "@/lib/task";

interface Props {
  onStart: (selection: ClassificationSelection) => void;
  onBack: () => void;
}

export function ClassificationSetup({ onStart, onBack }: Props) {
  const { runs } = use(getRuns());
  const [extractionRun, setExtractionRun] = useState<string | null>(
    runs[0]?.extractionRun ?? null,
  );
  const [mode, setMode] = useState<ReviewMode>("blind");
  const [pipelineReviewer, setPipelineReviewer] = useState<string | null>(null);

  const selectedRun = runs.find((run) => run.extractionRun === extractionRun);
  const availablePipeline = selectedRun?.pipelineReviewers ?? [];
  const anchoredAvailable = availablePipeline.length > 0;

  const changeRun = (value: string | null) => {
    setExtractionRun(value);
    const next = runs.find((run) => run.extractionRun === value);
    const available = next?.pipelineReviewers ?? [];
    if (mode === "anchored" && available.length === 0) {
      setMode("blind");
      setPipelineReviewer(null);
    } else if (mode === "anchored") {
      setPipelineReviewer(available[0]);
    }
  };

  const changeMode = (value: string) => {
    const nextMode = value as ReviewMode;
    setMode(nextMode);
    setPipelineReviewer(
      nextMode === "anchored" ? (availablePipeline[0] ?? null) : null,
    );
  };

  const canStart =
    extractionRun !== null && (mode === "blind" || pipelineReviewer !== null);

  const start = () => {
    if (extractionRun === null) {
      return;
    }
    onStart({
      task: "classification",
      extractionRun,
      mode,
      pipelineReviewer: mode === "anchored" ? pipelineReviewer : null,
    });
  };

  if (runs.length === 0) {
    return (
      <Container size="xs" pt="xl">
        <Stack gap="md">
          <Title order={2}>Classification review</Title>
          <Text c="dimmed">No extraction runs found.</Text>
          <Button variant="default" onClick={onBack}>
            Back
          </Button>
        </Stack>
      </Container>
    );
  }

  return (
    <Container size="xs" pt="xl">
      <Stack gap="md">
        <Title order={2}>Classification review</Title>
        <Select
          label="Extraction run"
          data={runs.map((run) => ({
            value: run.extractionRun,
            label: `${run.extractionRun} (${run.riskCount} risks)`,
          }))}
          value={extractionRun}
          onChange={changeRun}
          allowDeselect={false}
        />
        <Stack gap={4}>
          <Text size="sm" fw={500}>
            Mode
          </Text>
          <SegmentedControl
            value={mode}
            onChange={changeMode}
            data={[
              { value: "blind", label: "Blind" },
              {
                value: "anchored",
                label: "Anchored",
                disabled: !anchoredAvailable,
              },
            ]}
          />
          <Text size="xs" c="dimmed">
            {mode === "blind"
              ? "Code each risk without seeing the pipeline's suggestion."
              : "Start from the pipeline's suggestion and correct it."}
          </Text>
        </Stack>
        {mode === "anchored" && availablePipeline.length > 1 ? (
          <Select
            label="Pipeline coding to anchor on"
            data={availablePipeline}
            value={pipelineReviewer}
            onChange={setPipelineReviewer}
            allowDeselect={false}
          />
        ) : null}
        <Group justify="space-between">
          <Button variant="default" onClick={onBack}>
            Back
          </Button>
          <Button onClick={start} disabled={!canStart}>
            Start review
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}
