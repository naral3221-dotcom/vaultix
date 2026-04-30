import { roadmapPhases, roadmapSummary } from "./roadmap-data";

export default function RoadmapPage() {
  return (
    <main className="admin-page">
      <a className="simple-back" href="/admin">
        관리자
      </a>
      <section className="admin-heading">
        <p className="eyebrow">Roadmap</p>
        <h1>개발 로드맵</h1>
        <p>{roadmapSummary.current}</p>
      </section>

      <section className="roadmap-summary" aria-label="로드맵 요약">
        <strong>{roadmapSummary.nextDecision}</strong>
      </section>

      <section className="roadmap-board" aria-label="phase별 개발 진행상황">
        {roadmapPhases.map((phase) => (
          <article className={`roadmap-card ${phase.status}`} key={phase.id}>
            <div className="roadmap-card-header">
              <div>
                <span>{phase.id}</span>
                <h2>{phase.title}</h2>
              </div>
              <strong>{phase.progress}%</strong>
            </div>
            <div className="roadmap-meter" aria-label={`${phase.id} 진행률 ${phase.progress}%`}>
              <span style={{ width: `${phase.progress}%` }} />
            </div>
            <RoadmapList title="완료" items={phase.completed} emptyText="아직 없음" />
            <RoadmapList title="진행 중" items={phase.inProgress} emptyText="대기" />
            <RoadmapList title="다음" items={phase.next} emptyText="없음" />
          </article>
        ))}
      </section>
    </main>
  );
}

function RoadmapList({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <div className="roadmap-list">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{emptyText}</p>
      )}
    </div>
  );
}
