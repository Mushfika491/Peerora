// React Router v7 behaviour, opted into early (react-router-dom 6.30).
// Used by the app's BrowserRouter and by every MemoryRouter in the tests, so
// tests run with exactly the same routing behaviour as the real app.
//
// - v7_startTransition: router state updates are wrapped in React.startTransition.
// - v7_relativeSplatPath: relative links inside splat ("*") routes resolve from
//   the full matched path. Peerora's only splat route is the 404 page and every
//   link in the app is absolute, so navigation is unchanged.
export const ROUTER_FUTURE = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;
