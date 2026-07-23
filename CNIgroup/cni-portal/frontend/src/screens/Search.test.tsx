import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { SearchScreen } from "./Search";

test("searches across types and offers exports to leadership", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      let body: unknown = {};
      if (url.includes("/search/"))
        body = {
          q: "budget",
          results: [
            { kind: "meeting", id: 1, title: "Budget review board", subtitle: "CNI Holdings · 21 Jul 2026", link: "/meetings/1" },
            { kind: "document", id: 2, title: "2026 Group Budget", subtitle: "CNI Holdings · Finance", link: "/documents/2" },
          ],
        };
      else if (url.includes("/entities/")) body = [{ id: 1, legal_name: "CNI Holdings" }];
      else if (url.includes("/roles/options/")) body = { can_manage: true };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    }),
  );
  render(
    <MemoryRouter>
      <SearchScreen />
    </MemoryRouter>,
  );

  fireEvent.change(screen.getByLabelText(/Search meetings/), { target: { value: "budget" } });
  await waitFor(() => expect(screen.getByText("Budget review board")).toBeInTheDocument());
  expect(screen.getByText("2026 Group Budget")).toBeInTheDocument();
  expect(screen.getByText("Meetings")).toBeInTheDocument();
  expect(screen.getByText("Documents")).toBeInTheDocument();

  // exports panel for leadership
  expect(screen.getByText("Regulator-ready exports")).toBeInTheDocument();
  expect(screen.getByText("Minute Book")).toBeInTheDocument();
  expect(screen.getAllByText("Export PDF").length).toBe(4);
});
