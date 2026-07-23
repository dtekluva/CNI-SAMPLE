import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { DocumentReader } from "./DocumentReader";

function mockFetch(docOverrides: Record<string, unknown> = {}) {
  return vi.fn((url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ id: 1 }) });
    let body: unknown = {};
    if (url.includes("/auth/session/")) body = { authenticated: true, mfa_verified: true, email: "ada@cni.test" };
    else if (url.includes("/annotations/")) body = [{ id: 7, author: 2, author_name: "Ada", page: 2, text: "prep note", visibility: "private", created_at: "2026-06-01T10:00:00Z" }];
    else if (url.includes("/content/"))
      body = { id: 5, title: "2026 Group Budget", text: "SECTION 1\nThe budget is N4.2bn.", version: 1,
               versions: [{ version_number: 1, uploaded_at: "2026-01-05T10:00:00Z", content_hash: "abc123" }],
               watermark: "Prepared for ada@cni.test" };
    else body = { id: 5, title: "2026 Group Budget", access_mode: "downloadable", topic: "Finance", committee: "",
                  page_count: 22, is_late: false, retention_until: "2033-01-01", legal_hold: false, purged: false, ...docOverrides };
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
  });
}

function renderReader() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/documents/5"]}>
        <Routes>
          <Route path="/documents/:id" element={<DocumentReader />} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

test("renders text, watermark, lifecycle panel and annotations", async () => {
  vi.stubGlobal("fetch", mockFetch());
  renderReader();
  await waitFor(() => expect(screen.getByText(/N4\.2bn/)).toBeInTheDocument());
  expect(screen.getByText("Open PDF")).toBeInTheDocument();
  expect(screen.getByText(/Prepared for ada@cni.test/)).toBeInTheDocument();
  expect(screen.getByText("Lifecycle & retention")).toBeInTheDocument();
  expect(screen.getByText("Purge")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("prep note")).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("Note"), { target: { value: "new note" } });
  fireEvent.click(screen.getByRole("button", { name: "Add note" }));
  await waitFor(() =>
    expect(vi.mocked(fetch).mock.calls.some((c) => String(c[0]).includes("/annotations/") && (c[1] as RequestInit)?.method === "POST")).toBe(true),
  );
});

test("purged document hides content and PDF", async () => {
  vi.stubGlobal("fetch", mockFetch({ purged: true }));
  renderReader();
  await waitFor(() => expect(screen.getByText("This document has been purged")).toBeInTheDocument());
  expect(screen.queryByText("Open PDF")).not.toBeInTheDocument();
});
