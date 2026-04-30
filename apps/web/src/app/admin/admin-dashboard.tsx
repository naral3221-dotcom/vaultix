"use client";

import { FormEvent, useEffect, useState } from "react";

type AdminAsset = {
  id: number;
  slug: string;
  title: string;
  status: string;
  asset_type: string;
  download_count: number;
};

type AdminReport = {
  id: number;
  asset_id: number;
  asset_slug: string;
  reason: string;
  message: string | null;
  status: string;
};

type AuditLog = {
  id: number;
  actor_user_id: number | null;
  action: string;
  target_type: string;
  target_id: number;
  metadata: Record<string, unknown> | null;
};

type GenerationRequest = {
  id: number;
  prompt: string;
  asset_type: string;
  provider_preference: string | null;
  status: string;
  admin_notes: string | null;
  result_asset_id: number | null;
};

type LoadState = "idle" | "loading" | "ready" | "error";

export function AdminDashboard() {
  const [assets, setAssets] = useState<AdminAsset[]>([]);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [generationRequests, setGenerationRequests] = useState<GenerationRequest[]>([]);
  const [state, setState] = useState<LoadState>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [generationPrompt, setGenerationPrompt] = useState("");
  const [generationNotes, setGenerationNotes] = useState("");
  const [isCreatingGenerationRequest, setIsCreatingGenerationRequest] = useState(false);

  useEffect(() => {
    void loadAdminData();
  }, []);

  async function loadAdminData() {
    setState("loading");
    setMessage(null);
    try {
      const [assetPayload, reportPayload, auditPayload, generationPayload] = await Promise.all([
        getAdminJson<{ data: AdminAsset[] }>("/api/v1/admin/assets?status=inbox"),
        getAdminJson<{ data: AdminReport[] }>("/api/v1/admin/reports"),
        getAdminJson<{ data: AuditLog[] }>("/api/v1/admin/audit-logs"),
        getAdminJson<{ data: GenerationRequest[] }>("/api/v1/admin/generation-requests"),
      ]);
      setAssets(assetPayload.data);
      setReports(reportPayload.data);
      setAuditLogs(auditPayload.data);
      setGenerationRequests(generationPayload.data);
      setState("ready");
    } catch {
      setMessage("관리자 데이터를 불러오지 못했습니다.");
      setState("error");
    }
  }

  async function resolveReport(reportId: number) {
    setMessage(null);
    try {
      const payload = await getAdminJson<{ data: AdminReport }>(`/api/v1/admin/reports/${reportId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "resolved", reason: "관리자 해결" }),
      });
      setReports((current) => current.map((report) => (report.id === reportId ? payload.data : report)));
      setMessage("신고를 해결 처리했습니다.");
    } catch {
      setMessage("신고 처리에 실패했습니다.");
    }
  }

  async function publishAsset(assetId: number) {
    setMessage(null);
    try {
      const payload = await getAdminJson<{ data: AdminAsset }>(`/api/v1/admin/assets/${assetId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "published", reason: "관리자 게시" }),
      });
      setAssets((current) => current.map((asset) => (asset.id === assetId ? payload.data : asset)));
      setMessage("게시 상태로 변경했습니다.");
    } catch {
      setMessage("상태 변경에 실패했습니다.");
    }
  }

  async function createGenerationRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = generationPrompt.trim();
    if (prompt.length < 8) {
      setMessage("생성 요청은 8자 이상 입력해 주세요.");
      return;
    }
    setIsCreatingGenerationRequest(true);
    setMessage(null);
    try {
      const payload = await getAdminJson<{ data: GenerationRequest }>("/api/v1/admin/generation-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          asset_type: "image",
          provider_preference: "nanobanana",
          admin_notes: generationNotes.trim() || null,
        }),
      });
      setGenerationRequests((current) => [payload.data, ...current]);
      setGenerationPrompt("");
      setGenerationNotes("");
      setMessage("생성 요청을 큐에 등록했습니다.");
    } catch {
      setMessage("생성 요청 등록에 실패했습니다.");
    } finally {
      setIsCreatingGenerationRequest(false);
    }
  }

  async function startGenerationRequest(requestId: number) {
    setMessage(null);
    try {
      const payload = await getAdminJson<{ data: GenerationRequest }>(
        `/api/v1/admin/generation-requests/${requestId}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "processing", admin_notes: "작업 시작" }),
        },
      );
      setGenerationRequests((current) =>
        current.map((request) => (request.id === requestId ? payload.data : request)),
      );
      setMessage("생성 요청을 처리 중으로 변경했습니다.");
    } catch {
      setMessage("생성 요청 상태 변경에 실패했습니다.");
    }
  }

  return (
    <div className="admin-dashboard">
      {message ? <p className="admin-message">{message}</p> : null}
      {state === "loading" ? <p className="admin-muted">불러오는 중</p> : null}

      <section className="admin-access-panel" aria-label="관리자 접근 안내">
        <div>
          <h2>관리자 접근 안내</h2>
          <p>Google OAuth 또는 이메일 로그인 후 `ADMIN_EMAILS`에 등록된 계정만 이 작업대를 사용할 수 있습니다.</p>
        </div>
        <a href="/admin/roadmap">로드맵 보기</a>
      </section>

      <section className="admin-section" aria-label="에셋 검수">
        <div className="admin-section-heading">
          <h2>에셋 검수</h2>
          <button type="button" onClick={loadAdminData}>
            새로고침
          </button>
        </div>
        <div className="admin-table">
          {assets.map((asset) => (
            <div className="admin-row" key={asset.id}>
              <div>
                <strong>{asset.title}</strong>
                <span>{asset.slug}</span>
              </div>
              <span>{asset.status}</span>
              <span>{asset.asset_type}</span>
              <span>{asset.download_count}</span>
              <button type="button" onClick={() => publishAsset(asset.id)}>
                게시
              </button>
            </div>
          ))}
          {state === "ready" && assets.length === 0 ? <p className="admin-muted">검수 대기 에셋이 없습니다.</p> : null}
        </div>
      </section>

      <section className="admin-section" aria-label="생성 요청 큐">
        <div className="admin-section-heading">
          <h2>생성 요청 큐</h2>
        </div>
        <form className="admin-generation-form" onSubmit={createGenerationRequest}>
          <label htmlFor="generation-prompt">생성 요청</label>
          <textarea
            id="generation-prompt"
            name="generation-prompt"
            onChange={(event) => setGenerationPrompt(event.target.value)}
            required
            rows={3}
            value={generationPrompt}
          />
          <label htmlFor="generation-notes">운영 메모</label>
          <input
            id="generation-notes"
            name="generation-notes"
            onChange={(event) => setGenerationNotes(event.target.value)}
            value={generationNotes}
          />
          <button type="submit" disabled={isCreatingGenerationRequest}>
            {isCreatingGenerationRequest ? "등록 중" : "요청 등록"}
          </button>
        </form>
        <div className="admin-table">
          {generationRequests.map((request) => (
            <div className="admin-row generation-row" key={request.id}>
              <div>
                <strong>{request.prompt}</strong>
                <span>{request.admin_notes ?? "메모 없음"}</span>
              </div>
              <span>{request.asset_type}</span>
              <span>{request.provider_preference ?? "auto"}</span>
              <span>{request.status}</span>
              <button type="button" onClick={() => startGenerationRequest(request.id)}>
                처리 시작
              </button>
            </div>
          ))}
          {state === "ready" && generationRequests.length === 0 ? (
            <p className="admin-muted">대기 중인 생성 요청이 없습니다.</p>
          ) : null}
        </div>
      </section>

      <section className="admin-section" aria-label="신고 inbox">
        <div className="admin-section-heading">
          <h2>신고 inbox</h2>
        </div>
        <div className="admin-table">
          {reports.map((report) => (
            <div className="admin-row" key={report.id}>
              <div>
                <strong>{report.asset_slug}</strong>
                <span>{report.message ?? "메시지 없음"}</span>
              </div>
              <span>{report.reason}</span>
              <span>{report.status}</span>
              <button type="button" onClick={() => resolveReport(report.id)}>
                해결
              </button>
            </div>
          ))}
          {state === "ready" && reports.length === 0 ? <p className="admin-muted">열린 신고가 없습니다.</p> : null}
        </div>
      </section>

      <section className="admin-section" aria-label="감사 로그">
        <div className="admin-section-heading">
          <h2>감사 로그</h2>
        </div>
        <div className="admin-table">
          {auditLogs.map((log) => (
            <div className="admin-row" key={log.id}>
              <div>
                <strong>{log.action}</strong>
                <span>{log.target_type}</span>
              </div>
              <span>{log.target_id}</span>
              <span>{log.actor_user_id ?? "system"}</span>
              <span>{formatMetadata(log.metadata)}</span>
            </div>
          ))}
          {state === "ready" && auditLogs.length === 0 ? <p className="admin-muted">감사 로그가 없습니다.</p> : null}
        </div>
      </section>
    </div>
  );
}

async function getAdminJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: "same-origin", ...init });
  if (!response.ok) {
    throw new Error(`Vaultix admin API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

function formatMetadata(metadata: Record<string, unknown> | null): string {
  if (!metadata) {
    return "-";
  }
  return Object.entries(metadata)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(", ");
}
