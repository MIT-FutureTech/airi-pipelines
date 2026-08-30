import type { WorkerEnv } from "./_env.js";
import { errorResponse } from "./_http.js";
import codings from "./codings.js";
import decisions from "./decisions.js";
import documentsManifest from "./documents/manifest.js";
import papers from "./papers.js";
import pdf from "./pdf.js";
import risksManifest from "./risks/manifest.js";

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
