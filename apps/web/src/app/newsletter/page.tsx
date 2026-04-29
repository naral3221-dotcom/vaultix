import { PublicPageShell } from "../_components/public-page-shell";

export default function NewsletterPage() {
  return (
    <PublicPageShell
      eyebrow="Newsletter"
      title="뉴스레터"
      description="새 자산, 제작 워크플로우, 업무용 AI 팁을 주 1회 받아볼 수 있도록 준비 중입니다."
    >
      <form className="inline-form">
        <label className="sr-only" htmlFor="newsletter-email">
          이메일
        </label>
        <input id="newsletter-email" type="email" placeholder="you@example.com" />
        <button type="submit">구독하기</button>
      </form>
    </PublicPageShell>
  );
}

