import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ session: { authenticated: true, email: "ada@cni.ng", name: "Ada Bello", mfa_verified: true } }),
}));

import { SettingsScreen } from "./Settings";

test("shows account, MFA status, and toggles a notification preference", async () => {
  const fetchMock = vi.fn((_url: string, opts?: RequestInit) => {
    if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ ok: true }) });
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) });
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<SettingsScreen />);
  await waitFor(() => expect(screen.getByText("Ada Bello")).toBeInTheDocument());
  expect(screen.getByText("MFA active")).toBeInTheDocument();

  fireEvent.click(screen.getByLabelText("Board pack published — email"));
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some((c) => String(c[0]).includes("/notifications/preferences/") && (c[1] as RequestInit)?.method === "POST"),
    ).toBe(true),
  );
});
