import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DownloadAction } from "./download-action";

describe("DownloadAction", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("requests a signed download URL and navigates on success", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { assign });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(201, {
          data: { download_url: "/dl/101/signed", expires_in_seconds: 300 },
        }),
      ),
    );

    render(<DownloadAction assetId={101} />);

    fireEvent.click(screen.getByRole("button", { name: "다운로드" }));

    await waitFor(() => expect(assign).toHaveBeenCalledWith("/dl/101/signed"));
  });

  it("shows a login action when the API requires authentication", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(401, {
          code: "unauthenticated",
          detail: "로그인이 필요합니다.",
        }),
      ),
    );

    render(<DownloadAction assetId={101} />);

    fireEvent.click(screen.getByRole("button", { name: "다운로드" }));

    expect(await screen.findByText("로그인이 필요합니다.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "로그인하기" })).toHaveAttribute("href", "/auth/signin");
  });

  it("shows a retry message when the download limit is exceeded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(429, {
          code: "rate_limit_exceeded",
          detail: "시간당 30회 다운로드 한도를 초과했습니다.",
        }),
      ),
    );

    render(<DownloadAction assetId={101} />);

    fireEvent.click(screen.getByRole("button", { name: "다운로드" }));

    expect(await screen.findByText("시간당 30회 다운로드 한도를 초과했습니다.")).toBeInTheDocument();
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
