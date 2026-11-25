// Detects browsers that hide their name in the User-Agent (currently Brave).
//
// Brave sends Chrome's exact User-Agent, but exposes navigator.brave.isBrave()
// (only Brave has it; Chrome, Edge, Vivaldi and other Chromium browsers do
// not). The result is sent to the API as the X-Client-Brand header, so the
// audit log can show "Brave" even when the browser's client hints are missing.
// It is only a display hint for the activity log; nothing relies on it for security.

export const CLIENT_BRAND_HEADER = "X-Client-Brand";

interface BraveNavigator extends Navigator {
  brave?: { isBrave?: () => Promise<boolean> };
}

let detection: Promise<string | null> | null = null;

export function detectClientBrand(nav: BraveNavigator | undefined = globalThis.navigator): Promise<string | null> {
  if (detection === null) {
    detection = (async () => {
      try {
        const isBrave = nav?.brave?.isBrave;
        return typeof isBrave === "function" && (await isBrave.call(nav?.brave)) === true ? "Brave" : null;
      } catch {
        return null; // detection must never break a request
      }
    })();
  }
  return detection;
}

// For tests: forget the cached result.
export function resetClientBrandDetection(): void {
  detection = null;
}
