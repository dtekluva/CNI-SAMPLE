import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { MeetingWorkspace } from "./MeetingWorkspace";

test("shows meeting title, quorum, and agenda", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      let body: unknown = {};
      if (url.includes("/agenda/")) body = [{ id: 9, title: "Q3 accounts", item_type: "approval", position: 0 }];
      else if (url.includes("/quorum/")) body = { present: 5, quorum: 5, met: true };
      else body = { id: 1, title: "Q3 Board", starts_at: "2026-07-18T10:00:00Z", meeting_type: "board" };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    }),
  );

  render(
    <MemoryRouter initialEntries={["/meetings/1"]}>
      <Routes>
        <Route path="/meetings/:id" element={<MeetingWorkspace />} />
      </Routes>
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Q3 Board")).toBeInTheDocument());
  await waitFor(() => expect(screen.getByText("Quorum 5 / 5")).toBeInTheDocument());
  await waitFor(() => expect(screen.getByText("Q3 accounts")).toBeInTheDocument());
});
