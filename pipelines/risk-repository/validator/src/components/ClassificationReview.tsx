import type { ReviewResponse, RiskEntry } from "@api/_classification";
import {
  AppShell,
  Badge,
  Button,
  Center,
  Group,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { use, useMemo, useState } from "react";
import { RiskCard } from "@/components/RiskCard";
import { RiskSidebar } from "@/components/RiskSidebar";
import { getRiskManifest } from "@/lib/api";
import { isRiskCoded } from "@/lib/coding";
import type { ClassificationSelection } from "@/lib/task";

interface Props {
  reviewer: string;
  selection: ClassificationSelection;
  onExit: () => void;
}

export function ClassificationReview({ reviewer, selection, onExit }: Props) {
  const initial = use(
    getRiskManifest({
      extractionRun: selection.extractionRun,
      reviewer,
      mode: selection.mode,
      pipelineReviewer: selection.pipelineReviewer,
    }),
  );
  const [risks, setRisks] = useState<RiskEntry[]>(initial.risks);
  const [activeId, setActiveId] = useState<string | null>(() =>
    firstUncodedId(initial.risks),
  );
  const [search, setSearch] = useState("");

  const activeIndex = useMemo(() => {
    if (activeId === null) {
      return -1;
    }
    return risks.findIndex((risk) => risk.id === activeId);
  }, [risks, activeId]);

  const activeEntry = activeIndex === -1 ? null : risks[activeIndex];

  const selectAndScroll = (id: string | null) => {
    setActiveId(id);
    if (id !== null) {
      requestAnimationFrame(() => {
        document
          .querySelector(`[data-risk-id="${id}"]`)
          ?.scrollIntoView({ block: "nearest" });
      });
    }
  };

  const navigate = (offset: number) => {
    if (risks.length === 0) {
      return;
    }
    if (activeIndex === -1) {
      selectAndScroll(risks[0].id);
      return;
    }
    const next = Math.max(0, Math.min(risks.length - 1, activeIndex + offset));
    if (next === activeIndex) {
      return;
    }
    selectAndScroll(risks[next].id);
  };

  useHotkeys([
    ["ArrowLeft", () => navigate(-1)],
    ["ArrowRight", () => navigate(1)],
  ]);

  const handleResponsesChanged = (
    riskId: string,
    responses: ReviewResponse[],
  ) => {
    setRisks((prev) =>
      prev.map((risk) => (risk.id === riskId ? { ...risk, responses } : risk)),
    );
  };

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 340, breakpoint: "sm" }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            <Title order={4}>Classification review</Title>
            <Badge variant="light">{selection.extractionRun}</Badge>
            <Badge
              variant="light"
              color={selection.mode === "anchored" ? "grape" : "blue"}
            >
              {selection.mode}
            </Badge>
          </Group>
          <Group gap="md">
            <Group gap="xs">
              <Text size="sm" c="dimmed">
                Reviewer:
              </Text>
              <Text size="sm" fw={500}>
                {reviewer}
              </Text>
            </Group>
            <Button size="xs" variant="subtle" onClick={onExit}>
              Back to tasks
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <RiskSidebar
          risks={risks}
          activeId={activeId}
          onSelect={selectAndScroll}
          search={search}
          onSearchChange={setSearch}
        />
      </AppShell.Navbar>
      <AppShell.Main style={{ height: "calc(100vh - 56px)" }}>
        {activeEntry === null ? (
          <Center h="100%" p="md">
            <Stack gap="sm" align="center">
              <Title order={2}>All coded</Title>
              <Text c="dimmed">Every risk in this run has been coded.</Text>
              <Text c="dimmed" size="sm">
                Revisit any risk from the sidebar to revise it.
              </Text>
            </Stack>
          </Center>
        ) : (
          <RiskCard
            key={activeEntry.id}
            reviewer={reviewer}
            entry={activeEntry}
            mode={selection.mode}
            position={activeIndex + 1}
            total={risks.length}
            onResponsesChanged={handleResponsesChanged}
          />
        )}
      </AppShell.Main>
    </AppShell>
  );
}

function firstUncodedId(risks: RiskEntry[]): string | null {
  const found = risks.find((risk) => !isRiskCoded(risk.responses));
  return found?.id ?? null;
}
