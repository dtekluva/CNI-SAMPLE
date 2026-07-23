import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { DashboardScreen } from "./Dashboard";

test("renders greeting and scoped stat summary", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("dashboard")
              ? { upcoming_meetings: 2, my_open_actions: 1, overdue_actions: 0, awaiting_my_signature: 0 }
              : url.includes("session")
                ? { authenticated: true, mfa_verified: true, email: "ada@cni.test" }
                : {},
          ),
      }),
    ),
  );

  render(
    <AuthProvider>
      <MemoryRouter>
        <DashboardScreen />
      </MemoryRouter>
    </AuthProvider>,
  );

  await waitFor(() => expect(screen.getByText(/Good day/)).toBeInTheDocument());
  await waitFor(() => expect(screen.getByText("Upcoming meetings")).toBeInTheDocument());
});
