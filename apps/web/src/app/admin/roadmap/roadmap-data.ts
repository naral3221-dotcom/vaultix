export type PhaseStatus = "done" | "active" | "next" | "later";

export type RoadmapPhase = {
  id: string;
  title: string;
  status: PhaseStatus;
  progress: number;
  completed: string[];
  inProgress: string[];
  next: string[];
};

export const roadmapPhases: RoadmapPhase[] = [
  {
    id: "Phase 0",
    title: "VPS 기반과 배포 골격",
    status: "done",
    progress: 100,
    completed: [
      "Docker Compose, PostgreSQL, Redis, FastAPI, Next.js",
      "Tailnet nginx 접근",
      "헬스체크와 기본 CI 검증",
    ],
    inProgress: [],
    next: [],
  },
  {
    id: "Phase 1",
    title: "공개 카탈로그와 계정/다운로드 MVP",
    status: "done",
    progress: 100,
    completed: [
      "공개 에셋 API와 탐색/상세 화면",
      "회원가입, 로그인, 이메일 인증, 비밀번호 재설정",
      "단일 사용 다운로드 링크와 파일 서빙",
      "Resend/Turnstile/일회용 이메일 차단",
    ],
    inProgress: [],
    next: [],
  },
  {
    id: "Phase 2",
    title: "관리자 운영",
    status: "active",
    progress: 80,
    completed: [
      "관리자 role과 ADMIN_EMAILS",
      "Google OAuth 로그인",
      "에셋 검수/게시 상태 변경",
      "신고 처리와 감사 로그",
    ],
    inProgress: ["관리자 UX 정리", "관리자 접근 안내"],
    next: ["에셋 생성 요청 큐"],
  },
  {
    id: "Phase 3",
    title: "AI 생성 파이프라인",
    status: "next",
    progress: 10,
    completed: ["이미지 라우팅 정책 확정"],
    inProgress: [],
    next: [
      "Nanobanana -> OpenAI gpt-image-2",
      "Celery 작업 큐",
      "프롬프트 템플릿과 결과 검수",
      "썸네일/WebP 변환",
    ],
  },
  {
    id: "Phase 4",
    title: "SEO와 운영 안정화",
    status: "later",
    progress: 0,
    completed: [],
    inProgress: [],
    next: ["sitemap/robots/ImageObject JSON-LD", "Sentry/Plausible", "백업과 모니터링"],
  },
];

export const roadmapSummary = {
  current: "현재 진행: Phase 2 관리자 운영",
  nextDecision: "다음 큰 결정: 관리자 UX 정리를 마친 뒤 에셋 생성 파이프라인으로 넘어갈지 확정",
};
