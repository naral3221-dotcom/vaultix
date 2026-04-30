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
                status: "inbox",
                asset_type: "image",
                download_count: 0,
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
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
