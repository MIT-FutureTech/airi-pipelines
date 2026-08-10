import { Button } from "@mantine/core";
import { useState } from "react";
import { fetchPdfLink } from "@/lib/api";

interface Props {
  quickRef: string;
}

export function PdfDownloadButton({ quickRef }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const download = async () => {
    setLoading(true);
    setError(null);
    try {
      const link = await fetchPdfLink(quickRef);
      const response = await fetch(link.url);
      if (!response.ok) {
        throw new Error(`Airtable returned HTTP ${response.status}`);
      }
      save(await response.blob(), link.filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant={error === null ? "default" : "light"}
      color={error === null ? undefined : "red"}
      loading={loading}
      title={error ?? `Download ${quickRef}.pdf`}
      onClick={() => void download()}
    >
      PDF
    </Button>
  );
}

function save(blob: Blob, filename: string): void {
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => {
    URL.revokeObjectURL(href);
  }, 1000);
}
