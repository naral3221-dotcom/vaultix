# Phase 4 — Tier 2 컨텐츠 + 최적화 상세 기획서

> **목적**: Tier 2 컨텐츠(노션/엑셀/HTML/컬러링북)로 카탈로그 다양성 확보, 인프라 최적화(R2 이전·캐싱·검색), A/B 테스트로 핵심 깔때기 개선, 추가 언어(중·스) 확장. 손익분기 도달 + 운영 자동화 80% 달성.
> **선행**: Phase 3 §7 진입 조건 모두 통과 / AdSense 승인 / 월 PV 5,000+
> **작성일**: 2026-04-27

---

## 1. 목표 & 완료 조건

### 1.1 목표

1. **Tier 2 컨텐츠 4종 추가**: 노션/Obsidian, 엑셀, HTML 랜딩, 컬러링북·워크시트
2. **추가 언어**: 중국어 간체(zh-CN), 스페인어(es) — DeepL 자동 번역으로 long-tail
3. **R2 스토리지 이전**: 50GB 도달 시 (또는 사전 준비)
4. **A/B 테스트 시스템 도입**: 핵심 깔때기 1~2개 최적화
5. **윈백·재참여 캠페인**: 30일 비활성 사용자
6. **운영 자동화 80%+**: 큐레이션 인박스 자동 승인 임계 도입, 정기 백업·복원·보고서 자동화
7. **손익분기**: 월 광고+제휴 수익 ≥ 인프라·외부 API 비용

### 1.2 완료 조건 (체크리스트)

**컨텐츠 타입**
- [ ] 노션/Obsidian 템플릿 마크다운 생성 워커 + 일 2~3개 발행
- [ ] 엑셀 템플릿 (openpyxl) 워커 + 수식 검증 + 일 1~2개 발행
- [ ] HTML 랜딩 페이지 (Tailwind) 워커 + Puppeteer 빌드 검증 + 일 1~2개 발행
- [ ] 컬러링북 워커 (SDXL line art) + 일 3~5개 발행
- [ ] 8개 컨텐츠 타입 동시 운영 (이미지/PPT/SVG/DOCX/노션/엑셀/HTML/컬러링북)

**추가 언어**
- [ ] zh-CN, es UI 번역 (DeepL 1차 + 사람 검수)
- [ ] 신규 자산 메타데이터 5개 언어 자동 번역 (ko/en/ja/zh-CN/es)
- [ ] 기존 자산 백필 번역
- [ ] hreflang 5언어 출력

**스토리지**
- [ ] Cloudflare R2 셋업 + 액세스 키 관리
- [ ] assets/published 디렉토리 → R2 마이그레이션 (백그라운드)
- [ ] 다운로드는 nginx → R2 signed URL 리다이렉트
- [ ] 로컬 디스크 25GB+ 확보 후 검증

**A/B 테스트**
- [ ] Alembic 0012: `ab_experiments`, `ab_assignments`
- [ ] /api/v1/ab/{key} 엔드포인트
- [ ] 첫 실험: 자산 카드 hover 액션 (즉시 다운로드 vs 즐겨찾기 우선)
- [ ] 두번째 실험: 회원가입 모달 카피 (B1 §3.2)

**운영 자동화**
- [ ] 큐레이션 자동 승인 정책: 점수 0.85+ + 카테고리 매칭 자동 승인 옵션
- [ ] 주간 운영 리포트 자동 생성 (Telegram 일요일 발송)
- [ ] 백업 복원 자동 검증 (월 1회 별도 PG에 복원 → 행 수 비교)
- [ ] 의존성 자동 업데이트 PR (Renovate auto-merge minor)
- [ ] 윈백 캠페인 (D+30 비활성 → "이런 자산이 새로 추가됐어요" 메일)

**KPI**
- [ ] 월 광고+제휴 수익 ≥ 운영비
- [ ] MAU 5,000+
- [ ] 운영 시간 주 4시간 이하 (큐레이션 자동화 효과)

---

## 2. 작업 분해 (WBS)

> W1~W8은 묶음 단위 + 의존성 순서일 뿐 일정 약속이 아닙니다 (D-9).

### W1 — 노션/Obsidian 템플릿

