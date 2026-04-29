import type { AssetDetail } from "../../_lib/api";

type AssetDetailViewProps = {
  asset: AssetDetail;
};

export function AssetDetailView({ asset }: AssetDetailViewProps) {
  return (
    <main className="asset-detail-page">
      <a className="simple-back" href="/explore">
        탐색으로 돌아가기
      </a>

      <section className="asset-detail-layout">
        <div className="asset-detail-preview" aria-label={asset.alt_text ?? asset.title}>
          <span>AI 생성</span>
        </div>

        <div className="asset-detail-copy">
          <p className="eyebrow">{asset.category?.name ?? "이미지 자산"}</p>
          <h1>{asset.title}</h1>
          <p>{asset.description ?? "업무용 문서와 발표자료에 바로 활용할 수 있는 이미지 자산입니다."}</p>

          <div className="asset-detail-tags">
            {asset.tags.map((tag) => (
              <a href={`/explore?tag=${tag.slug}`} key={tag.slug}>
                {tag.name}
              </a>
            ))}
          </div>

          <div className="license-summary" id="summary">
            <strong>영구 사용 가능</strong>
            <p>받은 자산은 업무와 개인 프로젝트에 자유롭게 사용할 수 있습니다. 파일 자체의 재배포만 금지됩니다.</p>
            <a href={asset.license_summary_url}>라이선스 전체 보기</a>
          </div>

          <a className="download-cta" href="/auth/signup">
            다운로드 준비 중
          </a>
          <p className="download-meta">다운로드 {asset.stats.downloads}회 · 이메일 인증 후 다운로드 흐름이 연결됩니다.</p>
        </div>
      </section>
    </main>
  );
}

