import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { AppShell } from "./AppShell";

test("shell renders the nav and current user", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(url.includes("entities") ? [] : { authenticated: true, mfa_verified: true, email: "ada@cni.test" }),
      }),
    ),
  );

  render(
    <AuthProvider>
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>
    </AuthProvider>,
  );

  expect(screen.getByText("Board Meetings")).toBeInTheDocument();
  expect(screen.getByText("Resolutions")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("ada@cni.test")).toBeInTheDocument());
});
