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

export function buildContentSecurityPolicy(apiBaseUrl = ""): string {
  const connect = ["'self'"];
  const trimmed = apiBaseUrl.trim();
  if (trimmed !== "") {
    connect.push(new URL(trimmed).origin); // a backend on another origin
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
