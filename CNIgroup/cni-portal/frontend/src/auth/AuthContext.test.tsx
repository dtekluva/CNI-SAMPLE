import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";

function Probe() {
  const { session, ready } = useAuth();
  if (!ready) return <div>loading</div>;
  return <div>{session?.authenticated ? `hi ${session.email}` : "anon"}</div>;
}

test("exposes the session from /auth/session/", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("session")
              ? { authenticated: true, email: "ada@cni.test", mfa_verified: true }
              : {},
          ),
      }),
    ),
  );

  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );
  await waitFor(() => expect(screen.getByText("hi ada@cni.test")).toBeInTheDocument());
});
