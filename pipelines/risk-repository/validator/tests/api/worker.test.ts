import worker from "@api/worker";
import { describe, expect, it } from "vitest";

function get(path: string): Promise<Response> {
  return worker.fetch(new Request(`https://validator.test${path}`), {});
}

describe("worker", () => {
  it("rejects an unknown endpoint", async () => {
    const response = await get("/api/nope");
    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({
      error: "No such endpoint: /api/nope",
    });
  });

  it("routes a known endpoint to its handler", async () => {
    // The codings handler rejects GET before reading any configuration, so a
    // 405 here means the request reached it.
    const response = await get("/api/codings");
    expect(response.status).toBe(405);
  });
});
