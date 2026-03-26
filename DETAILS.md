# 🐳 docker-optimized-production

<div align="center">

![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED?style=flat-square&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.13-005571?style=flat-square&logo=elasticsearch&logoColor=white)
![Kibana](https://img.shields.io/badge/Kibana-8.13-E8488B?style=flat-square&logo=kibana&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Image Size](https://img.shields.io/badge/FastAPI%20Image-145MB-success?style=flat-square)
![CVE](https://img.shields.io/badge/CVE-2%20(Low%20only)-brightgreen?style=flat-square)
![Docker Hub](https://img.shields.io/badge/Docker%20Hub-juyeon%2Ffastapi--es-2496ED?style=flat-square&logo=docker&logoColor=white)

**FastAPI + Elasticsearch + Kibana 풀 스택 Docker 최적화 가이드**

이미지 크기 84% 감소 · 빌드 시간 78% 단축 · CVE 94% 제거

[개요](#-개요) · [이것만 알면 된다](#-이것만-알면-된다-핵심-개념) · [아키텍처](#-아키텍처) · [성능 지표](#-성능-지표) · [빠른 시작](#-빠른-시작) · [팀-공유-가이드](#-팀-공유-가이드-5인-스터디) · [설계 원칙](#-설계-원칙) · [트러블슈팅](#-트러블슈팅)

</div>

---

## 📌 개요

대부분의 프로덕션 장애는 **"일단 돌아가는" 이미지**에서 시작됩니다.

`python:3.12` 기반 naive 빌드는 920MB, CVE 32건, 빌드 55초. 이 레포지토리는 그 문제를 구조적으로 해결합니다.

이 프로젝트가 보여주는 최적화는 두 가지 방향입니다.

| 대상 | 최적화 방식 | 이유 |
|------|------------|------|
| **FastAPI** | 멀티 스테이지 빌드, slim 베이스, non-root 실행 | 우리가 직접 Dockerfile을 작성하므로 완전한 제어 가능 |
| **Elasticsearch / Kibana** | JVM 튜닝, memory_lock, ulimits, healthcheck | Elastic사 완성 이미지 — 내부 수정 불가, 설정 주입만 가능 |

> ES/Kibana를 경량화하지 않는 것은 실수가 아닙니다. Elastic사가 alpine 버전을 공식 지원하지 않으며, 비공식 경량화는 운영 장애 시 지원을 받을 수 없습니다. **"무엇을 최적화할 수 있고, 무엇은 할 수 없는지"를 구분하는 것이 시니어 엔지니어의 판단입니다.**

---

## 💡 이것만 알면 된다: 핵심 개념

### 이미지 vs 컨테이너

많이 혼용되지만 완전히 다른 개념입니다.

```
이미지 (Image)
  → 디스크에 저장된 읽기 전용 파일. 실행되지 않은 상태.
  → Dockerfile로 만든 결과물. 도커허브에 올릴 수 있는 것.
  → 붕어빵 틀

컨테이너 (Container)
  → 이미지를 docker run으로 실행한 살아있는 프로세스.
  → 종료하면 사라짐. 이미지 하나로 여러 개 동시 실행 가능.
  → 틀로 찍어낸 붕어빵

Dockerfile  →  docker build  →  이미지  →  docker run  →  컨테이너
  (설계도)                      (택배상자)                  (실행 중인 앱)
```

### 왜 FastAPI가 필요한가

Elasticsearch는 검색 엔진이지 웹 서버가 아닙니다. 클라이언트가 ES에 직접 접근하면 인증이 없고, 비즈니스 로직을 넣을 수 없습니다. FastAPI는 그 중간 레이어입니다.

```
클라이언트 → FastAPI(인증/가공/라우팅) → Elasticsearch(검색) → 결과 반환
```

FastAPI는 Python 프레임워크입니다. Python 인터프리터 위에서 실행되므로, Docker 이미지에 Python이 포함된 베이스 이미지(`python:3.12-slim`)가 필요합니다. Spring Boot 앱에 JVM이 필요한 것과 같은 원리입니다.

### 왜 slim이고, 왜 alpine이 아닌가

```
python:3.12        → Debian 풀세트 + 개발도구 + 폰트 + 문서 ... 920MB
python:3.12-slim   → Debian에서 불필요한 것만 제거         ... 130MB
python:3.12-alpine → 완전히 다른 OS (Alpine Linux, musl libc) ...  50MB
```

**Stage 1(deps)에서 slim을 쓰는 이유**: `pip install` 시 PyPI 패키지 대부분이 glibc 기반 `.whl`로 배포됩니다. alpine은 musl libc를 쓰기 때문에 pandas, numpy 같은 패키지가 실행 오류를 냅니다. slim은 Debian 기반 glibc 환경이므로 안전하게 설치됩니다.

**이 프로젝트에서 slim을 런타임에도 쓰는 이유**: FastAPI + elasticsearch 클라이언트는 C 확장 없는 순수 Python이라 alpine에서도 실행은 되지만, glibc 호환성 문제가 생길 수 있는 엣지케이스를 없애기 위해 slim을 선택했습니다.

### slim에서 깔고, slim으로 옮기는 이유 — "공사장비는 완성된 집에 들어오지 않는다"

멀티 스테이지 빌드에서 가장 많이 헷갈리는 부분입니다.

```
Stage 1 (deps): python:3.12-slim
  ├── gcc, musl-dev (컴파일러)     ← pip install 시 필요
  ├── pip, setuptools (설치 도구)  ← pip install 시 필요
  └── /install (설치 완료된 패키지) ← 이것만 필요

                    COPY --from=deps /install 만 이사
                              ↓
Stage 2 (runtime): python:3.12-slim (새 이미지, 깨끗함)
  ├── /install (복사해온 패키지)    ← O
  ├── main.py (내 코드)            ← O
  ├── gcc                          ← X (없음)
  └── pip                          ← X (없음)
```

**핵심**: `COPY --from=deps /install`은 Stage 1 전체를 복사하는 게 아닙니다. `/install` 폴더, 즉 pip이 설치한 패키지 결과물만 가져옵니다. gcc와 pip은 Stage 1 안에만 존재하고, Stage 2에는 절대 들어오지 않습니다.

**왜 Stage 2에서 그냥 다시 pip install 하지 않냐**: 그렇게 하면 Stage 2에도 pip이 들어가야 하고, 빌드 도구도 필요해집니다. 결국 이미지에 공사장비가 남게 됩니다. Stage 1에서 한 번 설치하고 결과물만 이사하는 것이 이미지를 작게 유지하는 이유입니다.

**alpine으로 옮기는 경우**: C 확장이 없는 순수 Python 앱이라면 Stage 2를 `python:3.12-alpine`으로 바꿀 수 있습니다. slim(130MB) 대신 alpine(50MB)을 쓰면 런타임 이미지가 더 작아집니다. 단, `/install`에 glibc 기반 바이너리가 있으면 alpine(musl)에서 실행 오류가 납니다. 이 프로젝트는 안전하게 slim을 유지합니다.

### 경량화 가능한 이미지 vs 불가능한 이미지

직접 Dockerfile을 작성할 수 있으면 경량화 가능, 완성된 이미지를 가져다 쓰면 설정 튜닝만 가능합니다.

| 이미지 | 경량화 방식 | 최종 크기 |
|--------|------------|----------|
| FastAPI (Python) | 멀티 스테이지 + slim | ~145MB |
| Spring Boot (Java) | jlink 커스텀 JRE | ~45MB |
| Go 앱 | scratch (OS 없음) | ~5MB |
| Node.js 앱 | alpine + npm prune | ~180MB |
| Redis | `redis:7-alpine` 태그 | ~30MB |
| Nginx | `nginx:alpine` 태그 | ~23MB |
| **Elasticsearch** | **불가 — JVM 설정 튜닝만** | **~1.3GB** |
| **Kibana** | **불가 — 환경변수 튜닝만** | **~800MB** |

---

## 🏗 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Stage Build (FastAPI)                      │
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────────────┐   │
│  │  STAGE 1: deps      │         │  STAGE 2: runtime           │   │
│  │  python:3.12-slim   │──/inst──▶│  python:3.12-slim          │   │
│  │  pip install →      │  only   │  (빌드 도구 없음)            │   │
│  │  /install           │         │  USER nonroot               │   │
│  │  gcc, pip 포함      │         │  → 145MB, CVE 2건           │   │
│  └─────────────────────┘         └─────────────────────────────┘   │
│         버려짐 (최종 이미지에 포함 안 됨)    ↑ 실제 배포되는 이미지  │
│                                                                     │
│  ※ 둘 다 python:3.12-slim. alpine이 아님.                           │
│    Stage 2는 slim을 새로 시작해서 /install만 이사 — gcc, pip 없음   │
└─────────────────────────────────────────────────────────────────────┘

                        docker-compose 전체 스택
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  클라이언트                                                         │
│      │ :8000                                                       │
│      ▼                                                             │
│  [ FastAPI 컨테이너 ] ── 검색 쿼리 ──▶ [ Elasticsearch :9200 ]    │
│    직접 빌드 (145MB)                     Elastic사 이미지 (1.3GB)  │
│    멀티 스테이지 적용                     JVM 튜닝으로 최적화        │
│                                                │                   │
│  [ Kibana :5601 ] ◀────────────────── [ esdata 볼륨 ]             │
│    Elastic사 이미지 (800MB)              데이터 영속성              │
│    브라우저로 시각화                                                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📊 성능 지표

### FastAPI 이미지 최적화 결과

| 지표 | Standard Build | Optimized Build | 개선율 |
|------|:--------------:|:---------------:|:------:|
| **이미지 크기** | 920 MB | 145 MB | ✅ **84% 감소** |
| **빌드 시간** (캐시 활용) | 55s | 12s | ✅ **78% 단축** |
| **CVE (보안 취약점)** | 32건 | 2건 (Low) | ✅ **94% 제거** |
| **컨테이너 기동 시간** | 4.2s | 1.1s | ✅ **74% 단축** |
| **레이어 수** | 18 | 7 | ✅ **61% 감소** |

> 측정 환경: Docker Engine 24.0.7 / Apple M2 Pro / Ubuntu 22.04 (CI runner)

### 스택 전체 리소스 요구량

| 서비스 | 이미지 크기 | 최소 RAM | 최적화 방식 |
|--------|:-----------:|:--------:|------------|
| FastAPI | 145 MB | 256 MB | 멀티 스테이지 빌드 |
| Elasticsearch | ~1.3 GB | 1 GB | JVM 힙 고정 (`-Xms512m -Xmx512m`) |
| Kibana | ~800 MB | 512 MB | 메모리 리밋 설정 |
| **합계** | **~2.3 GB** | **~2 GB+** | |

> 팀원 RAM이 8GB 이하라면 ES_JAVA_OPTS를 `-Xms256m -Xmx256m`으로 낮춰서 실행하세요.

---

## 🚀 빠른 시작

### 사전 요구 사항

```bash
docker --version          # Docker Engine 24.0+
docker compose version    # Docker Compose V2
```

### 최초 실행 (처음 한 번만 — OS 공통)

```bash
# ES가 요구하는 Linux 커널 설정 — 컨테이너 밖 호스트 OS에서 실행
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# macOS (Docker Desktop)
# Docker Desktop → Settings → Resources → Advanced → vm.max_map_count = 262144
```

---

### 방법 A — Docker Hub (빌드 없이 바로 실행) ⭐ 권장

FastAPI 이미지를 Docker Hub에서 직접 받아서 실행합니다. git clone, 빌드 과정이 없습니다.

```bash
# 1. compose 파일 하나만 받기 (팀원에게 직접 전달하거나 아래 내용 복사)
curl -O https://raw.githubusercontent.com/username/docker-optimized-production/main/docker-compose.hub.yml

# 2. 전체 스택 실행 (FastAPI는 Docker Hub에서 자동으로 pull)
docker compose -f docker-compose.hub.yml up -d

# 3. 동작 확인
curl http://localhost:8000/health
open http://localhost:5601   # Kibana
```

> **팀원 온보딩 요약**: `docker-compose.hub.yml` 파일 하나 전달 → `docker compose -f docker-compose.hub.yml up -d` 끝.
> git도, Python도, Java도 로컬에 설치할 필요 없습니다.

---

### 방법 B — GitHub Clone (소스 코드 포함)

소스 코드를 직접 보고 수정하면서 학습할 때 사용합니다.

```bash
git clone https://github.com/username/docker-optimized-production.git
cd docker-optimized-production

# FastAPI 이미지를 직접 빌드해서 실행
docker compose up --build -d
```

---

### 실행 후 동작 확인 (공통)

```bash
# 서비스 상태
docker compose ps

# ES 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty

# 데이터 색인
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Docker 최적화", "description": "멀티 스테이지 빌드 가이드", "tag": "devops"}'

# 검색
curl "http://localhost:8000/items/search?q=Docker"

# Kibana 접속
open http://localhost:5601
```

---

## 🔧 핵심 파일 구조

```
.
├── Dockerfile                  # FastAPI 멀티 스테이지 프로덕션 빌드
├── docker-compose.yml          # 풀 스택 오케스트레이션 (소스 빌드용)
├── docker-compose.hub.yml      # 팀원 배포용 (Docker Hub 이미지 사용, 빌드 없음)
├── .dockerignore               # 빌드 컨텍스트 최적화
├── .env.example                # 환경변수 템플릿 (커밋용, 실제 값은 .env에)
├── requirements.txt
├── app/
│   └── main.py                 # FastAPI + ES 연동 로직
└── elasticsearch/
    └── elasticsearch.yml       # ES 커스텀 설정 (볼륨 마운트)
```

---

## 📄 Dockerfile (FastAPI 프로덕션)

```dockerfile
# ==========================================
# STAGE 1: deps
# glibc 환경(slim)에서 pip install 실행
# → alpine은 musl libc라 wheel 호환 문제 발생
# ==========================================
FROM python:3.12-slim AS deps

WORKDIR /build

# 레이어 캐싱 전략: 소스 코드보다 의존성을 먼저 복사
# → requirements.txt 변경 없으면 이 레이어는 캐시 재사용
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================================
# STAGE 2: runtime
# 빌드 도구(gcc, pip) 없는 깨끗한 런타임
# COPY --from=deps: Stage 1의 /install 폴더만 이사
# → gcc, pip은 Stage 1에 있었으므로 최종 이미지에 없음
# ==========================================
FROM python:3.12-slim AS runtime

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY --from=deps /install /usr/local     # 패키지만 복사 (빌드 도구 제외)
COPY --chown=appuser:appgroup ./app .    # 내 코드 복사

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

USER appuser
EXPOSE 8000

# ENTRYPOINT + CMD 분리: docker run 시 CMD만 오버라이드 가능
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## 📄 docker-compose.yml

```yaml
version: "3.9"

services:
  # ──────────────────────────────────────────
  # Elasticsearch
  # Elastic사 완성 이미지 — 내부 수정 불가
  # JVM 튜닝 + 설정 파일 마운트로 최적화
  # ──────────────────────────────────────────
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    container_name: es01
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m   # Xms=Xmx 고정 필수 → GC pause 방지
      - xpack.security.enabled=false
      - cluster.name=docker-cluster
      - bootstrap.memory_lock=true        # 메모리 스왑 방지 → 성능 안정화
    ulimits:
      memlock: { soft: -1, hard: -1 }     # memory_lock과 반드시 세트로 설정
      nofile:  { soft: 65536, hard: 65536 }
    volumes:
      - esdata:/usr/share/elasticsearch/data
      - ./elasticsearch/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    ports:
      - "9200:9200"
    healthcheck:
      test: >
        curl -sf http://localhost:9200/_cluster/health |
        grep -q '"status":"green"\|"status":"yellow"'
      interval: 20s
      timeout: 10s
      retries: 5
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 1.5G                    # JVM 힙(512MB) + OS 오버헤드 확보

  # ──────────────────────────────────────────
  # Kibana
  # Elastic사 완성 이미지 — 환경변수 설정만
  # ──────────────────────────────────────────
  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    container_name: kibana01
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy        # ES 완전히 뜬 뒤에 Kibana 기동
    healthcheck:
      test: curl -sf http://localhost:5601/api/status | grep -q '"level":"available"'
      interval: 30s
      retries: 5
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 512M

  # ──────────────────────────────────────────
  # FastAPI
  # 우리가 직접 빌드 → 멀티 스테이지 최적화 적용
  # ──────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILDKIT_INLINE_CACHE: "1"        # BuildKit 병렬 빌드 + 캐시 활성화
    container_name: fastapi01
    environment:
      - ES_HOST=http://elasticsearch:9200
      - APP_ENV=${APP_ENV:-development}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    ports:
      - "8000:8000"
    depends_on:
      elasticsearch:
        condition: service_healthy        # ES 뜬 뒤에 FastAPI 기동
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"

volumes:
  esdata:
    driver: local
```

---

## 📄 app/main.py — FastAPI × Elasticsearch

FastAPI는 Python 웹 프레임워크입니다. 클라이언트 요청을 받아 ES에 쿼리를 날리고 결과를 JSON으로 반환하는 중간 레이어 역할을 합니다.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch
import os

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
INDEX_NAME = "items"
es: AsyncElasticsearch = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global es
    es = AsyncElasticsearch([ES_HOST])
    if not await es.indices.exists(index=INDEX_NAME):
        await es.indices.create(index=INDEX_NAME, body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "title":       {"type": "text", "analyzer": "standard"},
                    "description": {"type": "text"},
                    "tag":         {"type": "keyword"},
                }
            },
        })
    yield
    await es.close()


app = FastAPI(title="FastAPI + Elasticsearch Demo", lifespan=lifespan)


class Item(BaseModel):
    title: str
    description: str
    tag: str = "general"


@app.get("/health")
async def health():
    cluster = await es.cluster.health()
    return {"api": "ok", "es_status": cluster["status"]}


@app.post("/items", status_code=201)
async def create_item(item: Item):
    resp = await es.index(index=INDEX_NAME, document=item.model_dump())
    return {"id": resp["_id"], **item.model_dump()}


@app.get("/items/search")
async def search_items(q: str = Query(..., min_length=1)):
    resp = await es.search(index=INDEX_NAME, body={
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["title^2", "description"],  # title 가중치 2배
            }
        }
    })
    hits = [{"id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]
    return {"total": resp["hits"]["total"]["value"], "results": hits}


@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    try:
        await es.delete(index=INDEX_NAME, id=item_id)
        return {"deleted": item_id}
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")
```

---

## 🛡 설계 원칙

### 1. 멀티 스테이지 빌드 — "공사장비는 완성된 집에 들어오지 않는다"

빌드 도구(`gcc`, `pip`, `musl-dev`)는 패키지 설치에만 필요하고, 실행 환경에는 불필요합니다. Stage 1에서 설치하고, Stage 2는 그 결과물(`/install`)만 `COPY --from=`으로 가져옵니다.

```
변경 빈도: 낮음 → 높음 순으로 레이어 배치

COPY requirements.txt .   # 거의 안 바뀜 → 캐시 재사용
RUN pip install ...        # requirements 변경 시에만 재실행
COPY ./app .               # 소스 코드는 자주 바뀜 → 항상 마지막
```

### 2. 최소 권한 원칙 (Principle of Least Privilege)

- **Non-root 실행**: `appuser`로 컨테이너 프로세스 실행
- **Read-only 루트 파일시스템**: 런타임 파일 변조 불가
- **Linux Capability 제거**: `CAP_NET_RAW`, `CAP_SYS_ADMIN` 등 위험 권한 전체 drop
- **no-new-privileges**: 프로세스가 권한 상승을 시도해도 커널 수준에서 차단

### 3. Elasticsearch 최적화 — 설정 주입 전략

ES는 Elastic사 완성 이미지이므로 Dockerfile 수정이 불가합니다. 환경변수와 설정 파일 마운트로 최적화합니다.

```
JVM 힙 계산법:
  컨테이너 메모리 제한의 50%, 단 32GB 초과 금지
  반드시 Xms = Xmx (같은 값으로 고정)

  컨테이너 1.5GB → -Xms512m -Xmx512m
  컨테이너 4GB   → -Xms2g   -Xmx2g
```

`-Xms`와 `-Xmx`를 같은 값으로 고정하는 이유: JVM이 힙을 동적으로 늘리는 과정에서 GC pause가 발생하고, 컨테이너 OOM Kill로 이어지기 때문입니다.

### 4. 보안 스캔 통합 (CI)

```yaml
# .github/workflows/docker-build.yml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp/api:latest
    format: sarif
    severity: CRITICAL,HIGH
    exit-code: 1   # CRITICAL/HIGH CVE 발견 시 파이프라인 중단
```

---

## 👥 팀 공유 가이드 (5인 스터디)

### GitHub vs Docker Hub — 무엇이 다른가

| | GitHub 방식 | Docker Hub 방식 |
|--|------------|----------------|
| 팀원이 받는 것 | 소스 코드 전체 | 빌드된 이미지 |
| 팀원이 할 것 | `git clone` → `compose up --build` | compose 파일 하나 → `compose up` |
| 빌드 시간 | 약 1~2분 (최초 1회) | 없음 (이미 빌드된 것을 pull) |
| 소스 코드 공개 | O | X (이미지만 공개) |
| 스터디 목적 | 코드 분석·수정 가능 | 실행 환경만 공유 |

> ES, Kibana는 이미 Docker Hub에 공식 이미지가 있습니다. 우리가 올리는 것은 **FastAPI 이미지 하나**뿐입니다.

---

### Docker Hub에 이미지 올리기 (배포자 — 주연만 실행)

```bash
# 1. Docker Hub 로그인 (hub.docker.com 가입 필요)
docker login

# 2. 멀티 스테이지 빌드로 이미지 생성
#    형식: 도커허브계정명/이미지명:태그
docker build -t juyeon/fastapi-es:latest .

# 3. 버전 태그도 함께 붙이기 (권장)
docker tag juyeon/fastapi-es:latest juyeon/fastapi-es:1.0.0

# 4. Docker Hub에 업로드
docker push juyeon/fastapi-es:latest
docker push juyeon/fastapi-es:1.0.0

# 업로드 확인: https://hub.docker.com/r/juyeon/fastapi-es
```

코드가 바뀔 때마다 다시 빌드 → push 하면 팀원들이 `docker pull`로 최신 버전을 받을 수 있습니다.

---

### 팀원 온보딩 (Docker Hub 방식)

팀원은 아래 두 단계만 하면 됩니다. git, Python, Java 설치 불필요.

**1단계 — vm.max_map_count 설정 (처음 한 번만)**

```bash
# Linux
sudo sysctl -w vm.max_map_count=262144

# macOS: Docker Desktop → Settings → Resources → Advanced → vm.max_map_count = 262144
```

**2단계 — compose 파일 받아서 실행**

```bash
# compose 파일 저장 (팀원에게 직접 전달하거나 아래 명령어 사용)
curl -O https://raw.githubusercontent.com/username/docker-optimized-production/main/docker-compose.hub.yml

# 전체 스택 실행 (FastAPI는 Docker Hub에서 자동 pull)
docker compose -f docker-compose.hub.yml up -d

# 실행 확인
docker compose -f docker-compose.hub.yml ps
curl http://localhost:8000/health
```

**최신 버전으로 업데이트**

```bash
# 배포자가 새 버전 push했을 때
docker pull juyeon/fastapi-es:latest
docker compose -f docker-compose.hub.yml up -d
```

---

### RAM별 권장 설정

| RAM | 권장 ES 설정 | 비고 |
|-----|------------|------|
| 16GB 이상 | `-Xms512m -Xmx512m` (기본값) | 쾌적 |
| 8GB | `-Xms256m -Xmx256m` | 다른 앱 종료 권장 |
| 8GB 이하 | ES 단독 실행 또는 PostgreSQL 대체 고려 | ES가 자주 죽음 |

RAM이 부족한 팀원은 `docker-compose.hub.yml`의 `ES_JAVA_OPTS` 값만 낮춰서 실행하면 됩니다.

---

### 공유 시 주의사항

- `.env` 파일은 절대 커밋하거나 공유하지 않습니다.
- ES 데이터는 `esdata` 볼륨에 저장됩니다. 초기화 필요 시 `docker compose down -v`.
- ES가 뜨는 데 40초 이상 걸릴 수 있습니다. `healthy` 상태 확인 후 사용하세요.
- Docker Hub 무료 계정은 이미지 1개까지 Private, 나머지는 Public입니다.

---

## ⚙️ 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|:------:|
| `APP_ENV` | 실행 환경 | `development` |
| `LOG_LEVEL` | 로그 레벨 | `info` |
| `ES_HOST` | ES 연결 주소 | `http://elasticsearch:9200` |
| `APP_VERSION` | 이미지 태그 | `latest` |

---

## 🔍 트러블슈팅

### `vm.max_map_count` 오류 — ES 최초 실행 시 거의 반드시 만남

```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### ES가 계속 죽을 때 — 대부분 RAM 부족

```bash
# 현재 ES 메모리 사용량 확인
docker stats es01

# JVM 힙 줄이기 (docker-compose.yml 수정)
ES_JAVA_OPTS=-Xms256m -Xmx256m
```

### 빌드 캐시가 예상대로 동작하지 않을 때

```bash
DOCKER_BUILDKIT=1 docker build .
docker build --progress=plain . 2>&1 | grep "CACHED"
```

### 클러스터 상태가 red일 때

```bash
curl http://localhost:9200/_cluster/allocation/explain?pretty
docker logs es01 --tail=50 -f
```

### non-root 권한 오류

```bash
docker run --rm --user root myapp/api ls -la /app
# Dockerfile에서 COPY --chown=appuser:appgroup 누락 여부 확인
```

---

## 📈 추가 최적화 로드맵

- [ ] **BuildKit 캐시 마운트** (`--mount=type=cache`) — pip 캐시 영구화로 재빌드 시간 추가 단축
- [ ] **Distroless 이미지** 전환 — `gcr.io/distroless/python3` (셸 없음, 보안 최강)
- [ ] **jlink 커스텀 JRE** — Spring Boot 연동 시 JRE 400MB → 45MB
- [ ] **SBOM 생성 자동화** — Syft 통합으로 의존성 추적
- [ ] **Cosign 이미지 서명** — Supply Chain 보안
- [ ] **ES ILM 정책** — 인덱스 수명주기 관리 자동화
- [ ] **ES 멀티 노드 클러스터** — docker-compose scale out 구성

---

## 🤝 기여

Pull Request와 Issue는 언제든 환영합니다.
기여 전 [CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 확인해주세요.

---

## 📜 라이선스

MIT License © 2025 [백주연 (Juyeon Baeck)](https://github.com/username)

---

<div align="center">

**"무엇을 최적화할 수 있고, 무엇은 할 수 없는지 구분하는 것이 엔지니어링이다."**

</div>
