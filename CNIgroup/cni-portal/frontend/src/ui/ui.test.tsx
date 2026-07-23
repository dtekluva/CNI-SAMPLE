import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Badge, Button, Card, CardBody, Field } from "./index";

test("Button applies its variant class", () => {
  render(<Button variant="danger">Revoke</Button>);
  expect(screen.getByText("Revoke")).toHaveClass("ns-btn--danger");
});

test("Badge renders with tone and label", () => {
  render(<Badge tone="success">Approved</Badge>);
  expect(screen.getByText("Approved")).toBeInTheDocument();
});

test("Card + CardBody render children", () => {
  render(
    <Card>
      <CardBody>Body content</CardBody>
    </Card>,
  );
  expect(screen.getByText("Body content")).toBeInTheDocument();
});

test("Field shows label and error, marks input invalid", () => {
  render(<Field label="Notice period" error="Below the statutory minimum" />);
  const input = screen.getByLabelText("Notice period");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByText("Below the statutory minimum")).toBeInTheDocument();
});
