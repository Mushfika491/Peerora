import { describe, expect, it } from "vitest";
import { apiConnectSource, buildContentSecurityPolicy } from "../csp";

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
    expect(apiConnectSource("https://api.example.com/api")).toBe("https://api.example.com");
  });

  it("treats an empty value or a same-site path such as /api as the site's own origin", () => {
    for (const value of ["", "   ", "/api", "/api/", "/"]) {
      expect(apiConnectSource(value)).toBeNull();
      expect(buildContentSecurityPolicy(value)).toContain("connect-src 'self';");
    }
  });

  it("stops the build with a clear message for values that are not a path or an http(s) URL", () => {
    for (const value of ["peerora.vercel.app", "//evil.example", "ftp://files.example.com", "javascript:alert(1)"]) {
      expect(() => buildContentSecurityPolicy(value)).toThrow(/VITE_API_BASE_URL must be empty/);
    }
  });
});
