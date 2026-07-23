import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { ActionsScreen } from "./Actions";

test("lists actions and completes one", async () => {
  const fetchMock = vi.fn((_url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ id: 1, status: "done" }) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1, title: "Follow up with auditors", owner_name: "Emeka (CFO)", due_date: "2026-08-01", status: "open" }]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<ActionsScreen />);
  await waitFor(() => expect(screen.getByText("Follow up with auditors")).toBeInTheDocument());
  expect(screen.getByText("open")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Complete" }));
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/actions/1/complete/"))).toBe(true));
});
