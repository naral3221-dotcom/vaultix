# A3 — 이미지 생성 라우팅 + 데스크탑 ComfyUI 특수 워커 설계

> **목적**: 외부 API(Nanobanana / OpenAI `gpt-image-2`)를 1·2차 메인으로 두고, 데스크탑 ComfyUI를 **특수 워크플로우 전용 보조 워커**로 운영하는 시스템 설계.
> **선행 결정**: D-1(원본) → **D-14(우선)**, A7 LLM 라우팅 정책
> **작성일**: 2026-04-27 (v0.4 갱신)
> **변경 요약**: v0.3은 "ComfyUI 1차 + Replicate 폴백" 구조였음. JH 4개사 무제한 API 키 보유 + 데스크탑 항시 가동 불가가 확인되어, **ComfyUI를 특수 워크플로우 보조로 격하**하고 일반 자산 생성은 외부 API가 담당.

---

## 0. 핵심 변경 요약 (v0.3 → v0.4)

| 항목 | v0.3 | v0.4 |
|------|------|------|
| 1차 (메인) | 데스크탑 ComfyUI | **Nanobanana API** |
| 2차 (폴백) | Replicate / fal.ai | **OpenAI `gpt-image-2` API** |
| 3차 | (없음) | **데스크탑 ComfyUI (특수 워크플로우 전용)** |
| ComfyUI 가동 가정 | 24/7 (전기료 감수) | 가변 (JH 사용 시간만) |
| ComfyUI 큐 | 일반 자산 50장/일 | 특수 워크플로우 0~20장/일 (가용 시) |
| 외부 API 비용 캡 | $50/월 | 없음 (무제한 키) — 호출량 추적만 |
| Ollama 의존 | 메타데이터 단계에서 사용 | **폐기** (A7 D-13) |

---

## 1. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│   VPS (main-hub)                                                │
│                                                                 │
│   ┌────────────────┐     ┌────────────────┐                     │
│   │  vaultix-api    │────→│  vaultix-redis  │                     │
│   │  (FastAPI)     │     │  (Celery 큐)    │                     │
│   └────────┬───────┘     └────────┬───────┘                     │
│            │                      │                             │
│            │ enqueue              │ pop                         │
│            ↓                      ↓                             │
│   ┌──────────────────────────────────────────────────┐          │
│   │  Celery 워커 풀                                   │          │
│   │  ─ image_primary    (외부 API → Nanobanana)        │          │
│   │  ─ image_secondary  (외부 API → gpt-image-2)        │          │
│   │  ─ image_special    (ComfyUI 전용 — 특수 워크플로우) │          │
│   │  ─ image_post       (검증·점수·메타·인박스)         │          │
│   └────┬──────────────────┬──────────────────┬───────┘          │
│        │                  │                  │                  │
└────────┼──────────────────┼──────────────────┼──────────────────┘
         │ HTTPS            │ HTTPS            │ Tailscale
         ↓                  ↓                  ↓
  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐
  │ Nanobanana  │   │ GPT Image    │   │ 데스크탑        │
  │ API (외부)   │   │ 2.0 API      │   │ ComfyUI :8188  │
  └──────┬──────┘   └──────┬───────┘   │ (AMD R9700)    │
         │                 │           │ — 가용 시간만   │
         └─────────┬───────┘           └───────┬────────┘
                   │                           │
                   │ 결과 PNG bytes              │ 결과 PNG file
                   ↓                           ↓
        ┌────────────────────────────────────────────────┐
        │ VPS  /var/lib/vaultix/assets/raw/               │
        │  → image_post 큐: 검증 → 점수 → 메타 → 인박스    │
        └────────────────────────────────────────────────┘
