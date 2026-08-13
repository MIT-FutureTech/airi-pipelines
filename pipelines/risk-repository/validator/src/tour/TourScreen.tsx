import { useState } from "react";
import { ClassificationReview } from "@/components/ClassificationReview";
import { navigate } from "@/lib/route";
import { DEMO_PAPER } from "@/tour/demoPaper";
import { demoSource } from "@/tour/demoSource";
import { CHAPTER_TWO } from "@/tour/steps";
import { Tour } from "@/tour/Tour";

interface Props {
  reviewer: string;
}

export function TourScreen({ reviewer }: Props) {
  const [source] = useState(demoSource);

  return (
    <>
      <ClassificationReview
        reviewer={reviewer}
        quickRef={DEMO_PAPER.quickRef}
        mode="anchored"
        source={source}
      />
      <Tour
        steps={CHAPTER_TWO}
        doneText="Back to papers"
        onClose={() => {
          navigate({ name: "papers" });
        }}
      />
    </>
  );
}
