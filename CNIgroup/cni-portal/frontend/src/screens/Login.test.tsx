import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { Login } from "./Login";

function renderLogin() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/mfa" element={<div>mfa page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

test("submits credentials and routes to /mfa on success", async () => {
  const fetchMock = vi.fn((url: string) => {
    if (url.includes("login")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ email: "a" }) });
    if (url.includes("session"))
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ authenticated: true, mfa_verified: false }) });
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
  });
  vi.stubGlobal("fetch", fetchMock);
  renderLogin();

  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@cni.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "pw-strong-123" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(screen.getByText("mfa page")).toBeInTheDocument());
  expect(fetchMock.mock.calls.some((c) => String(c[0]).includes("/auth/login/"))).toBe(true);
});

test("shows an error on bad credentials", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      url.includes("login")
        ? Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({ detail: "no" }) })
        : Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(url.includes("session") ? { authenticated: false } : {}) }),
    ),
  );
  renderLogin();

  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@cni.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(screen.getByText(/Invalid email or password/)).toBeInTheDocument());
});
