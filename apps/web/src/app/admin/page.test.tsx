import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("./admin-dashboard", () => ({
  AdminDashboard: () => <div>Admin dashboard</div>,
}));

import AdminPage from "./page";

describe("AdminPage", () => {
  it("renders the admin workspace shell", () => {
    render(<AdminPage />);

    expect(screen.getByRole("heading", { name: "관리자 작업대" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "로드맵" })).toHaveAttribute("href", "/admin/roadmap");
  });
});
