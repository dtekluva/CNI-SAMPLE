import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AgendaBuilder } from "./AgendaBuilder";

test("lists items and posts a new one on add", async () => {
  const fetchMock = vi.fn((_url: string, opts?: RequestInit) => {
    if (opts?.method === "POST")
      return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ id: 2, title: "New item", item_type: "noting", position: 1 }) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1, title: "Apologies", item_type: "noting", position: 0 }]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<AgendaBuilder meetingId={1} />);
  await waitFor(() => expect(screen.getByText("Apologies")).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("New agenda item"), { target: { value: "New item" } });
  fireEvent.click(screen.getByRole("button", { name: "Add" }));

  await waitFor(() =>
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/agenda/") && (c[1] as RequestInit)?.method === "POST")).toBe(true),
  );
});
