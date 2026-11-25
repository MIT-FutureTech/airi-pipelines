import { userEmail } from "@api/_user";
import { describe, expect, it } from "vitest";

function request(headers: Record<string, string>): Request {
  return new Request("https://reviewer.example.com/api/judgements", {
    headers,
  });
}

describe("userEmail", () => {
  it("takes the email Cloudflare Access signed in", () => {
    const signedIn = request({
      "Cf-Access-Authenticated-User-Email": " Someone@Example.com ",
    });

    expect(userEmail(signedIn, { LOCAL_USER_EMAIL: "dev@example.com" })).toBe(
      "someone@example.com",
    );
  });

  it("falls back to the local email when Access isn't there", () => {
    expect(
      userEmail(request({}), { LOCAL_USER_EMAIL: "dev@example.com" }),
    ).toBe("dev@example.com");
  });

  it("finds no user without either", () => {
    expect(userEmail(request({}), {})).toBeNull();
  });
});
