import { type Driver, type DriveStep, driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useEffect, useRef } from "react";
import { anchorSelector, findAnchor } from "@/tour/dom";
import type { TourStep } from "@/tour/steps";

interface Props {
  steps: TourStep[];
  doneText: string;
  /** `reachedEnd` is false when the reviewer closed the tour part-way. */
  onClose: (reachedEnd: boolean) => void;
}

export function Tour({ steps, doneText, onClose }: Props) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

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
      overlayClickBehavior: () => {},
      overlayColor: "rgba(0, 0, 0, 0.55)",
      stagePadding: 6,
      stageRadius: 8,
      // Mantine Kbd
      nextBtnText: "Next →",
      prevBtnText: "← Back",
      doneBtnText: doneText,
      progressText: "{{current}} of {{total}}",
      onDestroyStarted: () => {
        const reachedEnd = instance?.isLastStep() ?? false;
        instance?.destroy();
        onCloseRef.current(reachedEnd);
      },
    });
    instance.drive();

    return () => {
      instance?.destroy();
      instance = null;
    };
  }, [steps, doneText]);

  return null;
}
