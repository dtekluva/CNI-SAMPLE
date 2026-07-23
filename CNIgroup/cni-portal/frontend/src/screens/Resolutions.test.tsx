import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { ResolutionsScreen } from "./Resolutions";

test("lists resolutions and votes", async () => {
  const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ for: 1 }) });
    if (url.includes("/results/"))
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ mode: "open", tally: { for: 2, against: 1, abstain: 0, recused: 0 }, total_votes: 3, ballots: [] }),
      });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          { id: 1, entity: 1, number: "CNI/BD/2026/014", title: "Approve Q3 accounts", outcome: "pending", kind: "board",
            voting_mode: "open", text: "THAT the Q3 accounts be and are hereby approved.", threshold: 0,
            effective_date: null, created_at: "2026-07-01T10:00:00Z" },
        ]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<ResolutionsScreen />);
  await waitFor(() => expect(screen.getByText("Approve Q3 accounts")).toBeInTheDocument());
  expect(screen.getByText("CNI/BD/2026/014")).toBeInTheDocument();
  expect(screen.getByText("pending")).toBeInTheDocument();

  // "Vote" opens a compact modal; then choose For
  fireEvent.click(screen.getByRole("button", { name: "Vote" }));
  await waitFor(() => expect(screen.getByText(/How do you vote/)).toBeInTheDocument());
  fireEvent.click(screen.getByRole("button", { name: "Vote for" }));
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/resolutions/1/vote/"))).toBe(true));

  // clicking the row opens the full-resolution modal with text and tally
  fireEvent.click(screen.getByText("Approve Q3 accounts"));
  await waitFor(() => expect(screen.getByText(/hereby approved/)).toBeInTheDocument());
  await waitFor(() => expect(screen.getByText(/3 votes cast/)).toBeInTheDocument());
  fireEvent.click(screen.getByLabelText("Close"));
  await waitFor(() => expect(screen.queryByText(/hereby approved/)).not.toBeInTheDocument());
});
