import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { NotificationsScreen } from "./Notifications";

test("shows in-portal inbox and marks read", async () => {
  const fetchMock = vi.fn((_url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ read: true }) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          { id: 1, event_type: "pack.published", channel: "in_portal", subject: "Q3 pack published", body: "Open the pack", read: false },
        ]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<NotificationsScreen />);
  await waitFor(() => expect(screen.getByText("Q3 pack published")).toBeInTheDocument());
  expect(screen.getByText("New")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Mark read" }));
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/notifications/1/read/"))).toBe(true));
});
