import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { DirectorProfile } from "./DirectorProfile";

test("shows full director details: BVN, document and contact", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            id: 7, entity: 1, entity_name: "CNI Group Holdings Limited", name: "Chief Adaeze Okonkwo",
            designation: "Chairman", appointed: "2018-08-01", ceased_on: null, active: true,
            date_of_birth: "1962-04-18", nationality: "Nigerian", occupation: "Company Director",
            bvn: "22110000101", document_type: "International Passport", document_number: "A08123456",
            document_expiry: "2030-06-30", residential_address: "4 Bourdillon Road, Ikoyi, Lagos",
            email: "chairman@cnigroup.demo", phone: "+234 803 100 0001",
            other_directorships: ["Sable Capital Partners"], shares: 8000000, share_class: "ordinary",
          }),
      }),
    ),
  );
  render(
    <MemoryRouter initialEntries={["/directors/7"]}>
      <Routes>
        <Route path="/directors/:id" element={<DirectorProfile />} />
      </Routes>
    </MemoryRouter>,
  );
  await waitFor(() => expect(screen.getAllByText("Chief Adaeze Okonkwo").length).toBeGreaterThan(0));
  expect(screen.getByText("22110000101")).toBeInTheDocument();
  expect(screen.getByText("International Passport")).toBeInTheDocument();
  expect(screen.getByText("A08123456")).toBeInTheDocument();
  expect(screen.getByText("4 Bourdillon Road, Ikoyi, Lagos")).toBeInTheDocument();
  expect(screen.getByText("Sable Capital Partners")).toBeInTheDocument();
  expect(screen.getByText(/8,000,000/)).toBeInTheDocument();
});
