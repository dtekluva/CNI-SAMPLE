import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { GroupScreen } from "./Group";

test("group rollup shows per-entity rows and a total", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            entities: [
              { entity: 1, entity_name: "CNI Holdings", meetings: 5, upcoming: 1, open_actions: 3, overdue_actions: 1, pending_resolutions: 2, compliance_red: 1 },
              { entity: 2, entity_name: "Liberty Pay", meetings: 2, upcoming: 0, open_actions: 1, overdue_actions: 0, pending_resolutions: 1, compliance_red: 0 },
            ],
            totals: { meetings: 7, upcoming: 1, open_actions: 4, overdue_actions: 1, pending_resolutions: 3, compliance_red: 1 },
          }),
      }),
    ),
  );
  render(<GroupScreen />);
  await waitFor(() => expect(screen.getByText("CNI Holdings")).toBeInTheDocument());
  expect(screen.getByText("Liberty Pay")).toBeInTheDocument();
  expect(screen.getByText("Group total")).toBeInTheDocument();
});
