import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HealthPage from "./page";

describe("HealthPage", () => {
  it("shows the web health status", () => {
    render(<HealthPage />);

    expect(screen.getByText("Vaultix web ok")).toBeInTheDocument();
  });
});
