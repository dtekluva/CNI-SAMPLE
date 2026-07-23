import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AnnouncementsScreen } from "./Announcements";

test("lists announcements and shows read count for leadership", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ read: true }) });
      let body: unknown = [];
      if (url.includes("/entities/")) body = [{ id: 1, legal_name: "CNI Holdings" }];
      else if (url.includes("/roles/options/")) body = { can_manage: true };
      else body = [{ id: 3, entity: 1, title: "Q3 board circular", body: "Please review the pack.", posted_by_name: "Alexa Moore", posted_at: "2026-07-10T09:00:00Z", read_by_me: true, read_count: 4 }];
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    }),
  );
  render(<AnnouncementsScreen />);
  await waitFor(() => expect(screen.getByText("Q3 board circular")).toBeInTheDocument());
  expect(screen.getByText(/Please review the pack/)).toBeInTheDocument();
  expect(screen.getByText("4 read")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "New announcement" })).toBeInTheDocument();
});