- [ ] **1.1** noton 템플릿 5종 (회의록 / 프로젝트 트래커 / 독서 노트 / 주간 리뷰 / GTD)
- [ ] **1.2** Obsidian용 마크다운 + 콜아웃 + 데이터뷰 변형
- [ ] **1.3** 노션 템플릿 = .md 파일 (사용자가 노션에 import) + 미리보기 PNG
- [ ] **1.4** 큐레이션 인박스에 마크다운 미리보기 (rendered HTML 표시)
- [ ] **1.5** prompt_templates 시드 15개

### W2 — 엑셀 템플릿

- [ ] **2.1** openpyxl 워커
- [ ] **2.2** 카테고리: 가계부 / 사업체 매출 추적 / 분기 KPI / OKR / 재고 관리
- [ ] **2.3** LLM이 시나리오 + 컬럼 + 수식 JSON 생성 → openpyxl로 빌드
- [ ] **2.4** 검증: 수식 평가 (formulas 라이브러리 또는 LibreOffice headless)
- [ ] **2.5** 미리보기: LibreOffice → PNG (시트 1~3장)
- [ ] **2.6** 다운로드: .xlsx + .csv (단순 데이터만)

### W3 — HTML 랜딩 페이지

- [ ] **3.1** Tailwind CDN 기반 단일 HTML
- [ ] **3.2** 카테고리: SaaS 랜딩 / 이벤트 / 포트폴리오 / 컨퍼런스 / 식당 메뉴
- [ ] **3.3** LLM이 섹션 구조 JSON → 빌드
- [ ] **3.4** 검증: Puppeteer로 빌드 + 스크린샷 + Lighthouse 빠른 진단 (성능 ≥ 80)
- [ ] **3.5** 다운로드: .html + assets.zip

### W4 — 컬러링북·워크시트

- [ ] **4.1** SDXL/Flux line art LoRA 적용 워크플로우
- [ ] **4.2** ComfyUI 워크플로우 추가: outline 스타일 (검정 선만)
- [ ] **4.3** 후처리: Pillow로 검정-흰색만 남기기 (저지연 outline 강제)
- [ ] **4.4** 카테고리: 동물 / 풍경 / 만다라 / 캐릭터 / 글자 워크시트
- [ ] **4.5** 다운로드: PNG + PDF (인쇄용 A4 200dpi)

### W5 — 추가 언어 zh-CN, es

- [ ] **5.1** next-intl messages: zh-CN, es 추가
- [ ] **5.2** UI 번역 (DeepL 1차 + 중국어/스페인어 가능 지인 검수)
- [ ] **5.3** asset_translations 백필 (기존 자산 5만개 + 신규)
- [ ] **5.4** hreflang 5개 + sitemap 5개
- [ ] **5.5** Plausible로 해당 언어 트래픽 모니터 (의미 있어야 유지, 의미 없으면 backlog)

### W6 — Cloudflare R2 이전

- [ ] **6.1** R2 버킷 생성 + 액세스 키
- [ ] **6.2** rclone로 `published/` → R2 동기화 (점진적, 1시간 단위)
- [ ] **6.3** boto3 어댑터 작성 (S3 호환)
- [ ] **6.4** 다운로드 흐름 변경: signed URL을 R2 URL로 발급 (만료 5분 그대로)
- [ ] **6.5** 핫링크 차단을 R2에서 (CORS·Referer)
- [ ] **6.6** 점진 전환: 신규 자산은 R2 직행, 기존 자산은 30일 마이그레이션
- [ ] **6.7** 마이그레이션 완료 후 로컬 `published/` 삭제 (충분한 검증 후)

### W7 — A/B 테스트 시스템

- [ ] **7.1** Alembic 0012 적용
- [ ] **7.2** /api/v1/ab/{key} + 클라이언트 훅 (`useExperiment("asset_card_v2")`)
- [ ] **7.3** 첫 실험 셋업: 자산 카드 hover 액션 변형
- [ ] **7.4** 결과 대시보드 (어드민)
- [ ] **7.5** 실험 종료 룰: 통계 유의성 또는 4주 한도 도달

### W8 — 운영 자동화 + 윈백 + 회고

- [ ] **8.1** 자동 승인 정책 (점수 0.85+ + 카테고리 매칭): 옵션 활성화
- [ ] **8.2** 주간 운영 리포트 자동 생성 (Telegram 일요일 18:00):
  - 신규 가입 / 다운로드 / 자동 발행 자산 / 큐레이션 처리 시간 / 광고 수익 / 외부 API 비용 / 비정상 알림
