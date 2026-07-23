import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { DirectorsScreen } from "./Directors";

test("groups directors by entity with shareholding and status", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve([
            { id: 1, entity: 1, entity_name: "CNI Holdings", name: "Ada Bello", designation: "Chairman", appointed: "2019-03-01", ceased_on: null, active: true, shares: 8000000, share_class: "ordinary" },
            { id: 2, entity: 1, entity_name: "CNI Holdings", name: "Gone Person", designation: "NED", appointed: "2018-01-01", ceased_on: "2022-01-01", active: false, shares: null, share_class: null },
          ]),
      }),
    ),
  );
  render(
    <MemoryRouter>
      <DirectorsScreen />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getByText("Ada Bello")).toBeInTheDocument());
  expect(screen.getByText("CNI Holdings")).toBeInTheDocument();
  expect(screen.getByText("Chairman")).toBeInTheDocument();
  expect(screen.getByText("8,000,000")).toBeInTheDocument();
  expect(screen.getByText("Active")).toBeInTheDocument();
  expect(screen.getByText(/Ceased/)).toBeInTheDocument();
});
