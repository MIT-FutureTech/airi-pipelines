import type { WorkerEnv } from "@api/_env";
import { errorResponse } from "@api/_http";
import codings from "@api/codings";
import decisions from "@api/decisions";
import documentsManifest from "@api/documents/manifest";
import papers from "@api/papers";
import pdf from "@api/pdf";
import risksManifest from "@api/risks/manifest";

type Handler = (request: Request, env: WorkerEnv) => Promise<Response>;

const ROUTES = new Map<string, Handler>([
  ["/api/codings", codings],
  ["/api/decisions", decisions],
  ["/api/documents/manifest", documentsManifest],
  ["/api/papers", papers],
  ["/api/pdf", pdf],
  ["/api/risks/manifest", risksManifest],
]);

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
