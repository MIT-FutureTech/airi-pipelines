import type { Decision, ManifestEntry } from "@api/_shared";
import { AppShell, Button, Group, Text, Title } from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { use, useMemo, useState } from "react";
import { DocumentCard } from "@/components/DocumentCard";
import { DoneScreen } from "@/components/DoneScreen";
import { Sidebar } from "@/components/Sidebar";
import { getManifest } from "@/lib/api";
import { clearReviewer } from "@/lib/storage";

interface Props {
  reviewer: string;
}

export function Validator({ reviewer }: Props) {
  const initial = use(getManifest(reviewer));
  const [manifest, setManifest] = useState<ManifestEntry[]>(initial.documents);
  const [activeId, setActiveId] = useState<string | null>(() =>
    firstUndecidedId(initial.documents),
  );
  const [search, setSearch] = useState("");

  const activeIndex = useMemo(() => {
    if (activeId === null) {
      return -1;
    }
    return manifest.findIndex((m) => m.id === activeId);
  }, [manifest, activeId]);

  const activeEntry = activeIndex === -1 ? null : manifest[activeIndex];

  const selectAndScroll = (id: string | null) => {
    setActiveId(id);
    if (id !== null) {
      requestAnimationFrame(() => {
        document
          .querySelector(`[data-doc-id="${id}"]`)
          ?.scrollIntoView({ block: "nearest" });
      });
    }
  };

  const navigate = (offset: number) => {
    if (manifest.length === 0) {
      return;
    }
    if (activeIndex === -1) {
      selectAndScroll(manifest[0].id);
      return;
    }
    const next = Math.max(
      0,
      Math.min(manifest.length - 1, activeIndex + offset),
    );
    if (next === activeIndex) {
      return;
    }
    selectAndScroll(manifest[next].id);
  };

  useHotkeys([
    ["ArrowLeft", () => navigate(-1)],
    ["ArrowRight", () => navigate(1)],
  ]);

  const handleSubmitted = (
    documentId: string,
    decision: Decision,
    comments: string | null,
    validationId: string,
  ) => {
    const updated = manifest.map((entry) =>
      entry.id === documentId
        ? { ...entry, decision, comments, validationId }
        : entry,
    );
    setManifest(updated);
    const nextId = nextUndecidedAfter(updated, documentId);
    selectAndScroll(nextId);
  };

  const switchReviewer = () => {
    clearReviewer();
    window.location.reload();
  };

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 320, breakpoint: "sm" }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={4}>Risk Repository Validator</Title>
          <Group gap="xs">
            <Text size="sm" c="dimmed">
              Reviewer:
            </Text>
            <Text size="sm" fw={500}>
              {reviewer}
            </Text>
            <Button size="xs" variant="subtle" onClick={switchReviewer}>
              Switch
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <Sidebar
          manifest={manifest}
          activeId={activeId}
          onSelect={selectAndScroll}
          search={search}
          onSearchChange={setSearch}
        />
      </AppShell.Navbar>
      <AppShell.Main style={{ height: "calc(100vh - 56px)" }}>
        {activeEntry === null ? (
          <DoneScreen total={manifest.length} />
        ) : (
          <DocumentCard
            key={activeEntry.id}
            reviewer={reviewer}
            entry={activeEntry}
            position={activeIndex + 1}
            total={manifest.length}
            onSubmitted={handleSubmitted}
          />
        )}
      </AppShell.Main>
    </AppShell>
  );
}

function firstUndecidedId(entries: ManifestEntry[]): string | null {
  const found = entries.find((e) => e.decision === null);
  return found?.id ?? null;
}

function nextUndecidedAfter(
  entries: ManifestEntry[],
  currentId: string,
): string | null {
  const currentIdx = entries.findIndex((e) => e.id === currentId);
  if (currentIdx === -1) {
    return firstUndecidedId(entries);
  }
  for (let i = currentIdx + 1; i < entries.length; i++) {
    if (entries[i].decision === null) {
      return entries[i].id;
    }
  }
  for (let i = 0; i < currentIdx; i++) {
    if (entries[i].decision === null) {
      return entries[i].id;
    }
  }
  return null;
}
