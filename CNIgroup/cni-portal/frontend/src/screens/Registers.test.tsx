import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { RegistersScreen } from "./Registers";

test("lists register entries with particulars and filters by type", async () => {
  const fetchMock = vi.fn((url: string) =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve(
          url.includes("/entities/")
            ? [{ id: 1, legal_name: "CNI Holdings" }]
            : [
                {
                  id: 1, entity: 1, register_type: "members", register_type_display: "Register of Members",
                  party_name: "Okonkwo Family Trust", particulars: { shares: 60000000, class: "ordinary" },
                  effective_from: "2018-01-01", ceased_on: null, is_active: true,
                },
              ],
        ),
    }),
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<RegistersScreen />);
  await waitFor(() => expect(screen.getByText("Okonkwo Family Trust")).toBeInTheDocument());
  expect(screen.getByText("Register of Members")).toBeInTheDocument();
  expect(screen.getByText(/60,000,000 ordinary shares/)).toBeInTheDocument();
  expect(screen.getByText("Current")).toBeInTheDocument();

  fireEvent.click(screen.getByText("Directors"));
  await waitFor(() =>
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("register_type=directors"))).toBe(true),
  );
});
