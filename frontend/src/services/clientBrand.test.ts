import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../test/helpers";
import { apiGet } from "./apiClient";
import { detectClientBrand, resetClientBrandDetection } from "./clientBrand";

afterEach(() => {
  resetClientBrandDetection();
  vi.unstubAllGlobals();
});

describe("navigator.brave detection", () => {
  it("reports Brave only when navigator.brave.isBrave() resolves true", async () => {
    const brave = { brave: { isBrave: () => Promise.resolve(true) } } as unknown as Navigator;
    expect(await detectClientBrand(brave)).toBe("Brave");
  });

  it("reports nothing for Chrome and other browsers without navigator.brave", async () => {
    expect(await detectClientBrand({} as Navigator)).toBeNull();
    resetClientBrandDetection();
    expect(await detectClientBrand(undefined)).toBeNull();
  });

  it("never throws if the check fails or lies", async () => {
    const broken = { brave: { isBrave: () => Promise.reject(new Error("blocked")) } } as unknown as Navigator;
    expect(await detectClientBrand(broken)).toBeNull();
    resetClientBrandDetection();
    const notBoolean = { brave: { isBrave: () => Promise.resolve("yes") } } as unknown as Navigator;
    expect(await detectClientBrand(notBoolean)).toBeNull();
  });

  it("sends the X-Client-Brand header with API requests in Brave", async () => {
    vi.stubGlobal("navigator", { brave: { isBrave: () => Promise.resolve(true) } });
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    await apiGet("/api/health");
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).get("X-Client-Brand")).toBe("Brave");
  });

  it("sends no hint header in other browsers", async () => {
    vi.stubGlobal("navigator", { userAgent: "Chrome" });
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    await apiGet("/api/health");
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).has("X-Client-Brand")).toBe(false);
  });
});
