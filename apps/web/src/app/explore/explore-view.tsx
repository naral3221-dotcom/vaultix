import type { AssetCard, Category } from "../_lib/api";

type ExploreViewProps = {
  categories: Category[];
  assets: AssetCard[];
  selectedCategory?: string;
};

export function ExploreView({ categories, assets, selectedCategory }: ExploreViewProps) {
  return (
    <main className="catalog-page">
      <a className="simple-back" href="/">
        Vaultix
      </a>
      <section className="catalog-heading">
        <p className="eyebrow">Explore</p>
        <h1>탐색</h1>
        <p>한국어 업무용 이미지 자산을 카테고리와 목적별로 탐색하세요.</p>
      </section>

      <div className="catalog-layout">
        <aside className="filter-panel" aria-label="카테고리 필터">
          <h2>카테고리</h2>
          <a className={!selectedCategory ? "active" : ""} href="/explore">
            전체
          </a>
          {categories.map((category) => (
            <a
              className={selectedCategory === category.slug ? "active" : ""}
              href={`/explore?category=${category.slug}`}
              key={category.slug}
            >
              {category.name}
            </a>
          ))}
        </aside>

        <section className="catalog-results" aria-label="자산 목록">
          {assets.length > 0 ? (
            <div className="api-asset-grid">
              {assets.map((asset) => (
                <a className="api-asset-card" href={`/asset/${asset.slug}`} key={asset.slug}>
                  <div className="api-asset-preview">
                    <span>AI 생성</span>
                  </div>
                  <div className="api-asset-body">
                    <h2>{asset.title}</h2>
                    <p>
                      <span>{asset.category?.name ?? "미분류"}</span>
                      <span>다운로드 {asset.stats.downloads}회</span>
                    </p>
                    <div className="asset-tags">
                      {asset.tags.map((tag) => (
                        <span key={tag.slug}>{tag.name}</span>
                      ))}
                    </div>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h2>아직 표시할 자산이 없어요.</h2>
              <p>다른 카테고리를 선택하거나 조금 뒤에 다시 확인해 주세요.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
