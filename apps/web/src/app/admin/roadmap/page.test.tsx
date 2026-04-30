import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RoadmapPage from "./page";

describe("RoadmapPage", () => {
  it("renders the current phase roadmap with completion, active, and next work", () => {
    render(<RoadmapPage />);

    expect(screen.getByRole("heading", { name: "개발 로드맵" })).toBeInTheDocument();
    expect(screen.getByText("현재 진행: Phase 2 관리자 운영")).toBeInTheDocument();
    expect(screen.getByText("Phase 0")).toBeInTheDocument();
    expect(screen.getByText("Phase 1")).toBeInTheDocument();
    expect(screen.getByText("Phase 2")).toBeInTheDocument();
    expect(screen.getByText("Phase 3")).toBeInTheDocument();
    expect(screen.getByText("신고 처리와 감사 로그")).toBeInTheDocument();
    expect(screen.getByText("Google OAuth")).toBeInTheDocument();
    expect(screen.getByText("Nanobanana -> OpenAI gpt-image-2")).toBeInTheDocument();
  });
});
