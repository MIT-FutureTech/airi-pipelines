import type { SaveJudgementRequest } from "@shared/judgements";

export type SaveStatus = "saving" | "saved" | "failed";

export type SaveQueue = (
  key: string,
  request: SaveJudgementRequest,
) => Promise<void>;

// Saves each cell's judgement one request at a time, so that an older save
// can't overwrite a newer one.
export function createSaveQueue(
  save: (request: SaveJudgementRequest) => Promise<unknown>,
): SaveQueue {
  const queues = new Map<string, Promise<void>>();
  return (key, request) => {
    const previous = queues.get(key) ?? Promise.resolve();
    const next = previous
      .catch(() => undefined)
      .then(async () => {
        await save(request);
      });
    queues.set(key, next);
    return next;
  };
}