- [ ] **8.3** 백업 복원 자동 검증: 월 1회 cron, 별도 PG로 복원, row count 비교, 알림
- [ ] **8.4** Renovate 룰 강화: minor·patch auto-merge, major는 PR
- [ ] **8.5** 윈백 캠페인: D+30 비활성 사용자 대상 "이런 자산이 새로 추가됐어요" Listmonk 캠페인
- [ ] **8.6** Phase 5 진입 전 회고

---

## 3. 기술 결정사항

### 3.1 결정 1 — R2 마이그레이션 트리거

**선택**: **35GB 도달 시 사전 시작** (50GB 한도 전 여유)

| 옵션 | 장점 | 단점 |
|------|------|------|
| 35GB 사전 ⭐ | 여유 마이그레이션 | 약간의 ops 부담 |
| 50GB 도달 시 | 마지막까지 미루기 | 디스크 가득 시 다운타임 위험 |

### 3.2 결정 2 — 노션 템플릿 형식

**선택**: **마크다운 .md 파일** (노션 import 호환)

- 사용자: 노션에서 "Import → Markdown" 드래그 드롭
- 옵션: 노션 API로 직접 페이지 생성 (사용자 OAuth 필요) — Phase 5 검토

### 3.3 결정 3 — A/B 테스트 통계 기준

**선택**: **베이지안 + 4주 한도**

- frequentist p-value 0.05 도달 또는 4주 경과 시 종료
- 둘 다 안 되면 winner 없이 control 유지

### 3.4 결정 4 — 자동 승인 임계

**선택**: **점수 0.85+ AND 카테고리 자동 분류 신뢰도 0.8+**

- 임계 미달은 인박스 그대로
- 자동 승인은 admin_audit_logs에 'auto.approve'로 기록
- JH가 주간 리포트에서 자동 승인 결과 검토 가능

### 3.5 결정 5 — Tier 2 발행 비중

**선택**: **이미지 50% / 그 외 합계 50%**

- 트래픽이 모이는 건 여전히 이미지가 가장 큼
- Tier 2는 차별화·SEO long-tail용

---

## 4. 코드/설정 골격

### 4.1 R2 어댑터

```python
# apps/api/src/vaultix_api/adapters/r2.py
import boto3
from botocore.client import Config
from vaultix_api.settings import settings


_session = boto3.session.Session()
_s3 = _session.client(
    "s3",
    endpoint_url=settings.r2_endpoint,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def upload(local_path: str, key: str, *, content_type: str = "image/webp"):
    _s3.upload_file(
        local_path, settings.r2_bucket, key,
        ExtraArgs={"ContentType": content_type, "CacheControl": "public, max-age=2592000, immutable"}
    )


def signed_url(key: str, *, expires: int = 300, filename: str | None = None) -> str:
    params = {"Bucket": settings.r2_bucket, "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return _s3.generate_presigned_url("get_object", Params=params, ExpiresIn=expires)
```

### 4.2 다운로드 핸들러 변경 (R2 리다이렉트)

```python
@router.get("/dl/{asset_id}/{nonce}")
async def download_file(asset_id: int, nonce: str, ...):
    # ... nonce·만료·시그니처 검증 ...
    asset = db.get(Asset, asset_id)

    if asset.storage == "r2":
        from vaultix_api.adapters.r2 import signed_url
        url = signed_url(f"published/original/{asset.id}.png", expires=300, filename=f"{asset.slug}.png")
        # downloads UPSERT는 별도 트랜잭션
        await record_download(asset, request.state.user, request.client.host)
        return RedirectResponse(url, status_code=302)
    else:  # local
        return Response(headers={
            "X-Accel-Redirect": f"/assets/raw/{asset.file_path}",
            "Content-Disposition": f'attachment; filename="{filename}"',
        })
```

### 4.3 A/B 훅 (Next.js)

```ts
// apps/web/src/lib/use-experiment.ts
"use client";
import { useEffect, useState } from "react";

export function useExperiment(key: string) {
  const [variant, setVariant] = useState<string | null>(null);
  useEffect(() => {
    fetch(`/api/v1/ab/${key}`).then(r => r.json()).then(d => setVariant(d.data.variant));
  }, [key]);
  return variant;
}

// 사용 예
function AssetCard({ asset }) {
  const variant = useExperiment("asset_card_v2");
  if (variant === "treatment") return <AssetCardV2 asset={asset} />;
  return <AssetCardV1 asset={asset} />;
}
```

### 4.4 주간 리포트 (Telegram)