```

### 1.1 핵심 설계 결정 (v0.4)

| 결정 | 내용 | 이유 |
|------|------|------|
| **외부 API 1·2차 메인** | Nanobanana → OpenAI `gpt-image-2` | JH 무제한 키 보유 + 안정성·속도 |
| **ComfyUI는 보조** | 특수 워크플로우(ControlNet/LoRA/일관성)만 처리 | 데스크탑 항시 가동 불가, 외부 API로 처리 어려운 차별화 작업만 |
| **워커는 VPS에 둠** | (v0.3 동일) | 큐/재시도/DB 접근/메타 처리는 VPS에서 |
| **ComfyUI HTTP API 직접 사용** | (v0.3 동일) | 한 단계 줄이면 장애점 ↓ |
| **Tailscale로 직접 호출** | (v0.3 동일) | 보안. 데스크탑 방화벽·DDNS 불필요 |
| **3개 큐 분리** | `image_primary`(Nanobanana), `image_secondary`(`gpt-image-2`), `image_special`(ComfyUI) | 각 큐별로 동시성·재시도·라우팅 정책 다름 |
| **결과 저장은 VPS 디스크** | 모든 출처의 PNG는 `/var/lib/vaultix/assets/raw/`로 즉시 저장 | (v0.3 동일) |
| **ComfyUI 수면 모드** | 헬스 down이면 `image_special` 큐는 작업을 **대기**(폐기 X) | JH가 데스크탑 켜면 자동 재개 |

---

## 2. 라우팅 정책

### 2.1 작업 종류와 큐 라우팅

| 작업 종류 | 라우팅 | 비고 |
|----------|--------|------|
| 일반 자산 생성 (단일 이미지) | `image_primary` (Nanobanana) | 일 50~200장 |
| 1차 실패·품질 미달 | `image_secondary` (`gpt-image-2`) | 자동 승격 |
| 같은 캐릭터 시리즈 12장 | `image_special` (ComfyUI) | 데스크탑 가용 시만 |
| ControlNet 포즈 강제 | `image_special` | 동일 |
| 한국 일러스트 LoRA 스타일 | `image_special` | 동일 |
| 부분 인페인팅 (큐레이션 후 보정) | `image_special` | 동일 |

### 2.2 자동 승격 규칙 (1차 → 2차)

다음 조건 하나라도 만족 시 같은 작업을 `image_secondary`로 재제출:
- API 응답 5xx, 4xx 일부 (rate limit 제외 — backoff 후 재시도)
- 생성 결과가 NSFW 필터(image_post 단계) 탈락
- CLIP 미적 점수 < 0.4 (낮은 품질 자동 재시도)
- 사용자 신고 누적 자산의 같은 프롬프트 패턴 매칭

### 2.3 ComfyUI 수면 모드

`image_special` 큐는 다음과 같이 동작:
- 데스크탑 헬스 `up` → 정상 처리
- 데스크탑 헬스 `degraded` → 1번 시도, 실패 시 큐 보관
- 데스크탑 헬스 `down` → 큐에 보관(작업 폐기 X), JH 데스크탑 켜면 헬스 `up`으로 변경 → Celery 자동 재시도

특수 워크플로우 작업은 **시간 민감하지 않음** (특정 일관성 시리즈는 며칠 늦게 발행돼도 무방). 따라서 큐 보관이 적절.

---

## 3. 특수 워크플로우 정의 (ComfyUI 전용)

ComfyUI를 보조 워커로 운영하는 가치는 **외부 API에서 처리 어려운 차별화 워크플로우**에 있음. Phase 1~3에 걸쳐 점진 도입.

### 3.1 워크플로우 4종

| 파일명 | 용도 | Phase |
|--------|------|------|
| `consistent_character.json` | 같은 캐릭터 12장 시리즈 (PPT 시리즈, 만화 컷) | 2 |
| `controlnet_pose.json` | 특정 포즈 강제 (비즈니스 자세 일관성) | 2 |
| `style_lora_korean.json` | 한국 일러스트 스타일 LoRA (K-콘텐츠 차별화) | 3 |
| `inpaint_iterative.json` | 부분 수정 반복 (큐레이션 후 자산 보정) | 3 |

### 3.2 워크플로우 트리거 (어드민 UI)

자산 상세 페이지의 어드민 컨트롤에 추가:
- **"이 자산을 시리즈로 만들기"** 버튼 → `consistent_character` 큐잉, 파라미터로 캐릭터 시드·N장 입력
- **"포즈 변형"** 버튼 → ControlNet 포즈 이미지 업로드 → `controlnet_pose` 큐잉
- **"K 스타일로 재생성"** 버튼 → `style_lora_korean` 큐잉
- **"부분 수정"** 버튼 → 영역 마스크 그리기 → `inpaint_iterative` 큐잉

### 3.3 자동 트리거

- 큐레이션 인박스에서 자산이 "발전 가능"으로 점수가 매겨지면 자동으로 시리즈화 후보 큐잉 (Phase 3에 도입)
- 인기 카테고리 자산은 주 1회 LoRA 스타일 변형 자동 발행

---

## 4. ComfyUI 측 세팅 (데스크탑) — v0.3과 거의 동일

### 4.1 ComfyUI 외부 인터페이스 바인딩

`run_comfyui_vaultix.bat` (`C:\AI\Image\comfyui\` 위치):

```bat
@echo off
cd /d C:\AI\Image\comfyui
.\python_embeded\python.exe -s ComfyUI\main.py ^
  --listen 0.0.0.0 ^
  --port 8188 ^
  --enable-cors-header * ^
  --output-directory C:\AI\Image\comfyui_output ^
  --temp-directory C:\AI\Image\comfyui_temp ^
  --max-upload-size 50
