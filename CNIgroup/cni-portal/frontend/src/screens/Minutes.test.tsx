import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { MinutesEditor } from "./Minutes";

test("shows minutes state and advances the workflow", async () => {
  const fetchMock = vi.fn((_url: string, opts?: RequestInit) => {
    if (opts?.method === "POST")
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ id: 1, state: "chairman_review", attendees: [], blocks: [] }) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1, state: "draft", attendees: [], blocks: [{ id: 9, agenda_item: 1, text: "Approved unanimously" }] }),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/meetings/1/minutes"]}>
      <Routes>
        <Route path="/meetings/:id/minutes" element={<MinutesEditor />} />
      </Routes>
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("draft")).toBeInTheDocument());
  expect(screen.getByText("Approved unanimously")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Advance to/ }));
  await waitFor(() =>
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/minutes/transition/") && (c[1] as RequestInit)?.method === "POST")).toBe(true),
  );
});
