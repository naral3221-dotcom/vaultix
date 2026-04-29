import { PublicPageShell } from "../_components/public-page-shell";

export default function ReportPage() {
  return (
    <PublicPageShell
      eyebrow="Report"
      title="신고하기"
      description="권리 침해, 부적절한 자산, 라이선스 문제가 의심되는 콘텐츠를 신고하는 페이지입니다."
    >
      <form className="stacked-form">
        <label htmlFor="report-url">문제가 있는 URL</label>
        <input id="report-url" placeholder="https://vaultix.example.com/asset/..." />
        <label htmlFor="report-detail">신고 내용</label>
        <textarea id="report-detail" rows={5} placeholder="확인해야 할 내용을 적어주세요." />
        <button type="submit">신고 접수</button>
      </form>
    </PublicPageShell>
  );
}