pause
```

> **주의**: `--listen 0.0.0.0`은 모든 인터페이스에 바인딩되지만, 윈도우 방화벽으로 Tailscale 인터페이스만 8188 인바운드 허용 → 결과적으로 Tailscale 사설망에서만 접근 가능.

### 4.2 윈도우 방화벽 룰

PowerShell (관리자 권한):

```powershell
# Tailscale 인터페이스에서만 8188 인바운드 허용
New-NetFirewallRule -DisplayName "ComfyUI Tailscale 8188" `
  -Direction Inbound -Protocol TCP -LocalPort 8188 `
  -InterfaceAlias "Tailscale" -Action Allow

# 다른 모든 인터페이스에서 8188 차단 (이미 기본 차단이지만 명시)
New-NetFirewallRule -DisplayName "ComfyUI Block Public 8188" `
  -Direction Inbound -Protocol TCP -LocalPort 8188 `
  -InterfaceAlias "Ethernet*","Wi-Fi*" -Action Block
```

### 4.3 자동 시작 (선택, 권장 X)

v0.4에서는 데스크탑이 항시 가동되지 않음을 전제하므로, **ComfyUI를 자동 시작하지 않음**. JH가 데스크탑을 켜고 ComfyUI를 수동 실행하거나, 작업 스케줄러로 "사용자 로그온 시" 트리거만 등록.

### 4.4 모델·LoRA 디렉토리

```
C:\AI\Image\comfyui\models\
├── checkpoints\         # Flux, SDXL 메인 모델
│   ├── flux1-dev-fp8.safetensors
│   └── sdxl-base-1.0.safetensors
├── loras\               # 스타일 LoRA
│   ├── korean_illustration_v1.safetensors  (Phase 3)
│   └── ...
├── vae\
├── clip\
└── controlnet\
    ├── control_v11p_sd15_openpose.pth
    └── ...
```

> Phase 2부터 LoRA·ControlNet 도입. Phase 1은 특수 워크플로우 자체가 없으므로 ComfyUI 비활성 가능.

---

## 5. 외부 API 어댑터

### 5.1 Nanobanana 어댑터 (1차)

```python
# apps/api/src/vaultix_api/adapters/nanobanana.py
from __future__ import annotations
import httpx
from vaultix_api.settings import settings


class NanobananaError(Exception):
    pass


class NanobananaClient:
    """Nanobanana 이미지 생성 API. 무제한 플랜."""

    def __init__(self, api_key: str, timeout: float = 120.0):
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # 실제 endpoint는 D.1 결과로 확정 — 여기는 추정
        self.base_url = settings.nanobanana_base_url

    async def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 1024,
        seed: int | None = None,
        negative_prompt: str = "",
        model: str = "default",
    ) -> bytes:
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "model": model,
            **({"seed": seed} if seed is not None else {}),
            **({"negative_prompt": negative_prompt} if negative_prompt else {}),
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as c:
            r = await c.post(f"{self.base_url}/v1/generate", json=payload)
            if r.status_code != 200:
                raise NanobananaError(f"generate failed: {r.status_code} {r.text[:200]}")
            data = r.json()
            # 응답 형식이 동기형(URL) vs 비동기형(job_id)인지 확인 필요 — 추후 보정
            if "image_url" in data:
                img = await c.get(data["image_url"])
                img.raise_for_status()
                return img.content
            elif "image_base64" in data:
                import base64
                return base64.b64decode(data["image_base64"])
            else:
                raise NanobananaError(f"unknown response shape: {list(data.keys())}")
```

### 5.2 OpenAI `gpt-image-2` 어댑터 (2차)

```python
# apps/api/src/vaultix_api/adapters/gpt_image.py
from __future__ import annotations
import httpx
import base64
from vaultix_api.settings import settings


class GPTImageError(Exception):
    pass


class GPTImageClient:
    """OpenAI gpt-image-2 (Images API)."""

    def __init__(self, api_key: str, timeout: float = 180.0):
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.base_url = "https://api.openai.com/v1"

    async def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",   # "1024x1024" | "1024x1792" | "1792x1024"
        quality: str = "high",
        model: str = "gpt-image-2",
    ) -> bytes:
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
            "response_format": "b64_json",
        }
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as c:
            r = await c.post(f"{self.base_url}/images/generations", json=payload)
            if r.status_code != 200:
                raise GPTImageError(f"generate failed: {r.status_code} {r.text[:200]}")
            data = r.json()
            b64 = data["data"][0]["b64_json"]
            return base64.b64decode(b64)
