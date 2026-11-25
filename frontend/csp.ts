// Content-Security-Policy for the built React app.
//
// It is added as a <meta> tag to dist/index.html during `vite build` only:
// the Vite dev server injects inline scripts for hot reloading, which a
// strict policy would block. (frame-ancestors cannot be set from a <meta>
// tag; the API already sends X-Frame-Options: DENY and its own CSP.)
//
// What the app actually loads:
//   scripts and styles - its own bundle (same origin), Google Fonts CSS
//   fonts              - fonts.gstatic.com
//   images             - same origin, data: URLs, and tutor photos (any https URL)
//   API calls          - same origin (/api), plus VITE_API_BASE_URL if set
import type { Plugin } from "vite";

// The extra connect-src source needed for VITE_API_BASE_URL, or null when the
// API is on the site's own origin (already allowed by 'self'):
//   ""  or a path on this site such as "/api"  -> null (same origin)
//   "https://api.example.com/..."             -> "https://api.example.com"
// Anything else (a host without http(s)://, "//host", other protocols) stops
// the build with a clear message instead of silently widening the policy.
export function apiConnectSource(apiBaseUrl = ""): string | null {
  const value = apiBaseUrl.trim();
  if (value === "" || (value.startsWith("/") && !value.startsWith("//"))) {
    return null;
  }
  let url: URL | null = null;
  try {
    url = new URL(value);
  } catch {
    url = null;
  }
  if (url === null || (url.protocol !== "https:" && url.protocol !== "http:")) {
    throw new Error(
      "VITE_API_BASE_URL must be empty (recommended: the API is served on the same origin under /api), " +
        "a path on this site such as /api, or a full http(s):// address of a separately hosted API."
    );
  }
  return url.origin;
}

export function buildContentSecurityPolicy(apiBaseUrl = ""): string {
  const connect = ["'self'"];
  const apiSource = apiConnectSource(apiBaseUrl);
  if (apiSource !== null) {
    connect.push(apiSource); // a backend on another origin
  }
  const directives: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": connect,
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
  };
  return Object.entries(directives)
    .map(([name, values]) => `${name} ${values.join(" ")}`)
    .join("; ");
}

export function contentSecurityPolicyPlugin(apiBaseUrl = ""): Plugin {
  return {
    name: "peerora-content-security-policy",
    apply: "build",
    transformIndexHtml() {
      return [
        {
          tag: "meta",
          attrs: { "http-equiv": "Content-Security-Policy", content: buildContentSecurityPolicy(apiBaseUrl) },
          injectTo: "head-prepend",
        },
      ];
    },
  };
}
