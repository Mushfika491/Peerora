import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ROUTER_FUTURE } from "../routerFuture";
import NotFoundPage from "../pages/NotFoundPage";
import EmptyState from "./EmptyState";

describe("EmptyState heading level", () => {
  it("uses h2 by default (a box inside a page that has its own h1)", () => {
    render(<EmptyState title="No records yet" message="Add one." />);
    expect(screen.getByRole("heading", { level: 2, name: "No records yet" })).toBeInTheDocument();
  });

  it("gives the 404 page an h1", () => {
    render(
      <MemoryRouter future={ROUTER_FUTURE}>
        <NotFoundPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
  });
});
