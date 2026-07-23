import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { Mfa } from "./Mfa";

function renderMfa() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/mfa"]}>
        <Routes>
          <Route path="/mfa" element={<Mfa />} />
          <Route path="/" element={<div>home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

test("enrols on mount, verifies, and routes home", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("enroll")) return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ config_url: "otpauth://totp/xyz" }) });
      if (url.includes("verify")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ status: "verified" }) });
      if (url.includes("session")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ authenticated: true, mfa_verified: true }) });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
  );
  renderMfa();

  await waitFor(() => expect(screen.getByLabelText("MFA enrolment QR code")).toBeInTheDocument());
  fireEvent.change(screen.getByLabelText("Authentication code"), { target: { value: "123456" } });
  fireEvent.click(screen.getByText("Verify"));
  await waitFor(() => expect(screen.getByText("home")).toBeInTheDocument());
});

test("shows an error on invalid code", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("enroll")) return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ config_url: "otpauth://x" }) });
      if (url.includes("verify")) return Promise.resolve({ ok: false, status: 400, json: () => Promise.resolve({ detail: "Invalid token." }) });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(url.includes("session") ? { authenticated: true, mfa_verified: false } : {}) });
    }),
  );
  renderMfa();

  fireEvent.change(screen.getByLabelText("Authentication code"), { target: { value: "000000" } });
  fireEvent.click(screen.getByText("Verify"));
  await waitFor(() => expect(screen.getByText(/Invalid code/)).toBeInTheDocument());
});
