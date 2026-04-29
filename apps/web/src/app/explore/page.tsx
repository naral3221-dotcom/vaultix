import { PublicPageShell } from "../_components/public-page-shell";

export default function ExplorePage() {
  return (
    <PublicPageShell
      eyebrow="Explore"
      title="탐색"
      description="한국어 업무용 이미지 자산을 카테고리와 목적별로 탐색하는 공간입니다."
    >
      <div className="placeholder-grid">
        {["비즈니스", "마케팅", "보고서", "SNS", "채용", "교육"].map((item) => (
          <a className="placeholder-card" href="/explore" key={item}>
            {item}
          </a>
        ))}
      </div>
    </PublicPageShell>
  );
}

