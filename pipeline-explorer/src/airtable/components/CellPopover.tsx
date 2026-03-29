"use client";

import * as Popover from "@radix-ui/react-popover";
import type { ReactNode } from "react";
import styles from "./CellPopover.module.css";

interface CellPopoverProps {
  children: ReactNode;
  content: ReactNode;
}

export function CellPopover({ children, content }: CellPopoverProps) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>{children}</Popover.Trigger>
      <Popover.Portal>
        <Popover.Content className={styles.content} sideOffset={4}>
          {content}
          <Popover.Arrow className={styles.arrow} />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
