import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("renders the Korean MVP home shell", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: "업무용 자료, 다 만들어 두었어요." })).toBeInTheDocument();
    expect(screen.getByLabelText("자료 검색")).toBeInTheDocument();
    expect(screen.getByText("이번 주 큐레이션")).toBeInTheDocument();
    expect(screen.getByText("이미지 자산")).toBeInTheDocument();
    expect(screen.getByText("새로 추가된 자산")).toBeInTheDocument();
  });
});
