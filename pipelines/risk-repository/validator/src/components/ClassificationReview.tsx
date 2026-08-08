import type { ReviewResponse, RiskEntry } from "@api/_classification";
import {
  Alert,
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
import { fetchRiskManifest, getRiskManifest } from "@/lib/api";
import { codableRisks, isRiskCoded, pipelineIsReady } from "@/lib/coding";
import type { ClassificationSelection } from "@/lib/task";
import { ancestorsOf, indexRisks } from "@/lib/tree";

interface Props {
  reviewer: string;
  selection: ClassificationSelection;
  onExit: () => void;
  onSwitchToBlind: () => void;
}

export function ClassificationReview({
  reviewer,
  selection,
  onExit,
  onSwitchToBlind,
}: Props) {
  const { quickRef, mode } = selection;
  const initial = use(getRiskManifest({ quickRef, reviewer, mode }));
  const [risks, setRisks] = useState<RiskEntry[]>(initial.risks);
  const [activeId, setActiveId] = useState<string | null>(() =>
    firstUncodedId(initial.risks),
  );
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [expandedAncestors, setExpandedAncestors] = useState<string[]>([]);

  const codable = codableRisks(risks);
  const waitingForPipeline = mode === "anchored" && !pipelineIsReady(risks);

  const checkForPipeline = async () => {
    setChecking(true);
    setCheckError(null);
    try {
      const fresh = await fetchRiskManifest({ quickRef, reviewer, mode });
      setRisks(fresh.risks);
    } catch (err) {
      setCheckError(err instanceof Error ? err.message : String(err));
    } finally {
      setChecking(false);
    }
  };

  const index = useMemo(() => indexRisks(risks), [risks]);

  const activeEntry = risks.find((risk) => risk.id === activeId) ?? null;
  const codableIndex =
    activeEntry === null
      ? -1
      : codable.findIndex((risk) => risk.id === activeEntry.id);

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
    if (codable.length === 0) {
      return;
    }
    if (codableIndex === -1) {
      selectAndScroll(codable[0].id);
      return;
    }
    const next = Math.max(
      0,
      Math.min(codable.length - 1, codableIndex + offset),
    );
    if (next !== codableIndex) {
      selectAndScroll(codable[next].id);
    }
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
        <Group h="100%" px="md" gap="md" wrap="nowrap">
          <Title order={4} style={{ flexShrink: 0 }}>
            {quickRef}
          </Title>
          <Text
            size="sm"
            c="dimmed"
            lineClamp={1}
            style={{ flex: 1, minWidth: 0 }}
          >
            {initial.title ?? ""}
          </Text>
          <Group gap="sm" wrap="nowrap" style={{ flexShrink: 0 }}>
            <Text size="sm" fw={500}>
              {reviewer}
            </Text>
            <Badge
              variant="light"
              color={mode === "anchored" ? "grape" : "blue"}
            >
              {mode}
            </Badge>
            <Button size="xs" variant="subtle" onClick={onExit}>
              Back to papers
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <RiskSidebar
          risks={risks}
          activeId={activeId}
          onSelect={selectAndScroll}
        />
      </AppShell.Navbar>
      <AppShell.Main style={{ height: "calc(100vh - 56px)" }}>
        {waitingForPipeline ? (
          <WaitingForPipeline
            checking={checking}
            error={checkError}
            onCheckAgain={checkForPipeline}
            onSwitchToBlind={onSwitchToBlind}
          />
        ) : activeEntry === null ? (
          <Center h="100%" p="md">
            <Stack gap="sm" align="center">
              <Title order={2}>All coded</Title>
              <Text c="dimmed">Every risk in this paper has been coded.</Text>
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
            ancestors={ancestorsOf(index, activeEntry)}
            expandedAncestors={expandedAncestors}
            mode={mode}
            position={codableIndex + 1}
            total={codable.length}
            onResponsesChanged={handleResponsesChanged}
            onExpandedAncestorsChange={setExpandedAncestors}
          />
        )}
      </AppShell.Main>
    </AppShell>
  );
}

interface WaitingProps {
  checking: boolean;
  error: string | null;
  onCheckAgain: () => void;
  onSwitchToBlind: () => void;
}

function WaitingForPipeline({
  checking,
  error,
  onCheckAgain,
  onSwitchToBlind,
}: WaitingProps) {
  return (
    <Center h="100%" p="md">
      <Stack gap="md" align="center" maw={440}>
        <Title order={3}>Not classified yet</Title>
        <Text c="dimmed" ta="center">
          The pipeline has not classified this paper. Anchored review starts
          once its classification is in.
        </Text>
        {error !== null ? (
          <Alert color="red" title="Could not check" w="100%">
            {error}
          </Alert>
        ) : null}
        <Group gap="sm">
          <Button onClick={onCheckAgain} loading={checking}>
            Check again
          </Button>
          <Button variant="default" onClick={onSwitchToBlind}>
            Review blind instead
          </Button>
        </Group>
      </Stack>
    </Center>
  );
}

function firstUncodedId(risks: RiskEntry[]): string | null {
  const found = codableRisks(risks).find((risk) => !isCoded(risk.responses));
  return found?.id ?? null;
}
