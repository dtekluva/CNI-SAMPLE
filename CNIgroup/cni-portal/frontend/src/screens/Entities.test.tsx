import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { EntitiesScreen } from "./Entities";

test("lists entities with completeness badges", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve([
            { id: 1, legal_name: "CNI Holdings", cac_rc_number: "RC1", is_complete: true },
            { id: 2, legal_name: "CNI Pay", cac_rc_number: "", is_complete: false },
          ]),
      }),
    ),
  );

  render(<EntitiesScreen />);
  await waitFor(() => expect(screen.getByText("CNI Holdings")).toBeInTheDocument());
  expect(screen.getByText("CNI Pay")).toBeInTheDocument();
  expect(screen.getByText("Complete")).toBeInTheDocument();
  expect(screen.getByText("Incomplete")).toBeInTheDocument();
});
