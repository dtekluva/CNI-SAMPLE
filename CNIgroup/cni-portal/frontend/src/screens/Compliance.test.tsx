import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { ComplianceScreen } from "./Compliance";

const OBLIGATION = {
  id: 1, entity: 1, entity_name: "Liberty Pay Limited", title: "CBN PSP Licence Renewal", regulator: "CBN",
  frequency: "annual", due_date: "2026-08-05", description: "Annual renewal of the payment licence.",
  rag: "amber",
  last_filing: { id: 4, period_label: "FY2025", filed_on: "2025-08-01", evidence: "CBN/ACK/2025/114", filed_by_name: "Alexa Moore" },
};

test("calendar shows RAG summary and opens the filing modal", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "POST")
        return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ filing: {}, next_due: "2027-08-05", rag: "green" }) });
      if (url.includes("/filings/"))
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve([{ id: 4, period_label: "FY2025", filed_on: "2025-08-01", evidence: "CBN/ACK/2025/114", filed_by_name: "Alexa Moore" }]),
        });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([OBLIGATION]) });
    }),
  );

  render(<ComplianceScreen />);
  await waitFor(() => expect(screen.getByText("CBN PSP Licence Renewal")).toBeInTheDocument());
  expect(screen.getByText("Due within 30 days")).toBeInTheDocument();
  expect(screen.getAllByText(/due in \d+d/).length).toBeGreaterThan(0);

  fireEvent.click(screen.getByRole("button", { name: "View" }));
  await waitFor(() => expect(screen.getByText("Filing history")).toBeInTheDocument());
  expect(screen.getByText("FY2025")).toBeInTheDocument();
  expect(screen.getByText("CBN/ACK/2025/114")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Period"), { target: { value: "FY2026" } });
  fireEvent.click(screen.getByRole("button", { name: /Record filing/ }));
  await waitFor(() =>
    expect(vi.mocked(fetch).mock.calls.some((c) => String(c[0]).includes("/filings/") && (c[1] as RequestInit)?.method === "POST")).toBe(true),
  );
});
