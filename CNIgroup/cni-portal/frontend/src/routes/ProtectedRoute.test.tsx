import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";

function stubSession(session: object) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(url.includes("session") ? session : {}) }),
    ),
  );
}

function renderAt() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<ProtectedRoute><div>secret</div></ProtectedRoute>} />
          <Route path="/login" element={<div>login page</div>} />
          <Route path="/mfa" element={<div>mfa page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

test("redirects to login when unauthenticated", async () => {
  stubSession({ authenticated: false });
  renderAt();
  await waitFor(() => expect(screen.getByText("login page")).toBeInTheDocument());
});

test("redirects to mfa when authenticated but not verified", async () => {
  stubSession({ authenticated: true, mfa_verified: false, email: "a@cni.test" });
  renderAt();
  await waitFor(() => expect(screen.getByText("mfa page")).toBeInTheDocument());
});

test("renders children when authenticated + verified", async () => {
  stubSession({ authenticated: true, mfa_verified: true, email: "a@cni.test" });
  renderAt();
  await waitFor(() => expect(screen.getByText("secret")).toBeInTheDocument());
});
