import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AdminDashboard } from "./admin-dashboard";

describe("AdminDashboard", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads inbox assets and reports", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/admin/assets")) {
          return response(200, {
            data: [
              {
                id: 101,
                slug: "pending-asset",
                title: "검수 대기 에셋",
                description: "관리자 검수 대기",
                alt_text: "검수 대기",
                status: "inbox",
                asset_type: "image",
                download_count: 0,
              },
            ],
          });
        }
        if (url.includes("/api/v1/admin/generation-requests")) {
          return response(200, {
            data: [
            {
              id: 1,
              prompt: "업무 보고서용 미니멀 아이콘 세트",
              asset_type: "icon_set",
              provider_preference: "openai",
                status: "queued",
                admin_notes: "검수 대기",
                result_asset_id: null,
              },
            ],
          });
        }
        return response(200, {
          data: [
            {
              id: 1,
              asset_id: 101,
              asset_slug: "pending-asset",
              reason: "copyright",
              message: "저작권 확인이 필요합니다.",
              status: "open",
            },
          ],
        });
      }),
    );

    render(<AdminDashboard />);

    expect(await screen.findByText("검수 대기 에셋")).toBeInTheDocument();
    expect(await screen.findByText("저작권 확인이 필요합니다.")).toBeInTheDocument();
    expect(await screen.findByText("업무 보고서용 미니멀 아이콘 세트")).toBeInTheDocument();
    expect(screen.getByText("관리자 접근 안내")).toBeInTheDocument();
  });

  it("publishes an asset from the inbox", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "PATCH") {
        return response(200, {
          data: {
            id: 101,
            slug: "pending-asset",
            title: "검수 대기 에셋",
            description: "관리자 검수 대기",
            alt_text: "검수 대기",
            status: "published",
            asset_type: "image",
            download_count: 0,
          },
        });
      }
      if (url.includes("/api/v1/admin/assets")) {
        return response(200, {
          data: [
            {
              id: 101,
              slug: "pending-asset",
              title: "검수 대기 에셋",
              description: "관리자 검수 대기",
              alt_text: "검수 대기",
              status: "inbox",
              asset_type: "image",
              download_count: 0,
            },
          ],
        });
      }
      if (url.includes("/api/v1/admin/generation-requests")) {
        return response(200, { data: [] });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    fireEvent.click(await screen.findByRole("button", { name: "게시" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/assets/101/status",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ status: "published", reason: "관리자 게시" }),
        }),
      ),
    );
    expect(await screen.findByText("published")).toBeInTheDocument();
  });

  it("edits inbox asset metadata before publishing", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "PATCH" && url.includes("/api/v1/admin/assets/101")) {
        return response(200, {
          data: {
            id: 101,
            slug: "minimal-dashboard-reference",
            title: "미니멀 대시보드 레퍼런스",
            description: "SaaS 관리자 화면에 쓰기 좋은 이미지",
            alt_text: "밝은 배경의 미니멀 대시보드 이미지",
            status: "inbox",
            asset_type: "image",
            download_count: 0,
          },
        });
      }
      if (url.includes("/api/v1/admin/assets")) {
        return response(200, {
          data: [
            {
              id: 101,
              slug: "pending-asset",
              title: "검수 대기 에셋",
              description: "관리자 검수 대기",
              alt_text: "검수 대기",
              status: "inbox",
              asset_type: "image",
              download_count: 0,
            },
          ],
        });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    fireEvent.change(await screen.findByLabelText("제목 101"), {
      target: { value: "미니멀 대시보드 레퍼런스" },
    });
    fireEvent.change(screen.getByLabelText("슬러그 101"), {
      target: { value: "minimal-dashboard-reference" },
    });
    fireEvent.change(screen.getByLabelText("설명 101"), {
      target: { value: "SaaS 관리자 화면에 쓰기 좋은 이미지" },
    });
    fireEvent.change(screen.getByLabelText("대체 텍스트 101"), {
      target: { value: "밝은 배경의 미니멀 대시보드 이미지" },
    });
    fireEvent.click(screen.getByRole("button", { name: "메타데이터 저장 101" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/assets/101",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({
            title: "미니멀 대시보드 레퍼런스",
            slug: "minimal-dashboard-reference",
            description: "SaaS 관리자 화면에 쓰기 좋은 이미지",
            alt_text: "밝은 배경의 미니멀 대시보드 이미지",
          }),
        }),
      ),
    );
    expect(await screen.findByText("메타데이터를 저장했습니다.")).toBeInTheDocument();
  });

  it("bulk imports image assets from pasted JSON", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.includes("/api/v1/admin/assets/import")) {
        return response(201, {
          data: {
            created_count: 2,
            assets: [
              {
                id: 201,
                slug: "dashboard-hero-reference",
                title: "대시보드 히어로 레퍼런스",
                description: "SaaS 랜딩 페이지에 쓰기 좋은 히어로 이미지",
                alt_text: "밝은 배경의 SaaS 대시보드 히어로 이미지",
                status: "inbox",
                asset_type: "image",
                download_count: 0,
              },
              {
                id: 202,
                slug: "newsletter-card-reference",
                title: "뉴스레터 카드 레퍼런스",
                description: "업무 생산성 뉴스레터에 어울리는 카드 이미지",
                alt_text: "뉴스레터 카드형 레퍼런스 이미지",
                status: "inbox",
                asset_type: "image",
                download_count: 0,
              },
            ],
          },
        });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    const importItems = [
      {
        slug: "dashboard-hero-reference",
        title: "대시보드 히어로 레퍼런스",
        file_path: "/cdn/original/dashboard-hero.png",
        category: { slug: "saas", name: "SaaS" },
        tags: [{ slug: "hero", name: "히어로" }],
      },
      {
        slug: "newsletter-card-reference",
        title: "뉴스레터 카드 레퍼런스",
        file_path: "/cdn/original/newsletter-card.png",
      },
    ];
    fireEvent.change(await screen.findByLabelText("대량 등록 JSON"), {
      target: { value: JSON.stringify(importItems) },
    });
    fireEvent.click(screen.getByRole("button", { name: "대량 등록" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/assets/import",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ items: importItems }),
        }),
      ),
    );
    expect(await screen.findByText("2개 에셋을 등록했습니다.")).toBeInTheDocument();
    expect(await screen.findByText("대시보드 히어로 레퍼런스")).toBeInTheDocument();
  });

  it("generates image derivatives for an inbox asset", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.includes("/api/v1/admin/assets/101/derivatives")) {
        return response(200, {
          data: {
            id: 101,
            slug: "pending-asset",
            title: "검수 대기 에셋",
            description: "관리자 검수 대기",
            alt_text: "검수 대기",
            thumbnail_path: "/cdn/thumb/pending-asset.webp",
            preview_path: "/cdn/preview/pending-asset.webp",
            status: "inbox",
            asset_type: "image",
            download_count: 0,
          },
        });
      }
      if (url.includes("/api/v1/admin/assets")) {
        return response(200, {
          data: [
            {
              id: 101,
              slug: "pending-asset",
              title: "검수 대기 에셋",
              description: "관리자 검수 대기",
              alt_text: "검수 대기",
              status: "inbox",
              asset_type: "image",
              download_count: 0,
            },
          ],
        });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    fireEvent.click(await screen.findByRole("button", { name: "파생 이미지 생성 101" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/assets/101/derivatives",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByText("파생 이미지를 생성했습니다.")).toBeInTheDocument();
  });

  it("resolves an open report and lists audit logs", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "PATCH" && url.includes("/api/v1/admin/reports/1/status")) {
        return response(200, {
          data: {
            id: 1,
            asset_id: 101,
            asset_slug: "pending-asset",
            reason: "copyright",
            message: "저작권 확인이 필요합니다.",
            status: "resolved",
          },
        });
      }
      if (url.includes("/api/v1/admin/reports")) {
        return response(200, {
          data: [
            {
              id: 1,
              asset_id: 101,
              asset_slug: "pending-asset",
              reason: "copyright",
              message: "저작권 확인이 필요합니다.",
              status: "open",
            },
          ],
        });
      }
      if (url.includes("/api/v1/admin/audit-logs")) {
        return response(200, {
          data: [
            {
              id: 1,
              actor_user_id: 1,
              action: "asset.status_changed",
              target_type: "asset",
              target_id: 101,
              metadata: { from: "inbox", to: "published" },
            },
          ],
        });
      }
      if (url.includes("/api/v1/admin/generation-requests")) {
        return response(200, { data: [] });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    expect(await screen.findByText("asset.status_changed")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "해결" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/reports/1/status",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ status: "resolved", reason: "관리자 해결" }),
        }),
      ),
    );
    expect(await screen.findByText("resolved")).toBeInTheDocument();
  });

  it("creates a generation request from the admin queue form", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.includes("/api/v1/admin/generation-requests")) {
        return response(201, {
          data: {
            id: 1,
            prompt: "상품 상세페이지 히어로 이미지",
            asset_type: "image",
            provider_preference: "openai",
            status: "queued",
            admin_notes: "우선순위 높음",
            result_asset_id: null,
          },
        });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    fireEvent.change(await screen.findByLabelText("생성 요청"), {
      target: { value: "상품 상세페이지 히어로 이미지" },
    });
    fireEvent.change(screen.getByLabelText("운영 메모"), { target: { value: "우선순위 높음" } });
    fireEvent.click(screen.getByRole("button", { name: "요청 등록" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/generation-requests",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            prompt: "상품 상세페이지 히어로 이미지",
            asset_type: "image",
            provider_preference: "openai",
            admin_notes: "우선순위 높음",
          }),
        }),
      ),
    );
    expect(await screen.findByText("상품 상세페이지 히어로 이미지")).toBeInTheDocument();
  });

  it("runs the worker for a queued generation request", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST" && url.includes("/api/v1/admin/generation-requests/1/run")) {
        return response(200, {
          data: {
            id: 1,
            prompt: "업무 보고서용 미니멀 아이콘 세트",
            asset_type: "image",
            provider_preference: "openai",
            status: "completed",
            admin_notes: "생성 완료",
            result_asset_id: 102,
          },
        });
      }
      if (url.includes("/api/v1/admin/generation-requests")) {
        return response(200, {
          data: [
            {
              id: 1,
              prompt: "업무 보고서용 미니멀 아이콘 세트",
              asset_type: "image",
              provider_preference: "openai",
              status: "queued",
              admin_notes: null,
              result_asset_id: null,
            },
          ],
        });
      }
      return response(200, { data: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminDashboard />);

    fireEvent.click(await screen.findByRole("button", { name: "worker 실행" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/generation-requests/1/run",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByText("completed")).toBeInTheDocument();
    expect(await screen.findByText("결과 에셋 #102")).toBeInTheDocument();
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
