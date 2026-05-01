import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RoadmapPage from "./page";

describe("RoadmapPage", () => {
  it("renders the current phase roadmap with completion, active, and next work", () => {
    render(<RoadmapPage />);

    expect(screen.getByRole("heading", { name: "개발 로드맵" })).toBeInTheDocument();
    expect(screen.getByText("현재 진행: Phase 3 이미지 공급 파이프라인")).toBeInTheDocument();
    expect(screen.getByText("Phase 0")).toBeInTheDocument();
    expect(screen.getByText("Phase 1")).toBeInTheDocument();
    expect(screen.getByText("Phase 2")).toBeInTheDocument();
    expect(screen.getByText("Phase 3")).toBeInTheDocument();
    expect(screen.getByText("신고 처리와 감사 로그")).toBeInTheDocument();
    expect(screen.getByText("Google OAuth 로그인")).toBeInTheDocument();
    expect(screen.getByText("생성 요청 큐 -> inbox 에셋 worker 연결")).toBeInTheDocument();
    expect(screen.getByText("OpenAI GPT Image provider 호출부")).toBeInTheDocument();
    expect(screen.getByText("관리자 에셋 메타데이터 편집")).toBeInTheDocument();
    expect(screen.getByText("이미지 대량 등록/import")).toBeInTheDocument();
    expect(screen.getByText("썸네일/WebP 변환")).toBeInTheDocument();
  });
});
