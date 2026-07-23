import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { DocumentsScreen } from "./Documents";

test("lists documents with access badges and downloads downloadable ones", async () => {
  const fetchMock = vi.fn((url: string) => {
    if (url.includes("/download/")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ url: "/signed", watermark: "wm" }) });
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          { id: 1, title: "Q3 Accounts", access_mode: "downloadable", committee: "", topic: "Finance" },
          { id: 2, title: "Confidential memo", access_mode: "view_only", committee: "", topic: "" },
        ]),
    });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <DocumentsScreen />
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getByText("Q3 Accounts")).toBeInTheDocument());
  expect(screen.getByText("View only")).toBeInTheDocument();
  expect(screen.getByText("Downloadable")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Download" }));
  await waitFor(() => expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/documents/1/download/"))).toBe(true));
});
