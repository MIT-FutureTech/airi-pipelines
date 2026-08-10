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
import type { ReviewMode, RiskEntry } from "@shared/classification";
import { isCoded } from "@shared/coding";
import { use, useEffect, useMemo, useState } from "react";
import { PdfDownloadButton } from "@/components/PdfDownloadButton";
import { RiskCard } from "@/components/RiskCard";
import { RiskSidebar } from "@/components/RiskSidebar";
import { fetchRiskManifest, getRiskManifest, saveCodings } from "@/lib/api";
import {
  codingsRequest,
  type Draft,
  draftEquals,
  draftFromResponses,
} from "@/lib/draft";
import { codableRisks, pipelineIsReady } from "@/lib/risks";
import { navigate } from "@/lib/route";
import { ancestorsOf, indexRisks } from "@/lib/tree";

interface Props {
  reviewer: string;
  quickRef: string;
  mode: ReviewMode;
}

type SaveState =
  | { status: "idle" }
  | { status: "saving"; riskId: string }
  | { status: "saved"; riskId: string }
  | { status: "failed"; riskId: string; message: string };

export function ClassificationReview({ reviewer, quickRef, mode }: Props) {
  const [manifest] = useState(() =>
    getRiskManifest({ quickRef, reviewer, mode }),
  );
  const initial = use(manifest);
  const [risks, setRisks] = useState<RiskEntry[]>(initial.risks);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [save, setSave] = useState<SaveState>({ status: "idle" });
  const [activeId, setActiveId] = useState<string | null>(() =>
    firstUncodedId(initial.risks),
  );
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [expandedAncestors, setExpandedAncestors] = useState<string[]>([]);

  const codable = codableRisks(risks);
  const waitingForPipeline = mode === "anchored" && !pipelineIsReady(risks);

  const dirtyIds = useMemo(() => {
    const ids = new Set<string>();
    for (const risk of risks) {
      const draft = drafts[risk.id];
      if (
        draft !== undefined &&
        !draftEquals(draft, draftFromResponses(risk.responses))
      ) {
        ids.add(risk.id);
      }
    }
    return ids;
  }, [risks, drafts]);

  const hasUnsavedWork = dirtyIds.size > 0;
  useEffect(() => {
    if (!hasUnsavedWork) {
      return;
    }
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("beforeunload", warn);
    };
  }, [hasUnsavedWork]);

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
  const activeDraft =
    activeEntry === null
      ? null
      : (drafts[activeEntry.id] ?? draftFromResponses(activeEntry.responses));
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

  const step = (offset: number) => {
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

  const saveActive = async () => {
    if (
      activeEntry === null ||
      activeDraft === null ||
      !dirtyIds.has(activeEntry.id)
    ) {
      return;
    }
    const entry = activeEntry;
    const draft = activeDraft;
    setSave({ status: "saving", riskId: entry.id });
    try {
      const saved = await saveCodings(
        codingsRequest({ reviewer, mode, entry, draft }),
      );
      setRisks((prev) =>
        prev.map((risk) =>
          risk.id === entry.id ? { ...risk, responses: saved.responses } : risk,
        ),
      );
      setDrafts((prev) => {
        const current = prev[entry.id];
        if (current === undefined || !draftEquals(current, draft)) {
          return prev;
        }
        const { [entry.id]: _saved, ...rest } = prev;
        return rest;
      });
      setSave({ status: "saved", riskId: entry.id });
    } catch (err) {
      setSave({
        status: "failed",
        riskId: entry.id,
        message: err instanceof Error ? err.message : String(err),
      });
      // A save can fail after part of it landed, so rebase on what Airtable
      // actually holds; otherwise a retry duplicates the rows that succeeded.
      fetchRiskManifest({ quickRef, reviewer, mode })
        .then((fresh) => {
          setRisks(fresh.risks);
        })
        .catch((error: unknown) => {
          console.warn("Could not refresh after a failed save", error);
        });
    }
  };

  useHotkeys([
    ["ArrowLeft", () => step(-1)],
    ["ArrowRight", () => step(1)],
  ]);
  useHotkeys([["mod+Enter", () => void saveActive()]], []);

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
            <PdfDownloadButton quickRef={quickRef} />
            <Text size="sm" fw={500}>
              {reviewer}
            </Text>
            <Badge
              variant="light"
              color={mode === "anchored" ? "grape" : "blue"}
            >
              {mode}
            </Badge>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <RiskSidebar
          risks={risks}
          activeId={activeId}
          dirtyIds={dirtyIds}
          onSelect={selectAndScroll}
        />
      </AppShell.Navbar>
      <AppShell.Main style={{ height: "calc(100vh - 56px)" }}>
        {waitingForPipeline ? (
          <WaitingForPipeline
            checking={checking}
            error={checkError}
            onCheckAgain={checkForPipeline}
            onSwitchToBlind={() =>
              navigate({ name: "classification", quickRef, mode: "blind" })
            }
          />
        ) : activeEntry === null || activeDraft === null ? (
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
            entry={activeEntry}
            ancestors={ancestorsOf(index, activeEntry)}
            expandedAncestors={expandedAncestors}
            draft={activeDraft}
            dirty={dirtyIds.has(activeEntry.id)}
            saving={save.status === "saving" && save.riskId === activeEntry.id}
            saved={save.status === "saved" && save.riskId === activeEntry.id}
            error={
              save.status === "failed" && save.riskId === activeEntry.id
                ? save.message
                : null
            }
            position={codableIndex + 1}
            total={codable.length}
            onDraftChange={(draft) => {
              setDrafts((prev) => ({ ...prev, [activeEntry.id]: draft }));
            }}
            onSave={() => void saveActive()}
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
