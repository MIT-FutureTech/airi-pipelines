import { useState } from "react";
import { ClassificationReview } from "@/components/ClassificationReview";
import { DEMO_PAPER } from "@/tour/demoPaper";
import { demoSource } from "@/tour/demoSource";

interface Props {
  reviewer: string;
}

export function TourScreen({ reviewer }: Props) {
  const [source] = useState(demoSource);

  return (
    <ClassificationReview
      reviewer={reviewer}
      quickRef={DEMO_PAPER.quickRef}
      mode="anchored"
      source={source}
    />
  );
}
