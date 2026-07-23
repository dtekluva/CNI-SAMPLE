import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { InterestDetail } from "./InterestDetail";

test("shows the full declaration with record card", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("/entities/")
              ? [{ id: 1, legal_name: "CNI Holdings" }]
              : {
                  id: 3, entity: 1, director_name: "Ada Bello", kind: "directorship",
                  kind_display: "Directorship elsewhere", party: "Sable Capital Partners",
                  details: "Non-executive chair of Sable Capital Partners, a private equity firm with holdings in payments infrastructure.",
                  declared_on: "2026-01-10", withdrawn_on: null, is_active: true, created_at: "2026-01-10T09:00:00Z",
                },
          ),
      }),
    ),
  );
  render(
    <MemoryRouter initialEntries={["/interests/3"]}>
      <Routes>
        <Route path="/interests/:id" element={<InterestDetail />} />
      </Routes>
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getAllByText("Sable Capital Partners").length).toBeGreaterThan(0));
  expect(screen.getByText(/private equity firm/)).toBeInTheDocument();
  expect(screen.getAllByText("Directorship elsewhere").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Active").length).toBeGreaterThan(0);
  expect(screen.getByRole("button", { name: "Withdraw" })).toBeInTheDocument();
});
