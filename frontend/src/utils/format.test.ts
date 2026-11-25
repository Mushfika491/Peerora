import { afterEach, describe, expect, it } from "vitest";
import { describeUserAgent, formatDate, formatDateTime, identifyBrowser, parseApiDate } from "./format";

// Real User-Agent strings.
const UA = {
  chromeLinux: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  // What the backend stores for Brave: Chrome's UA plus the token from client hints / navigator.brave.
  braveLinux: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Brave/131",
  braveHintOnly: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Brave",
  firefoxLinux: "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
  edgeWindows: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
  operaMac: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/115.0.0.0",
  safariMac: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
  chromeAndroid: "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
};

describe("UTC to local time", () => {
  const event = "2026-11-24T00:37:00Z"; // stored and sent by the API in UTC

  it("shows Bangladesh time (UTC+6) for a viewer in Asia/Dhaka", () => {
    expect(formatDateTime(event, "Asia/Dhaka")).toBe("24 Nov 2026, 06:37");
  });

  it("uses real timezone rules, not a fixed offset", () => {
    expect(formatDateTime(event, "UTC")).toBe("24 Nov 2026, 00:37");
    expect(formatDateTime(event, "America/New_York")).toBe("23 Nov 2026, 19:37"); // UTC-5 in November
    expect(formatDateTime("2026-07-01T12:00:00Z", "America/New_York")).toBe("1 Jul 2026, 08:00"); // UTC-4 in July
    expect(formatDateTime(event, "Asia/Kolkata")).toBe("24 Nov 2026, 06:07"); // UTC+5:30
  });

  it("treats a timestamp without a timezone as UTC, never as local time", () => {
    expect(formatDateTime("2026-11-24T00:37:00", "Asia/Dhaka")).toBe("24 Nov 2026, 06:37");
    expect(formatDateTime("2026-11-24T00:37:00.500612", "Asia/Dhaka")).toBe("24 Nov 2026, 06:37");
    expect(formatDateTime("2026-11-24T00:37:00+00:00", "Asia/Dhaka")).toBe("24 Nov 2026, 06:37");
    expect(parseApiDate("2026-11-24T00:37:00")?.toISOString()).toBe("2026-11-24T00:37:00.000Z");
  });

  it("converts across the date line correctly", () => {
    expect(formatDate("2026-11-23T19:30:00Z", "Asia/Dhaka")).toBe("24 November 2026"); // 01:30 next day
    expect(formatDate("2026-11-23T19:30:00Z", "UTC")).toBe("23 November 2026");
  });

  it("keeps calendar dates (due dates) on the same day everywhere", () => {
    expect(formatDate("2026-11-28", "America/New_York")).toBe("28 November 2026");
    expect(formatDate("2026-11-28", "Asia/Dhaka")).toBe("28 November 2026");
  });

  it("handles missing and invalid values", () => {
    expect(formatDateTime(null)).toBe("never");
    expect(formatDateTime("not a date")).toBe("not a date");
  });
});

describe("default timezone is the viewer's own", () => {
  const original = process.env.TZ;
  afterEach(() => {
    process.env.TZ = original;
  });

  it("follows the system timezone when none is given", () => {
    process.env.TZ = "Asia/Dhaka";
    expect(formatDateTime("2026-11-24T00:37:00Z")).toBe("24 Nov 2026, 06:37");
    process.env.TZ = "UTC";
    expect(formatDateTime("2026-11-24T00:37:00Z")).toBe("24 Nov 2026, 00:37");
  });
});

describe("browser identification", () => {
  it("identifies Brave from the token the backend adds", () => {
    expect(identifyBrowser(UA.braveLinux)).toBe("Brave");
    expect(identifyBrowser(UA.braveHintOnly)).toBe("Brave");
    expect(describeUserAgent(UA.braveLinux)).toBe("Brave on Linux");
  });

  it("does not call other Chromium browsers Brave", () => {
    expect(identifyBrowser(UA.chromeLinux)).toBe("Chrome");
    expect(describeUserAgent(UA.chromeLinux)).toBe("Chrome on Linux");
    expect(identifyBrowser(UA.edgeWindows)).toBe("Edge");
    expect(identifyBrowser(UA.operaMac)).toBe("Opera");
    expect(describeUserAgent(UA.chromeAndroid)).toBe("Chrome on Android");
  });

  it("identifies Firefox and Safari", () => {
    expect(describeUserAgent(UA.firefoxLinux)).toBe("Firefox on Linux");
    expect(describeUserAgent(UA.safariMac)).toBe("Safari on macOS");
  });

  it("falls back sensibly for unknown or missing user agents", () => {
    expect(identifyBrowser("curl/8.5.0")).toBe("Unknown browser");
    expect(describeUserAgent("curl/8.5.0")).toBe("Unknown browser");
    expect(describeUserAgent("python-httpx/0.28 (Linux)")).toBe("Unknown browser on Linux");
    expect(describeUserAgent(null)).toBe("Unknown device");
    expect(describeUserAgent("")).toBe("Unknown device");
  });
});
