import type { WorkerEnv } from "@api/_env";
import { errorResponse } from "@api/_http";
import judgements from "@api/judgements";

type Handler = (request: Request, env: WorkerEnv) => Promise<Response>;

const ROUTES = new Map<string, Handler>([["/api/judgements", judgements]]);

export default {
  async fetch(request: Request, env: WorkerEnv): Promise<Response> {
    const { pathname } = new URL(request.url);
    const handler = ROUTES.get(pathname);
    if (handler === undefined) {
      return errorResponse(404, `No such endpoint: ${pathname}`);
    }
    return await handler(request, env);
  },
};
