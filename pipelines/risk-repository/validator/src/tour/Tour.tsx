import { type Driver, type DriveStep, driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useEffect, useRef } from "react";
import { anchorSelector, findAnchor } from "@/tour/dom";
import type { TourStep } from "@/tour/steps";

interface Props {
  steps: TourStep[];
  onDone: () => void;
}

export function Tour({ steps, onDone }: Props) {
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  useEffect(() => {
    if (import.meta.env.DEV) {
      for (const step of steps) {
        if (step.anchor !== undefined) {
          findAnchor(step.anchor);
        }
      }
    }

    let instance: Driver | null = null;
    const driveSteps: DriveStep[] = steps.map((step) => ({
      element:
        step.anchor === undefined ? undefined : anchorSelector(step.anchor),
      skipMissingElement: step.anchor !== undefined,
      onHighlightStarted: () => {
        if (step.act === undefined) {
          return;
        }
        step.act();
        // The demo moves the layout under the popover, so re-measure once React
        // has painted the result.
        requestAnimationFrame(() => instance?.refresh());
      },
      popover: {
        title: step.title,
        description: step.body,
        side: step.side,
        align: step.align,
      },
    }));

    instance = driver({
      steps: driveSteps,
      showProgress: true,
      allowClose: true,
      overlayColor: "rgba(0, 0, 0, 0.55)",
      stagePadding: 6,
      stageRadius: 8,
      nextBtnText: "Next →",
      prevBtnText: "← Back",
      doneBtnText: "Done",
      progressText: "{{current}} of {{total}}",
      onDestroyStarted: () => {
        instance?.destroy();
        onDoneRef.current();
      },
    });
    instance.drive();

    return () => {
      instance?.destroy();
      instance = null;
    };
  }, [steps]);

  return null;
}
