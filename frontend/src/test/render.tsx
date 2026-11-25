import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { ToastProvider } from "../components/Toast";
import { ROUTER_FUTURE } from "../routerFuture";

// Shows the current path so tests can assert redirects.
export function LocationProbe() {
  const location = useLocation();
  return <p data-testid="location">{location.pathname}</p>;
}

// Renders a page inside a router (at `path`, matching `pattern`) and the toast provider.
export function renderWithRouter(ui: ReactElement, { path = "/", pattern = "*" } = {}) {
  return render(
    <MemoryRouter initialEntries={[path]} future={ROUTER_FUTURE}>
      <ToastProvider>
        <Routes>
          <Route path={pattern} element={ui} />
          <Route path="/login" element={<LocationProbe />} />
        </Routes>
      </ToastProvider>
    </MemoryRouter>
  );
}
