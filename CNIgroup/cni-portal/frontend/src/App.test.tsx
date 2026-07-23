import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import App from "./App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: "ok", service: "cni-governance-api", version: "0.1.0" }),
      }),
    ),
  );
});

test("renders the portal title", () => {
  render(<App />);
  expect(screen.getByText(/Governance Portal/i)).toBeInTheDocument();
});
