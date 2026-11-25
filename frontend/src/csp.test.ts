import { describe, expect, it } from "vitest";
import { buildContentSecurityPolicy } from "../csp";

describe("frontend Content-Security-Policy", () => {
  it("allows only what the app loads", () => {
    const policy = buildContentSecurityPolicy();
    expect(policy).toContain("default-src 'self'");
    expect(policy).toContain("script-src 'self'");
    expect(policy).not.toContain("unsafe-inline");
    expect(policy).not.toContain("unsafe-eval");
    expect(policy).toContain("style-src 'self' https://fonts.googleapis.com");
    expect(policy).toContain("font-src 'self' https://fonts.gstatic.com");
    expect(policy).toContain("connect-src 'self'");
    expect(policy).toContain("object-src 'none'");
  });

  it("allows a separately hosted API when VITE_API_BASE_URL is set", () => {
    expect(buildContentSecurityPolicy("https://api.example.com/")).toContain("connect-src 'self' https://api.example.com");
  });
});
