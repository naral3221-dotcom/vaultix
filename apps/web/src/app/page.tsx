export default function HomePage() {
  const curatedCollections = [
    "보고서용 비즈니스 그래픽",
    "PPT 배경 이미지",
    "SNS 카드뉴스 소재",
    "이력서 첫인상 세트",
  ];

  const contentTypes = ["이미지 자산", "PPT 템플릿", "SVG 인포그래픽", "이력서 DOCX", "아이콘 세트", "AI 제작 가이드"];

  const recentAssets = [
    { title: "회의실 발표 장면", tone: "indigo" },
    { title: "분기 성과 그래프", tone: "amber" },
    { title: "마케팅 플랜 보드", tone: "sky" },
    { title: "채용 공고 배너", tone: "emerald" },
    { title: "프로젝트 일정표", tone: "rose" },
    { title: "고객 여정 지도", tone: "slate" },
  ];

  return (
    <main className="site-shell">
      <header className="site-header" aria-label="Vaultix 주요 탐색">
        <a className="wordmark" href="/">
          Vaultix
        </a>
        <nav className="desktop-nav" aria-label="주요 메뉴">
          <a href="/explore">탐색</a>
          <a href="/today">오늘의 큐레이션</a>
          <a href="/log">운영 일지</a>
          <a href="/newsletter">뉴스레터</a>
        </nav>
        <div className="header-actions">
          <a className="ghost-link" href="/auth/login">
            로그인
          </a>
          <a className="primary-link" href="/auth/signup">
            회원가입
          </a>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">AI 생성 · 영구 사용권 · 한국어 우선</p>
          <h1>업무용 자료, 다 만들어 두었어요.</h1>
          <p className="hero-description">
            AI가 만든 이미지와 업무용 에셋을 무료로 받고, 어떤 프롬프트와 흐름으로 만들었는지도 함께 확인하세요.
          </p>

          <form className="search-panel" action="/search">
            <label className="sr-only" htmlFor="home-search">
              자료 검색
            </label>
            <input id="home-search" name="q" placeholder="어떤 자료가 필요하신가요?" />
            <button type="submit">검색</button>
          </form>

          <div className="quick-keywords" aria-label="추천 검색어">
            {["발표자료", "인포그래픽", "보고서 이미지", "SNS 카드"].map((keyword) => (
              <a href={`/search?q=${encodeURIComponent(keyword)}`} key={keyword}>
                {keyword}
              </a>
            ))}
          </div>
        </div>

        <div className="hero-visual" aria-label="Vaultix 자산 미리보기">
          <div className="visual-toolbar">
            <span>신규 이미지</span>
            <strong>AI 생성</strong>
          </div>
          <div className="visual-grid">
            {recentAssets.slice(0, 4).map((asset, index) => (
              <div className={`visual-tile tone-${asset.tone}`} key={asset.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{asset.title}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-band" aria-labelledby="curation-heading">
        <div className="section-heading">
          <p className="eyebrow">Curated</p>
          <h2 id="curation-heading">이번 주 큐레이션</h2>
        </div>
        <div className="collection-grid">
          {curatedCollections.map((title) => (
            <a className="collection-card" href="/today" key={title}>
              <span>{title}</span>
              <small>업무에 바로 쓰기 좋은 묶음</small>
            </a>
          ))}
        </div>
      </section>

      <section className="content-band muted-band" aria-labelledby="type-heading">
        <div className="section-heading">
          <p className="eyebrow">Asset Types</p>
          <h2 id="type-heading">컨텐츠 타입별</h2>
        </div>
        <div className="type-grid">
          {contentTypes.map((type) => (
            <a className="type-card" href="/explore" key={type}>
              {type}
            </a>
          ))}
        </div>
      </section>

      <section className="content-band" aria-labelledby="recent-heading">
        <div className="section-heading split-heading">
          <div>
            <p className="eyebrow">Recently Added</p>
            <h2 id="recent-heading">새로 추가된 자산</h2>
          </div>
          <a className="text-link" href="/explore">
            더 보기
          </a>
        </div>
        <div className="asset-grid">
          {recentAssets.map((asset) => (
            <article className="asset-card" key={asset.title}>
              <div className={`asset-preview tone-${asset.tone}`}>
                <span>AI 생성</span>
              </div>
              <h3>{asset.title}</h3>
              <p>다운로드 준비 중 · Phase 1 샘플</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="site-footer">
        <p>© 2026 Vaultix. AI 생성 콘텐츠 / 영구 사용 가능 / 재배포 금지</p>
        <nav aria-label="푸터 메뉴">
          <a href="/license">라이선스</a>
          <a href="/privacy">Privacy</a>
          <a href="/about">About</a>
          <a href="/contact">Contact</a>
        </nav>
      </footer>
    </main>
  );
}