```

### 5.3 ComfyUI 어댑터 (3차, 특수 워크플로우 전용)

```python
# apps/api/src/vaultix_api/adapters/comfy.py
from __future__ import annotations
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any
import httpx
from loguru import logger

from vaultix_api.settings import settings

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"


class ComfyError(Exception):
    """ComfyUI 호출 실패. 호출자는 큐에 보관(폐기 X)할 것."""


class ComfyAsleepError(ComfyError):
    """데스크탑 자체가 꺼져있는 상태. 큐에 그대로 보관."""


class ComfyClient:
    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    async def health(self) -> dict:
        """200 + 여유 VRAM 있는지 확인."""
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self.base_url}/system_stats")
                r.raise_for_status()
                return r.json()
        except (httpx.ConnectTimeout, httpx.ConnectError) as e:
            raise ComfyAsleepError(f"desktop unreachable: {e}") from e

    async def submit(self, workflow: dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(f"{self.base_url}/prompt", json=payload)
            if r.status_code != 200:
                raise ComfyError(f"submit failed: {r.status_code} {r.text[:200]}")
            return r.json()["prompt_id"]

    async def wait_for_result(
        self, prompt_id: str, *, max_wait: float = 300.0, poll: float = 2.0
    ) -> list[dict]:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=10) as c:
            while time.monotonic() - start < max_wait:
                r = await c.get(f"{self.base_url}/history/{prompt_id}")
                if r.status_code == 200:
                    data = r.json()
                    if prompt_id in data:
                        outputs = data[prompt_id].get("outputs", {})
                        # SaveImage 노드 ID는 워크플로우마다 다름
                        for node_id, node_out in outputs.items():
                            if "images" in node_out and node_out["images"]:
                                return node_out["images"]
                await asyncio.sleep(poll)
        raise ComfyError(f"timeout after {max_wait}s for prompt_id={prompt_id}")

    async def download(self, image_meta: dict, dest: Path) -> Path:
        params = {
            "filename": image_meta["filename"],
            "subfolder": image_meta.get("subfolder", ""),
            "type": image_meta.get("type", "output"),
        }
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{self.base_url}/view", params=params)
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            return dest


def render_workflow(template_name: str, vars: dict[str, Any]) -> dict:
    raw = (WORKFLOWS_DIR / template_name).read_text(encoding="utf-8")
    for key, val in vars.items():
        raw = raw.replace(f'"{{{{{key}}}}}"', json.dumps(val))
    return json.loads(raw)
```

---

## 6. Celery 워커 설계

### 6.1 큐와 라우팅

```python
# apps/api/src/vaultix_api/workers/celery_app.py
from celery import Celery
from vaultix_api.settings import settings

celery_app = Celery(
    "vaultix",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_routes={
        "vaultix.image.generate_primary":   {"queue": "image_primary"},
        "vaultix.image.generate_secondary": {"queue": "image_secondary"},
        "vaultix.image.generate_special":   {"queue": "image_special"},
        "vaultix.image.validate":           {"queue": "image_post"},
        "vaultix.image.score":              {"queue": "image_post"},
        "vaultix.image.metadata":           {"queue": "image_post"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    timezone="Asia/Seoul",
    enable_utc=False,
)
```

### 6.2 워커 컨테이너 분리 (docker-compose 추가분)

```yaml
  celery-image-primary:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-image-primary
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis, postgres]
    environment:
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      NANOBANANA_API_KEY: ${NANOBANANA_API_KEY}
      NANOBANANA_BASE_URL: ${NANOBANANA_BASE_URL}
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/assets:/data/assets
    command: celery -A vaultix_api.workers.celery_app worker -Q image_primary -c 4 -n primary@%h

  celery-image-secondary:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-image-secondary
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis, postgres]
    environment:
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/assets:/data/assets
    command: celery -A vaultix_api.workers.celery_app worker -Q image_secondary -c 2 -n secondary@%h

  celery-image-special:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-image-special
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis, postgres]
    environment:
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      COMFY_HOST: ${COMFY_HOST}
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/assets:/data/assets
    command: celery -A vaultix_api.workers.celery_app worker -Q image_special -c 1 -n special@%h

  celery-image-post:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-image-post
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis, postgres]
    environment:
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/assets:/data/assets
    command: celery -A vaultix_api.workers.celery_app worker -Q image_post -c 4 -n post@%h
```

> **주의**: `celery-image-post`에서 Ollama 의존 제거 (D-13). 메타데이터는 외부 LLM API 호출.

### 6.3 메인 태스크

```python
# apps/api/src/vaultix_api/workers/tasks_image.py
from __future__ import annotations
from pathlib import Path
import asyncio
from celery.utils.log import get_task_logger

