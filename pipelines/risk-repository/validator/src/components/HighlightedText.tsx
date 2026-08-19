import { Fragment, useMemo } from "react";
import { type HighlightGroup, highlightText } from "@/lib/highlight";

interface Props {
  text: string;
  groups: HighlightGroup[];
}

export function HighlightedText({ text, groups }: Props) {
  const chunks = useMemo(() => highlightText(text, groups), [text, groups]);
  return (
    <>
      {chunks.map((chunk, idx) => {
        const key = `${idx}-${chunk.text}`;
        if (chunk.color === null) {
          return <Fragment key={key}>{chunk.text}</Fragment>;
        }
        return (
          <mark
            key={key}
            style={{
              backgroundColor: `var(--mantine-color-${chunk.color}-3)`,
              color: "#000",
              padding: 0,
              borderRadius: 2,
            }}
          >
            {chunk.text}
          </mark>
        );
      })}
    </>
  );
}
