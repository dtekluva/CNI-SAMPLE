import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { CommitteesScreen } from "./Committees";

const COMMITTEE = {
  id: 1, entity: 1, entity_name: "CNI Group Holdings Limited", name: "Audit Committee",
  charter: "TOR: oversee financial reporting and the external audit.", charter_adopted_on: "2026-01-15",
  reports_count: 1,
  memberships: [
    { id: 1, user: 2, user_name: "Folake Balogun", role: "chair", term_start: "2025-01-01", term_end: "2026-09-01", ended_on: null, is_active: true, expires_soon: true },
    { id: 2, user: 3, user_name: "Kelechi Eze", role: "member", term_start: "2025-01-01", term_end: null, ended_on: null, is_active: true, expires_soon: false },
  ],
};

test("committee cards show chair, terms; detail reveals charter and reports", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("/reports/")
              ? [{ id: 9, title: "Q2 Audit Committee Report", summary: "No material findings.", status: "submitted", submitted_by_name: "Folake Balogun", submitted_at: "2026-06-30T10:00:00Z", noted_at: null }]
              : [COMMITTEE],
          ),
      }),
    ),
  );

  render(<CommitteesScreen />);
  await waitFor(() => expect(screen.getByText("Audit Committee")).toBeInTheDocument());
  expect(screen.getByText(/Chair: Folake Balogun/)).toBeInTheDocument();
  expect(screen.getByText("1 term expiring")).toBeInTheDocument();

  fireEvent.click(screen.getByText("Audit Committee"));
  await waitFor(() => expect(screen.getByText(/oversee financial reporting/)).toBeInTheDocument());
  await waitFor(() => expect(screen.getByText("Q2 Audit Committee Report")).toBeInTheDocument());
  expect(screen.getByText("Term expiring")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Note" })).toBeInTheDocument();
});