from vaultix_api.workers.celery_app import celery_app
from vaultix_api.adapters.comfy import ComfyClient, ComfyError, ComfyAsleepError, render_workflow
from vaultix_api.adapters.nanobanana import NanobananaClient, NanobananaError
from vaultix_api.adapters.gpt_image import GPTImageClient, GPTImageError
from vaultix_api.db.session import SessionLocal
from vaultix_api.models.generation_job import GenerationJob, JobStatus
from vaultix_api.settings import settings

log = get_task_logger(__name__)
ASSET_RAW_DIR = Path("/data/assets/raw")
WIDTH_HEIGHT = {"1:1": (1024, 1024), "2:3": (832, 1216), "3:2": (1216, 832)}


@celery_app.task(
    name="vaultix.image.generate_primary",
    bind=True,
    autoretry_for=(NanobananaError,),
    retry_kwargs={"max_retries": 2, "countdown": 30},
)
def generate_primary(self, job_id: int):
    """1차: Nanobanana API."""
    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.status = JobStatus.GENERATING_PRIMARY
        job.attempts += 1
        db.commit()

        client = NanobananaClient(settings.nanobanana_api_key)
        w, h = WIDTH_HEIGHT[job.aspect_ratio]
        try:
            png = run_async(client.generate(
                prompt=job.prompt_text,
                width=w, height=h,
                seed=job.seed,
                negative_prompt=job.negative_prompt or "",
            ))
            dest = ASSET_RAW_DIR / f"job_{job.id}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(png)

            job.raw_path = str(dest)
            job.generator = "nanobanana"
            job.status = JobStatus.GENERATED
            db.commit()

            from vaultix_api.workers.tasks_post import validate_image
            validate_image.delay(job_id)

        except NanobananaError as e:
            log.warning(f"nanobanana failed for job {job_id}: {e}")
            if self.request.retries < 2:
                raise  # autoretry
            # 최종 실패 → 2차 승격
            generate_secondary.delay(job_id)


