import type { SaveJudgementRequest } from "@shared/judgements";
import { describe, expect, it } from "vitest";
import { createSaveQueue } from "@/lib/saving";

function request(comment: string): SaveJudgementRequest {
  return {
    companyId: "recBank",
    companyName: "Example Bank",
    codeRecordId: "recDomain22",
    codeKey: "Domain 2.2",
    decision: null,
    comment,
    supportingMitigationRecordIds: [],
  };
}

describe("createSaveQueue", () => {
  it("sends a cell's saves one at a time, in order", async () => {
    const events: string[] = [];
    const enqueue = createSaveQueue(async ({ comment }) => {
      events.push(`start ${comment}`);
      await new Promise((resolve) =>
        setTimeout(resolve, comment === "first" ? 20 : 0),
      );
      events.push(`end ${comment}`);
    });

    await Promise.all([
      enqueue("cell", request("first")),
      enqueue("cell", request("second")),
    ]);

    expect(events).toEqual([
      "start first",
      "end first",
      "start second",
      "end second",
    ]);
  });

  it("carries on after a failed save", async () => {
    const saved: string[] = [];
    const enqueue = createSaveQueue(async ({ comment }) => {
      if (comment === "first") {
        throw new Error("Airtable is down");
      }
      saved.push(comment);
    });

    const first = enqueue("cell", request("first"));
    const second = enqueue("cell", request("second"));

    await expect(first).rejects.toThrow("Airtable is down");
    await second;
    expect(saved).toEqual(["second"]);
  });

  it("doesn't make other cells wait", async () => {
    const events: string[] = [];
    let finishSlow = () => {};
    const enqueue = createSaveQueue(async ({ comment }) => {
      if (comment === "slow") {
        await new Promise<void>((resolve) => {
          finishSlow = resolve;
        });
      }
      events.push(comment);
    });

    const slow = enqueue("first cell", request("slow"));
    await enqueue("second cell", request("quick"));
    finishSlow();
    await slow;

    expect(events).toEqual(["quick", "slow"]);
  });
});
