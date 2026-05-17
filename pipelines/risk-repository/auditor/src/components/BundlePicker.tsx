import { Select } from "@mantine/core";
import { use } from "react";
import { getManifest } from "@/lib/api";

interface Props {
  value: string | null;
  onChange: (value: string | null) => void;
}

export function BundlePicker({ value, onChange }: Props) {
  const manifest = use(getManifest());
  const sorted = [...manifest.bundles].sort((a, b) =>
    b.generated_at.localeCompare(a.generated_at),
  );
  const data = sorted.map((entry) => ({
    value: entry.filename,
    label: entry.run_name ?? entry.filename,
  }));
  return (
    <Select
      placeholder="Select a bundle"
      data={data}
      value={value}
      onChange={onChange}
      w={320}
      searchable
      nothingFoundMessage="No bundles"
    />
  );
}
