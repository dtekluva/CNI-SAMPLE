import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { MeetingsScreen } from "./Meetings";

test("lists meetings with quorum", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve([
            { id: 1, title: "Q3 Board", meeting_type: "board", starts_at: "2026-07-18T10:00:00Z", quorum: 5 },
          ]),
      }),
    ),
  );

  render(
    <MemoryRouter>
      <MeetingsScreen />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getByText("Q3 Board")).toBeInTheDocument());
  expect(screen.getByText("Quorum 5")).toBeInTheDocument();
});
