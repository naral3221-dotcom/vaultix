import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AssetDetailView } from "./asset-detail-view";

describe("AssetDetailView", () => {
  it("renders asset detail, license summary, and download action", () => {
    render(
      <AssetDetailView
        asset={{
          id: 101,
          slug: "business-meeting-illustration",
          title: "비즈니스 미팅 일러스트",
          description: "보고서와 발표자료에 쓰기 좋은 회의 장면 이미지입니다.",
          alt_text: "회의 장면",
          preview_url: "/cdn/preview/business-meeting.webp",
          thumbnail_url: "/cdn/thumb/business-meeting.webp",
          license_summary_url: "/license#summary",
          category: { id: 1, slug: "business", name: "비즈니스" },
          tags: [{ slug: "meeting", name: "미팅" }],
          stats: { downloads: 42, favorites: 0 },
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "비즈니스 미팅 일러스트" })).toBeInTheDocument();
    expect(screen.getByText("영구 사용 가능")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "다운로드 준비 중" })).toHaveAttribute(
      "href",
      "/auth/signup",
    );
  });
});

