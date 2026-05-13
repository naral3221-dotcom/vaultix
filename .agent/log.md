<!-- 마지막 회전: 없음 -->

## [2026-05-14 04:24:07 KST] session-start | /agent-init 으로 .agent/ 초기화
- 프로젝트 타입: monorepo (apps/api FastAPI + apps/web Next.js + infra)
- 위키 섹션: README, overview, architecture, domain, modules, dependencies, decisions, conventions, glossary (9개)
- 시드 출처: README.md, docs/ROADMAP.md, 구현시작_README.md, 기획서/00_INDEX.md, 기획서/00_IMPLEMENTATION_SPEC_v0.4.md, 기획서/A7_LLM_라우팅_정책.md, apps/api/pyproject.toml, apps/web/package.json, git log -20
- 백업 대상 없음 (.claude/ 부재, 신규 초기화 모드)

## [2026-05-14 04:24:07 KST] decision | Phase 3 이미지 공급 파이프라인 활성 상태로 컨텍스트 고정
- 이유: ROADMAP.md 가 Phase 3 = 85% Active 로 명시. 다음 마일스톤은 `OPENAI_API_KEY` 프로덕션 설정 + 생성 자산 저장 확인.
- 영향: 후속 작업의 디폴트 Phase 컨텍스트는 Phase 3. MVP 범위(Phase 0+1) 와 별개로, *현재 진행 중* 은 Phase 3 임을 state.md 에 반영.

## [2026-05-14 04:30:00 KST] decision | vault 를 디폴트 origin 으로 채택, GitHub 은 백업으로 강등
- 사용자 명시: "왠만해서는 깃허브 안 쓸 거고 vault 쓸 거".
- 액션: `git remote rename origin github` + `git remote add origin http://100.116.156.37:9006/jh97/vaultix.git` + `git push -u origin main`.
- 영향: 향후 모든 `git push` 의 디폴트 = vault. GitHub 으로의 push 는 명시 요청 시에만 `git push github main`. 자동 미러 cron 은 forge setup 스크립트로 별도 설치 가능 (`rules/vault.md`).

## [2026-05-14 04:42:00 KST] file-edit | README.md 갱신 + 루트 VERSION 신설
- README.md: Repository 표 (vault primary / github backup), Version/Phase 헤더, "Start here" 우선순위 정렬, OpenClaw Gateway 룰 명시, Versioning 섹션 추가.
- VERSION: `0.1.0` (apps/api · apps/web 과 동기화). MVP 완료 시 `1.0.0` 으로 bump 예정.
- 이유: vault 웹 UI 첫 페이지 가독성 + 모노레포 버전 단일 진실 공급원 확립.
