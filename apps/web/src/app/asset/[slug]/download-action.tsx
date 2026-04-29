"use client";

import { useState } from "react";

type DownloadActionProps = {
  assetId: number;
};

type DownloadState = {
  message: string | null;
  actionHref?: string;
  actionLabel?: string;
};

export function DownloadAction({ assetId }: DownloadActionProps) {
  const [state, setState] = useState<DownloadState>({ message: null });
  const [isLoading, setIsLoading] = useState(false);

  async function handleDownload() {
    setIsLoading(true);
    setState({ message: null });

    try {
      const response = await fetch(`/api/v1/downloads/${assetId}`, {
        method: "POST",
        credentials: "include",
      });
      const payload = await response.json();

      if (response.ok) {
        window.location.assign(payload.data.download_url);
        return;
      }

      if (payload.code === "unauthenticated") {
        setState({
          message: payload.detail ?? "로그인이 필요합니다.",
          actionHref: "/auth/signin",
          actionLabel: "로그인하기",
        });
        return;
      }

      if (payload.code === "email_not_verified") {
        setState({
          message: payload.detail ?? "이메일 인증 후 다운로드할 수 있습니다.",
          actionHref: "/auth/verify",
          actionLabel: "인증 확인하기",
        });
        return;
      }

      setState({ message: payload.detail ?? "다운로드를 준비하지 못했습니다. 잠시 후 다시 시도해 주세요." });
    } catch {
      setState({ message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요." });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="download-action">
      <button className="download-cta" disabled={isLoading} onClick={handleDownload} type="button">
        {isLoading ? "준비 중" : "다운로드"}
      </button>
      {state.message ? (
        <div className="download-notice" role="status">
          <p>{state.message}</p>
          {state.actionHref && state.actionLabel ? <a href={state.actionHref}>{state.actionLabel}</a> : null}
        </div>
      ) : null}
    </div>
  );
}