@celery_app.task(
    name="vaultix.image.generate_secondary",
    bind=True,
    autoretry_for=(GPTImageError,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
)
def generate_secondary(self, job_id: int):
    """2차: OpenAI gpt-image-2 API."""
    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.status = JobStatus.GENERATING_SECONDARY
        job.attempts += 1
        db.commit()

        client = GPTImageClient(settings.openai_api_key)
        size = {"1:1": "1024x1024", "2:3": "1024x1792", "3:2": "1792x1024"}[job.aspect_ratio]
        try:
            png = run_async(client.generate(prompt=job.prompt_text, size=size))
            dest = ASSET_RAW_DIR / f"job_{job.id}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(png)

            job.raw_path = str(dest)
            job.generator = "gpt_image_2"
            job.status = JobStatus.GENERATED
            db.commit()

            from vaultix_api.workers.tasks_post import validate_image
            validate_image.delay(job_id)

        except GPTImageError as e:
            log.error(f"gpt_image failed for job {job_id}: {e}")
            if self.request.retries < 2:
                raise
            job.status = JobStatus.FAILED
            job.error = str(e)[:500]
            db.commit()


@celery_app.task(
    name="vaultix.image.generate_special",
    bind=True,
    autoretry_for=(ComfyAsleepError, ComfyError),
    retry_kwargs={"max_retries": 30, "countdown": 600},  # 30회 × 10분 = 5시간 대기
    retry_backoff=False,
)
def generate_special(self, job_id: int):
    """3차: ComfyUI 특수 워크플로우. 데스크탑 down이면 큐에 보관(재시도)."""
    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.attempts += 1

        comfy = ComfyClient(settings.comfy_host)
        try:
            run_async(comfy.health())
        except ComfyAsleepError:
            # 데스크탑이 꺼져있음 → 큐 보관, 10분 후 재시도
            log.info(f"desktop asleep, requeue job {job_id} in 10min")
            raise

        job.status = JobStatus.GENERATING_SPECIAL
        db.commit()

        workflow_template = job.workflow_template  # e.g. "consistent_character.json"
        workflow = render_workflow(workflow_template, job.workflow_params or {})

        prompt_id = run_async(comfy.submit(workflow))
        images = run_async(comfy.wait_for_result(prompt_id, max_wait=300))
        dest = ASSET_RAW_DIR / f"job_{job.id}.png"
        run_async(comfy.download(images[0], dest))

        job.raw_path = str(dest)
        job.generator = "comfyui"
        job.status = JobStatus.GENERATED
        db.commit()

        from vaultix_api.workers.tasks_post import validate_image
        validate_image.delay(job_id)


def run_async(coro):
    """Celery 태스크 안에서 async 호출 헬퍼."""
    return asyncio.get_event_loop().run_until_complete(coro)
```

### 6.4 라우팅 결정 로직 (요약)

```
새 작업 enqueue
   ├─ workflow_template 지정 안 됨 (일반 자산) → image_primary 큐
   │     └─ Nanobanana 실패 시 자동 image_secondary 승격
   │
   └─ workflow_template 지정 (특수 워크플로우) → image_special 큐
         ├─ Redis health:comfy = "up" → 즉시 처리
         ├─ Redis health:comfy = "degraded" → 1번 시도
         └─ Redis health:comfy = "down" → 큐 보관(10분 간격 헬스 재확인)
```

---

## 7. 헬스체크 패턴

### 7.1 정기 헬스체크 (10분마다, v0.3은 5분 → 데스크탑 부담 ↓)

```python
# apps/api/src/vaultix_api/workers/tasks_health.py
from celery.schedules import crontab
from vaultix_api.workers.celery_app import celery_app
from vaultix_api.adapters.comfy import ComfyClient, ComfyAsleepError, ComfyError

celery_app.conf.beat_schedule = {
    "comfy-health-10min": {
        "task": "vaultix.health.comfy",
        "schedule": crontab(minute="*/10"),
    },
    "external-api-health-5min": {
        "task": "vaultix.health.external_apis",
        "schedule": crontab(minute="*/5"),
    },
}

@celery_app.task(name="vaultix.health.comfy")
def health_comfy():
    """Tailscale로 데스크탑 ComfyUI 헬스 체크. 상태를 Redis에 기록."""
    import redis as r
    from vaultix_api.settings import settings

    rc = r.from_url(settings.redis_url)
    try:
        comfy = ComfyClient(settings.comfy_host, timeout=5)
        stats = run_async(comfy.health())
        rc.setex("health:comfy", 1200, "up")
        rc.delete("health:comfy:fails")
        device = stats.get("devices", [{}])[0]
        rc.setex(
            "health:comfy:meta", 1200,
            f"{device.get('name','?')} vram_free={device.get('vram_free',0)}"
        )
    except ComfyAsleepError as e:
        # 데스크탑 자체가 꺼짐 — 알림 안 함 (정상 시나리오)
        rc.setex("health:comfy", 1200, "down")
    except ComfyError as e:
        # ComfyUI 프로세스만 죽음 — 알림 (JH 액션 필요)
        fails = int(rc.get("health:comfy:fails") or 0) + 1
        rc.setex("health:comfy:fails", 3600, str(fails))
        if fails >= 3:
            rc.setex("health:comfy", 1200, "down")
            send_alert(f"ComfyUI process down (3 consecutive checks): {e}")
        else:
            rc.setex("health:comfy", 1200, "degraded")
```

> **포인트**: `ComfyAsleepError`(데스크탑 자체 꺼짐)은 정상 시나리오라 알림 안 함. `ComfyError`(데스크탑은 켜져있는데 ComfyUI만 죽음)는 JH 조치 필요라 알림.

### 7.2 외부 API 헬스 (신규)

```python
@celery_app.task(name="vaultix.health.external_apis")
def health_external_apis():
    """Nanobanana / OpenAI gpt-image-2 헬스 체크. 둘 다 down이면 P0 알림."""
    import redis as r
    rc = r.from_url(settings.redis_url)

    nb_ok = check_nanobanana_health()
    gpt_ok = check_gpt_image_health()

    rc.setex("health:nanobanana", 600, "up" if nb_ok else "down")
    rc.setex("health:gpt_image", 600, "up" if gpt_ok else "down")

    if not nb_ok and not gpt_ok:
        send_alert("P0: Both image APIs down (Nanobanana + gpt-image-2)")
```

### 7.3 Uptime Kuma 모니터

| 모니터 | 종류 | 임계 |
|--------|------|------|
| Nanobanana API | HTTP `https://api.nanobanana.{...}/health` (실제 endpoint은 D.1) | 응답 < 5s |
| OpenAI `gpt-image-2` API | HTTP `https://api.openai.com/v1/models` (200 + 인증 OK) | 응답 < 10s |
| ComfyUI Tailscale | HTTP `http://100.x.x.x:8188/system_stats` (선택, JH 가용 시간만 모니터) | 응답 < 5s |

---

## 8. 보안 (Tailscale ACL) — v0.3과 동일

### 8.1 Tailscale ACL 설정

`https://login.tailscale.com/admin/acls`:

```jsonc
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:vps"],
      "dst": ["tag:desktop:8188"],
    },
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": ["*:*"],
    },
  ],
  "tagOwners": {
    "tag:vps": ["autogroup:owner"],
    "tag:desktop": ["autogroup:owner"],
  },
}
```

### 8.2 ComfyUI 자체 인증 (선택)

Tailscale ACL로 충분. 추가 보안은 Phase 4+에서 검토.

---

## 9. 큐잉 전략

### 9.1 일일 자동 발행 배치

```python
# apps/api/src/vaultix_api/services/scheduler.py
from vaultix_api.workers.tasks_image import generate_primary, generate_special
from vaultix_api.models.prompt_template import PromptTemplate
from vaultix_api.models.generation_job import GenerationJob
import random
import redis as r
from vaultix_api.settings import settings


def enqueue_daily_batch(db, *, target_count: int = 50):
    """매일 09:00 KST에 호출되는 배치. 일반 자산 N장 큐잉."""
    templates = pick_templates(db, count=target_count)
    for tpl in templates:
        prompt_text = render_prompt(tpl)
        job = GenerationJob(
            prompt_template_id=tpl.id,
            prompt_text=prompt_text,
            negative_prompt=tpl.negative_prompt,
            aspect_ratio=tpl.aspect_ratio,
            seed=random.randint(1, 2**31),
        )
        db.add(job); db.flush()
        generate_primary.delay(job.id)  # 무조건 1차로 시작 (외부 API 무제한)
    db.commit()


def enqueue_special(db, *, template_name: str, params: dict, parent_asset_id: int | None = None):
    """특수 워크플로우 큐잉. 어드민 트리거 또는 자동."""
    job = GenerationJob(
        workflow_template=template_name,
        workflow_params=params,
        parent_asset_id=parent_asset_id,
        status=JobStatus.QUEUED_SPECIAL,
    )
    db.add(job); db.flush()
    generate_special.delay(job.id)
    db.commit()
```

### 9.2 시간대별 운영 가이드

데스크탑 가용성에 의존하지 않음. 단, 특수 워크플로우의 처리 속도는 데스크탑 가용 시간에 종속.

| 시간대 | 일반 자산(image_primary/secondary) | 특수 워크플로우(image_special) |
|--------|-----------------------------------|------------------------------|
| 24/7 | 외부 API로 즉시 처리 | 데스크탑 켜진 시간만 처리, 그 외 큐 대기 |
| JH 데스크탑 켜진 시간 | (영향 없음) | 큐에 쌓인 작업 일괄 처리 |
| JH 휴가 모드 | 일시 정지(인박스 누적) | 일시 정지 |

### 9.3 큐 상태 어드민 API

```python
@router.get("/admin/queue/status")
async def queue_status():
    return {
        "image_primary": redis_queue_len("image_primary"),
        "image_secondary": redis_queue_len("image_secondary"),
        "image_special": redis_queue_len("image_special"),
        "image_post": redis_queue_len("image_post"),
        "comfy_health": redis_get("health:comfy"),
        "nanobanana_health": redis_get("health:nanobanana"),
        "gpt_image_health": redis_get("health:gpt_image"),
        "today_calls": {
            "nanobanana": count_today("nanobanana"),
            "gpt_image": count_today("gpt_image_2"),
            "comfyui": count_today("comfyui"),
        },
    }
```

---

## 10. 환경변수 (.env 추가분)

```dotenv
# 외부 이미지 API (D-14)
NANOBANANA_API_KEY=
NANOBANANA_BASE_URL=https://api.nanobanana.{...}    # D.1 결과로 확정

OPENAI_API_KEY=                                      # gpt-image-2 + LLM 라우팅 공용
OPENAI_IMAGE_MODEL=gpt-image-2

# 데스크탑 ComfyUI (특수 워크플로우 전용)
COMFY_HOST=http://100.x.x.x:8188                     # 데스크탑 Tailscale IP
COMFY_TIMEOUT=300                                     # 단일 작업 max 대기 (초)

# v0.3에서 제거된 변수 (참고용)
# OLLAMA_BASE_URL — D-13으로 폐기
# OLLAMA_META_MODEL — 폐기
# REPLICATE_API_TOKEN — D-14로 폐기
# FAL_API_KEY — 폐기
# EXTERNAL_BUDGET_USD_PER_MONTH — 무제한 키 보유로 캡 무의미
```

---

## 11. 실패·예외 케이스 매트릭스

| 케이스 | 감지 | 자동 대응 | 운영자 알림 |
|--------|------|----------|-----------|
| Nanobanana API 5xx | 응답 코드 | autoretry 2회 → 2차 승격 | 5분 내 5회 이상 fallback 시 |
| Nanobanana rate limit | 429 | exponential backoff 5분까지 | 5분 이상 지속 시 |
| OpenAI `gpt-image-2` 5xx | 응답 코드 | autoretry 2회 → job 실패 | 즉시 알림 (둘 다 다운이면 P0) |
| 두 외부 API 동시 다운 | health 체크 | 신규 일반 자산 작업 큐 일시 정지 | P0 텔레그램 |
| 데스크탑 꺼짐 | health=down | special 큐 보관(10분 간격 재시도) | 알림 안 함 (정상) |
| 데스크탑 켜짐, ComfyUI만 죽음 | submit 5xx | autoretry 2회 → 큐 보관 | 텔레그램 (JH 조치 필요) |
| Tailscale 끊김 | TCP 타임아웃 | special 큐 보관 | 텔레그램 (Tailscale 자체 이슈) |
| GPU OOM | submit 200이지만 wait 에러 | retry 2회 → 큐 보관 | 잦으면 알림 |
| 워크플로우 JSON 오류 | submit 400 | autoretry 무의미 → 즉시 실패 | 텔레그램 (코드 버그) |
| 외부 API 토큰 만료 | 401 | autoretry 무의미 → 즉시 실패 | P0 텔레그램 |
| 결과 PNG 깨짐 | 검증 단계 실패 | retry 1회 → 폐기 | 일일 리포트 |
| 디스크 가득 | write_bytes 에러 | 즉시 실패 | P0 텔레그램 |

---

## 12. 성능 목표

### 12.1 Phase 1

| 메트릭 | 목표 |
|--------|------|
| Nanobanana 1장 생성 (1024×1024) | 5~15초 (서비스 사양에 따름) |
| OpenAI `gpt-image-2` 1장 생성 (1024×1024) | 15~30초 |
| 다운로드(생성된 PNG, 1~3MB) | < 3초 |
| 일 자동 발행 (합계) | 50장 |
| Nanobanana 비중 | > 90% |
| OpenAI `gpt-image-2` 비중 (1차 실패 폴백) | < 10% |
| ComfyUI 비중 | 0% (Phase 1엔 특수 워크플로우 미도입) |

### 12.2 Phase 2~3

| 메트릭 | 목표 |
|--------|------|
| 일 자동 발행 | 100~200장 |
| 특수 워크플로우 발행 | 일 5~20장 (데스크탑 가용 시) |
| ComfyUI 큐 보관 시간 (데스크탑 down) | 평균 12시간 이내 처리 (JH 일일 가동 가정) |

---

## 13. Phase별 진화

| Phase | 추가 기능 |
|:---:|----------|
| 0 | 본 라우팅 골격 + Nanobanana/`gpt-image-2` 어댑터 PoC |
| 1 | image_primary + image_secondary 본격 운영 (일 50장). image_special은 골격만 (작업 없음) |
| 2 | 특수 워크플로우 2종 도입: `consistent_character`, `controlnet_pose` |
| 3 | 특수 워크플로우 2종 추가: `style_lora_korean`, `inpaint_iterative`. 큐레이션 인박스 → 시리즈화 자동 트리거 |
| 4 | A/B 테스트 (Nanobanana 모델 v1 vs v2 비교, 다운로드 → 자동 가중치) |
| 5 | 영상용 ffmpeg 합성 워커 추가 (이미지 N장 → 슬라이드쇼) |

---

## 14. 다음 문서로 이어지는 결정

- `GenerationJob` 모델 (필드: `workflow_template`, `workflow_params`, `parent_asset_id`, `generator` enum 갱신) → A1 데이터모델 DDL 갱신
- `/admin/queue/status`, `/admin/jobs/*`, `/admin/special/trigger` 엔드포인트 → A2 API 스펙 갱신
- 워커 컨테이너 추가·재구성 → 02 Phase 1 docker-compose 추가분 갱신
- 워크플로우 JSON 4종 → Phase 2~3에 작성
- 어드민 UI에 특수 워크플로우 트리거 버튼 → B2 와이어프레임 어드민 자산상세 페이지에 추가

---

## 부록 — 폐기된 v0.3 결정·코드

| 항목 | 폐기 이유 | 대체 |
|------|----------|------|
| Replicate / fal.ai 어댑터 | 외부 API 무제한 키로 불필요 | Nanobanana / `gpt-image-2` |
| `EXTERNAL_BUDGET_USD_PER_MONTH=50` 비용 캡 | 무제한 플랜으로 무의미 | 호출량 추적만 (T-10) |
| Ollama 메타데이터 단계 | D-13으로 외부 LLM API 통일 | A7 라우팅 정책 §2 |
| 데스크탑 자동 시작 | 데스크탑 항시 가동 X 전제 | JH 수동 실행 또는 사용자 로그온 트리거만 |
| 시간대별 ComfyUI 풀가동 (23:00~06:00 50장 배치) | 일반 자산은 외부 API로 24/7 처리 | 시간대 정책 불필요 |

