import { AdminDashboard } from "./admin-dashboard";

export default function AdminPage() {
  return (
    <main className="admin-page">
      <a className="simple-back" href="/">
        Vaultix
      </a>
      <section className="admin-heading">
        <p className="eyebrow">Admin</p>
        <h1>관리자 작업대</h1>
        <p>검수 대기 에셋, 신고 inbox, 게시 상태를 한 곳에서 처리합니다.</p>
      </section>
      <AdminDashboard />
    </main>
  );
}
