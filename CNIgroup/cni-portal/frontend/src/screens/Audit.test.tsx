import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AuditScreen } from "./Audit";

test("lists audit events and filters by action", async () => {
  const fetchMock = vi.fn((_url: string, _opts?: RequestInit) =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1, action: "resolution.signed", actor: 1, timestamp: "2026-07-12T09:00:00Z" }]),
    }),
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<AuditScreen />);
  await waitFor(() => expect(screen.getByText("resolution.signed")).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("Filter by action"), { target: { value: "resolution.signed" } });
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("action=resolution.signed"))).toBe(true));
});

test("folds consecutive same-action events with count and span, expands on click", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve([
            { id: 12, action: "minutes.state_changed", actor: 1, timestamp: "2026-07-19T23:46:41Z" },
            { id: 11, action: "minutes.state_changed", actor: 1, timestamp: "2026-07-19T23:10:00Z" },
            { id: 10, action: "minutes.state_changed", actor: 1, timestamp: "2026-07-19T22:46:41Z" },
            { id: 9, action: "auth.login", actor: 1, timestamp: "2026-07-19T22:00:00Z" },
          ]),
      }),
    ),
  );
  render(<AuditScreen />);
  await waitFor(() => expect(screen.getByText("minutes.state_changed")).toBeInTheDocument());
  expect(screen.getByText("3 events")).toBeInTheDocument();
  // folded by default — individual rows hidden
  expect(screen.queryByText("#11")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { expanded: false }));
  await waitFor(() => expect(screen.getByText("#11")).toBeInTheDocument());
  // the single login event stays flat
  expect(screen.getByText("auth.login")).toBeInTheDocument();
});