```python
# apps/api/src/vaultix_api/services/weekly_report.py
def build_weekly_report(db, week_start, week_end) -> str:
    new_users = db.scalar(select(func.count()).select_from(User).where(User.created_at.between(week_start, week_end)))
    downloads = db.scalar(select(func.count()).select_from(Download).where(Download.downloaded_at.between(week_start, week_end)))
    published = db.scalar(select(func.count()).select_from(Asset).where(Asset.published_at.between(week_start, week_end)))
    inbox_remaining = db.scalar(select(func.count()).select_from(Asset).where(Asset.status == 'inbox'))
    spend = calc_monthly_spend(db)

    return f"""📊 vaultix 주간 리포트
{week_start:%Y-%m-%d} ~ {week_end:%Y-%m-%d}

신규 가입:  {new_users:,}명
다운로드:   {downloads:,}건
자동 발행:  {published:,}장 (일평균 {published//7})
인박스:     {inbox_remaining}장 대기

이번 달 외부 API 비용: ${spend:.2f} / $50

상세: https://vaultix.example.com/admin
"""
```

### 4.5 .env 추가분

```dotenv
# Phase 4
R2_ENDPOINT=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=vaultix-assets
ASSET_STORAGE_DEFAULT=r2     # local | r2 — 신규 자산 저장 위치

AUTO_APPROVE_THRESHOLD=0.85
AUTO_APPROVE_CAT_CONFIDENCE=0.8
```

---

## 5. 테스트 계획

### 5.1 R2 마이그레이션 테스트

| 시나리오 | 검증 |
|---------|------|
| 새 자산 R2 직행 | bucket에 파일 도착 |
| 다운로드 → R2 redirect → 파일 정상 | 200 + 파일 크기 일치 |
| 5분 만료 후 같은 URL 재요청 | 403 |
| 핫링크 차단 (다른 도메인 referer) | 403 |
| 마이그레이션 진행 중 다운로드 (local 자산) | 정상 |

### 5.2 8개 타입 동시 운영

- 인박스에서 8개 타입 모두 표시·승인 가능
- 검색 시 type 필터로 분류 정확

### 5.3 A/B 일관성

- 같은 사용자(또는 anon_id)에 항상 같은 variant
- 변형 간 사용자 비율 50/50 (±5%)

### 5.4 자동 승인 정책 검증

- 점수 0.86 + 카테고리 신뢰도 0.85 → 자동 승인 → 발행 큐
- 점수 0.84 → 인박스 대기

---

## 6. 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|------|
| R2 마이그레이션 중 파일 손실 | 低 | 高 | 원본을 로컬에 30일 보존 후 삭제, 무결성 hash 검증 |
| R2 비용 발생 (이전 무료라도 PUT 비용) | 低 | 低 | 월 사용량 모니터, $5/월 예산 |
| 자동 승인 정책 폭주 (저질 자동 발행) | 中 | 中 | 첫 2주는 자동 승인 OFF, 점수 분포 분석 후 활성화 |
| Tier 2 사용자 수요 불확실 | 中 | 中 | 분석으로 인기 타입만 강화, 비인기는 발행 줄임 |
| 추가 언어 트래픽 0 | 中 | 低 | DeepL 비용만 약간, 부담 적음 |
| HTML 랜딩 LLM 빌드 실패율 | 中 | 中 | Puppeteer 검증, 실패 자산 폐기 |
| Renovate auto-merge가 운영 중단 유발 | 中 | 中 | minor만 auto, 매주 검토 30분 |
| A/B 실험 결과 해석 오류 | 中 | 低 | 4주 한도 + 베이지안 + 결과 보고서 자동화 |

---

## 7. Phase 5 진입 조건

- [ ] §1.2 완료 조건 모든 체크박스 ✅
- [ ] 손익분기 (월 수익 ≥ 운영비)
- [ ] MAU 5,000+
- [ ] 8개 컨텐츠 타입 동시 운영 4주 안정
- [ ] R2 이전 완료
- [ ] 운영 시간 주 4시간 이하 4주 연속
- [ ] 첫 A/B 실험 결과 도출 + 적용

---

## 8. 다음 액션

1. Phase 3 §7 진입 조건 충족 시 본 W1 착수
2. R2 마이그레이션(W6)은 디스크 35GB 도달 알림이 오면 다른 W보다 우선 진행
3. 운영 자동화(W8)는 다른 W에서 발견된 반복 패턴을 모아 한꺼번에 처리

