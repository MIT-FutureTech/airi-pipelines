import type { WorkerEnv } from "@api/_env";

const ACCESS_EMAIL_HEADER = "Cf-Access-Authenticated-User-Email";

// In production, Cloudflare passes the user's email address in a header.
// During local development, use an environment variable instead.
export function userEmail(request: Request, env: WorkerEnv): string | null {
  const email =
    request.headers.get(ACCESS_EMAIL_HEADER) ?? env.LOCAL_USER_EMAIL ?? "";
  const normalized = email.trim().toLowerCase();
  return normalized === "" ? null : normalized;
}
