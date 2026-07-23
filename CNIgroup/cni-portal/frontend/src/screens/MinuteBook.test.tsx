import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { MinuteBookScreen } from "./MinuteBook";

test("lists sealed minutes, shows integrity band, verifies a seal", async () => {
  const fetchMock = vi.fn((url: string) =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve(
          url.includes("/integrity/")
            ? { audit_chain: { intact: true, events: 240 }, sealed_minutes: [{ id: 1, intact: true }], all_intact: true }
            : url.includes("/verify/")
              ? { stored: "abc", current: "abc", intact: true }
              : url.includes("/entities/")
                ? [{ id: 1, legal_name: "CNI Holdings" }]
                : [
                    {
                      id: 1, state: "signed", content_hash: "a1b2c3d4e5f60718", signed_at: "2026-04-02T12:00:00Z",
                      signed_by_name: "Inyang Inyangete", meeting_title: "Q1 2026 Board Meeting",
                      meeting_date: "2026-03-24T10:00:00Z", entity: 1, entity_name: "CNI Group Holdings Limited",
                    },
                  ],
        ),
    }),
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<MinuteBookScreen />);
  await waitFor(() => expect(screen.getByText("Q1 2026 Board Meeting")).toBeInTheDocument());
  expect(screen.getByText("Record integrity verified")).toBeInTheDocument();
  expect(screen.getByText(/Signed by Inyang Inyangete/)).toBeInTheDocument();
  expect(screen.getByText("Open PDF")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Verify seal" }));
  await waitFor(() => expect(screen.getByText(/seal intact/)).toBeInTheDocument());
});
