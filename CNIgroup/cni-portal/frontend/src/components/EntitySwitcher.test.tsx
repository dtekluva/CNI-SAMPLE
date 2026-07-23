import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { EntitySwitcher, type Entity } from "./EntitySwitcher";

function mockEntities(list: Entity[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(list) })),
  );
}

test("lists only the permitted entities returned by the API", async () => {
  mockEntities([{ id: 1, legal_name: "Alpha" }]);
  render(<EntitySwitcher />);
  await waitFor(() => expect(screen.getByText("Alpha")).toBeInTheDocument());
  // A single entity -> no group option.
  expect(screen.queryByText(/Group \(all entities\)/)).toBeNull();
});

test("shows the group option when multiple entities are permitted", async () => {
  mockEntities([
    { id: 1, legal_name: "Alpha" },
    { id: 2, legal_name: "Beta" },
  ]);
  render(<EntitySwitcher />);
  await waitFor(() => expect(screen.getByText("Beta")).toBeInTheDocument());
  expect(screen.getByText(/Group \(all entities\)/)).toBeInTheDocument();
});
