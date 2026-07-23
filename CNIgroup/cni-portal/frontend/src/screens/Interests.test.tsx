import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { InterestsScreen } from "./Interests";

test("lists interests, declares a new one, withdraws", async () => {
  const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ ok: true }) });
    if (url.includes("/entities/"))
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([{ id: 1, legal_name: "CNI Holdings" }]) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            id: 3, entity: 1, director_name: "Ada Bello", kind: "directorship", kind_display: "Directorship elsewhere",
            party: "Sable Capital", details: "", declared_on: "2026-01-10", withdrawn_on: null, is_active: true,
          },
        ]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <InterestsScreen />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getByText("Sable Capital")).toBeInTheDocument());
  expect(screen.getByText("Active")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Company / counterparty"), { target: { value: "X Ltd" } });
  fireEvent.click(screen.getByRole("button", { name: "Declare interest" }));
  await waitFor(() =>
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/interests/") && (c[1] as RequestInit)?.method === "POST")).toBe(true),
  );

  fireEvent.click(screen.getByRole("button", { name: "Withdraw" }));
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/withdraw/"))).toBe(true));
});
