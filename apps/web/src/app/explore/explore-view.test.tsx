import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExploreView } from "./explore-view";

describe("ExploreView", () => {
  it("renders categories and API-backed assets", () => {
    render(
      <ExploreView
        categories={[
          { id: 1, slug: "business", name: "비즈니스" },
          { id: 2, slug: "report", name: "보고서" },
        ]}
        assets={[
          {
            id: 101,
            slug: "business-meeting-illustration",
            title: "비즈니스 미팅 일러스트",
            alt_text: "회의 장면",
            thumbnail_url: "/cdn/thumb/business-meeting.webp",
            preview_url: "/cdn/preview/business-meeting.webp",
            category: { id: 1, slug: "business", name: "비즈니스" },
            tags: [{ slug: "meeting", name: "미팅" }],
            stats: { downloads: 42, favorites: 0 },
          },
        ]}
      />,
    );

    expect(screen.getByRole("heading", { name: "탐색" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "비즈니스" })).toHaveAttribute(
      "href",
      "/explore?category=business",
    );
    expect(screen.getByRole("link", { name: /비즈니스 미팅 일러스트/ })).toHaveAttribute(
      "href",
      "/asset/business-meeting-illustration",
    );
    expect(screen.getByText("다운로드 42회")).toBeInTheDocument();
  });
});

