"use client";

import dynamic from "next/dynamic";
import type { AirtableBase } from "@/airtable/types";

const AirtableHeatmap = dynamic(
  () =>
    import("@/airtable/components/AirtableHeatmap").then(
      (mod) => mod.AirtableHeatmap,
    ),
  { ssr: false },
);

interface AirtableViewProps {
  bases: AirtableBase[];
}

export function AirtableView({ bases }: AirtableViewProps) {
  return <AirtableHeatmap bases={bases} />;
}
