"use client";

import { useEffect, useState } from "react";

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

type LoadState = "idle" | "loading" | "ready" | "error";

export function AdminDashboard() {
  const [assets, setAssets] = useState<AdminAsset[]>([]);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [state, setState] = useState<LoadState>("idle");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadAdminData();
  }, []);

  async function loadAdminData() {
    setState("loading");
    setMessage(null);
    try {
      const [assetPayload, reportPayload] = await Promise.all([
        getAdminJson<{ data: AdminAsset[] }>("/api/v1/admin/assets?status=inbox"),
        getAdminJson<{ data: AdminReport[] }>("/api/v1/admin/reports"),
      ]);
      setAssets(assetPayload.data);
      setReports(reportPayload.data);
      setState("ready");
    } catch {
      setMessage("관리자 데이터를 불러오지 못했습니다.");
      setState("error");
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

  return (
    <div className="admin-dashboard">
      {message ? <p className="admin-message">{message}</p> : null}
      {state === "loading" ? <p className="admin-muted">불러오는 중</p> : null}

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
            </div>
          ))}
          {state === "ready" && reports.length === 0 ? <p className="admin-muted">열린 신고가 없습니다.</p> : null}
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
