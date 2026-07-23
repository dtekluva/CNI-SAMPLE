import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { DelegationMatrixScreen } from "./DelegationMatrix";

test("renders DoA tiers per category with an out-of-authority ceiling", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("/entities/")
              ? [{ id: 1, legal_name: "CNI Group Holdings Limited" }]
              : [
                  { id: 1, entity: 1, entity_name: "CNI Group Holdings Limited", category: "Capital expenditure", approver: "Managing Director", max_amount: "50000000.00", tier: 1 },
                  { id: 2, entity: 1, entity_name: "CNI Group Holdings Limited", category: "Capital expenditure", approver: "Board Finance Committee", max_amount: "250000000.00", tier: 2 },
                  { id: 3, entity: 1, entity_name: "CNI Group Holdings Limited", category: "Capital expenditure", approver: "Full Board", max_amount: "1000000000.00", tier: 3 },
                ],
          ),
      }),
    ),
  );

  render(<DelegationMatrixScreen />);
  await waitFor(() => expect(screen.getByText("Capital expenditure")).toBeInTheDocument());
  expect(screen.getByText("Managing Director")).toBeInTheDocument();
  expect(screen.getByText("Board Finance Committee")).toBeInTheDocument();
  expect(screen.getByText("₦50m")).toBeInTheDocument();
  expect(screen.getByText("₦1bn")).toBeInTheDocument();
  expect(screen.getByText("Shareholders")).toBeInTheDocument();
  expect(screen.getByText("out of authority")).toBeInTheDocument();
});
