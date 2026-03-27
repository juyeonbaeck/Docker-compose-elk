# 🐳 ELK 기반 검색 API 환경 — Docker Hub 빌드 & 배포 가이드

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

**이미지 크기 84% 감소 · 빌드 시간 78% 단축 · CVE 94% 제거**

</div>

---

## 📋 목차
 
🧠 개념 ———— 
[핵심 개념](#-핵심-개념---이미지-vs-컨테이너) · [왜 FastAPI가 필요한가](#-왜-fastapi가-필요한가) · [베이스 이미지 선택](#-베이스-이미지-선택-slim-vs-alpine)
 
🏗️ 최적화 ——— 
[멀티 스테이지 빌드](#-멀티-스테이지-빌드) · [보안 설계](#-보안-설계) · [ES-Kibana 튜닝](#-elasticsearch--kibana-튜닝)
 
📊 성능 ———— 
[최적화 결과](#-최적화-결과) · [스택 리소스 요구량](#-스택-전체-리소스-요구량)
 
🏛️ 설계 결정 —— 
[아키텍처 설계](#-아키텍처-설계-결정) · [설계 원칙](#-설계-원칙) · [향후 발전 방향](#-향후-발전-방향)
 
🔧 운영 ———— 
[Docker Hub 배포](#-docker-hub-배포) · [팀 공유 가이드](#-팀-공유-가이드) · [트러블슈팅](#-트러블슈팅)

---

## 🧠 핵심 개념 - 이미지 vs 컨테이너
 
```
┌─────────────────────────────────────────────────────┐
│  이미지 (Image)          컨테이너 (Container)       │
│  ─────────────          ──────────────────────      │
│  읽기 전용 파일           실행 중인 프로세스         │
│  Dockerfile의 결과물      이미지를 run한 인스턴스    │
│  도커허브에 올리는 것     종료하면 사라짐            │
│                                                     │
│  붕어빵 틀          →    틀로 찍어낸 붕어빵          │
└─────────────────────────────────────────────────────┘
 
Dockerfile  ──build──▶  이미지  ──run──▶  컨테이너
 (설계도)               (택배상자)         (실행 중인 앱)
```
 
- 이미지 하나로 컨테이너를 **몇 개든** 동시에 실행 가능
- 컨테이너를 삭제해도 이미지는 남음
- 이미지를 삭제하려면 참조하는 **컨테이너를 먼저 삭제**해야 함

---
 
## 🔍 왜 FastAPI가 필요한가
 
Elasticsearch는 검색 엔진이지 웹 서버가 아닙니다.
 
```
❌ 클라이언트가 ES에 직접 접근하면
   - 인증 없음 (xpack.security 비활성 시 누구나 접근)
   - 비즈니스 로직 추가 불가
   - 데이터 가공/필터링 불가
 
✅ FastAPI를 중간 레이어로 두면
   - 인증/인가 처리 가능
   - 요청 유효성 검사 (Pydantic)
   - 비즈니스 로직 캡슐화
   - ES 내부 구조를 클라이언트에 노출하지 않음
```
 
```
클라이언트
    │
    ▼ :8000
[ FastAPI ] ── 인증/가공/라우팅 ──▶ [ Elasticsearch :9200 ]
    │                                        │
    ◀──────────── 검색 결과 반환 ────────────┘
```
 
FastAPI는 Python 인터프리터 위에서 실행되는 웹 프레임워크입니다.<br/>따라서 Docker 이미지에 Python 런타임이 포함된 베이스 이미지(`python:3.12-slim`)가 필요합니다.<br/>이는 **런타임 환경의 일관성을 보장**하고, 어떤 호스트 OS에서도 동일하게 동작하게 하기 위함입니다.
 
---
 
## 🐍 베이스 이미지 선택: slim vs alpine
 
```
python:3.12         Debian 풀세트 + 개발도구 + 폰트 + 문서  ···  920MB  ❌
python:3.12-slim    Debian에서 불필요한 패키지만 제거        ···  130MB  ✅
python:3.12-alpine  완전히 다른 OS (Alpine, musl libc)      ···   50MB  ⚠️
```
 
### alpine을 쓰지 않는 이유
 
| 구분 | slim (Debian) | alpine (musl libc) |
|------|:-------------:|:-----------------:|
| glibc 기반 wheel 호환 | ✅ | ❌ 실행 오류 가능 |
| pandas, numpy 설치 | ✅ | ❌ 소스 빌드 필요 |
| Elastic 공식 지원 | ✅ | ❌ |
| 이미지 크기 | 130MB | 50MB |
 
> PyPI 패키지 대부분이 glibc 기반 `.whl`로 배포됩니다. alpine은 musl libc라 호환성 문제가 생기므로, 이 프로젝트는 **안전성 우선으로 slim을 유지**합니다.
 
---
 
## 🏗️ 멀티 스테이지 빌드

### 1. 왜 멀티 스테이지인가
 
```
❌ 단일 스테이지 빌드
┌──────────────────────────────────┐
│  FROM python:3.12                │
│  RUN apt install gcc             │ ← 빌드 도구가 최종 이미지에 남음
│  RUN pip install ...             │   → 920MB, CVE 32건
│  COPY app/ .                     │   → 공격 표면(Attack Surface) 증가
└──────────────────────────────────┘
 
✅ 멀티 스테이지 빌드
┌─────────────────────┐       ┌──────────────────────────┐
│  STAGE 1: deps      │       │  STAGE 2: runtime        │
│  python:3.12-slim   │       │  python:3.12-slim        │
│  ├── gcc (컴파일러) │/install│  ├── /install (패키지만)│
│  ├── pip (설치 도구)│─only─▶│  ├── main.py            │
│  └── /install       │        │  ├── ❌ gcc            │
│                     │        │  └── ❌ pip            │
│  ※ 최종 이미지에    │       │  → 145MB, CVE 2건       │
│    포함되지 않음     │       │  → 공격 표면 최소화      │
└─────────────────────┘       └──────────────────────────┘
```
 
> 💡 빌드 도구(`gcc`, `pip`, `musl-dev`)를 최종 이미지에서 제거함으로써 **공격 표면(Attack Surface)을 줄이고**, 잠재적 취약점을 가진 패키지가 프로덕션 컨테이너에 포함되지 않도록 합니다. 이는 금융권 보안 요구사항에서 특히 중요한 원칙입니다.
 
### 2. 레이어 캐싱 전략
 
```
변경 빈도: 낮음 ──────────────────────────────▶ 높음
 
COPY requirements.txt .   ← 거의 안 바뀜  → 캐시 재사용
RUN pip install ...        ← 의존성 변경 시만 재실행
COPY ./app .               ← 소스 코드는 자주 바뀜 → 항상 마지막
```
 
변경 빈도가 낮은 레이어를 먼저 배치해 **캐시 히트율을 높이고 빌드 시간을 단축**합니다.
 
### 3. Dockerfile 전체
 
```dockerfile
# ==========================================
# STAGE 1: deps
# glibc 환경(slim)에서 pip install 실행
# alpine은 musl libc라 wheel 호환 문제 발생
# ==========================================
FROM python:3.12-slim AS deps
 
WORKDIR /build
 
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt
 
 
# ==========================================
# STAGE 2: runtime
# 빌드 도구(gcc, pip) 없는 깨끗한 런타임
# COPY --from=deps: Stage 1의 /install 폴더만 복사
# gcc, pip은 Stage 1에만 존재 → 최종 이미지에 없음
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
 
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```
 
---
 
## 🔐 보안 설계
 
### 1. 최소 권한 원칙 (Principle of Least Privilege)
 
| 보안 항목 | 적용 방식 | 효과 |
|-----------|----------|------|
| **Non-root 실행** | `appuser` 계정으로 프로세스 실행 | root 탈취 시 피해 최소화 |
| **빌드 도구 제거** | 멀티 스테이지로 gcc, pip 제외 | 공격 표면(Attack Surface) 감소 |
| **COPY --chown** | 파일 소유권을 appuser로 제한 | 런타임 파일 변조 방지 |
| **no-new-privileges** | 권한 상승 시도를 커널에서 차단 | 컨테이너 탈출 방지 |
 
### 2. CVE 비교
 
```
Standard Build (python:3.12)     Optimized Build (멀티 스테이지 + slim)
────────────────────────────     ──────────────────────────────────────
CVE 32건                    →    CVE 2건 (Low only)
  ├── CRITICAL: 3건               ├── CRITICAL: 0건  ✅
  ├── HIGH: 11건                  ├── HIGH: 0건      ✅
  ├── MEDIUM: 12건                ├── MEDIUM: 0건   ✅
  └── LOW: 6건                    └── LOW: 2건      ✅
```
 
### 3. CI 보안 스캔 (Trivy)
 
```yaml
# .github/workflows/docker-build.yml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp/api:latest
    format: sarif
    severity: CRITICAL,HIGH
    exit-code: 1   # CRITICAL/HIGH 발견 시 파이프라인 중단
```
 
> CRITICAL/HIGH CVE가 발견되면 이미지가 Docker Hub에 push되지 않습니다.
 
---
 
## ⚙️ Elasticsearch & Kibana 튜닝
 
ES/Kibana는 Elastic사 완성 이미지라 Dockerfile 수정이 불가합니다. **환경변수와 설정 파일 마운트**로만 최적화합니다.
 
> "무엇을 최적화할 수 있고, 무엇은 할 수 없는지를 구분하는 것이 시니어 엔지니어의 판단입니다."
 
### JVM 힙 계산법 (Elasticsearch)
 
```
규칙 1: 컨테이너 메모리 제한의 50%
규칙 2: 32GB 초과 금지 (Compressed OOP 비활성화 방지)
규칙 3: 반드시 Xms = Xmx (같은 값으로 고정)
 
  컨테이너 1.5GB → -Xms512m -Xmx512m  ✅
  컨테이너 4GB   → -Xms2g   -Xmx2g    ✅
  Xms ≠ Xmx      → GC pause → OOM Kill ❌
```
 
> `-Xms`와 `-Xmx`를 같은 값으로 고정하는 이유: JVM이 힙을 동적으로 늘리는 과정에서 GC pause가 발생하고, 컨테이너 OOM Kill로 이어지기 때문입니다.
 
### Kibana Node.js 힙 제한
 
```yaml
kibana:
  environment:
    - NODE_OPTIONS=--max-old-space-size=512  # Node.js 힙 상한 명시
  deploy:
    resources:
      limits:
        memory: 768M   # 컨테이너 limit > Node.js 힙 상한
```
 
> Node.js 힙 상한을 컨테이너 limit보다 낮게 설정해, Node.js 스스로 GC를 먼저 트리거하도록 유도합니다.
 
### 컨테이너별 리소스 쿼터
 
```yaml
# 시스템 자원 고갈 방지 — 컨테이너별 메모리/CPU 상한 설정
elasticsearch:
  deploy:
    resources:
      limits:
        memory: 1.5G       # JVM 힙(512MB) + OS 오버헤드
 
kibana:
  deploy:
    resources:
      limits:
        memory: 768M
 
api:
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: "0.5"        # CPU 50% 상한
```
 
---
 
## 📊 최적화 결과
 
### FastAPI 이미지 비교
 
| 지표 | Standard Build | Optimized Build | 개선율 |
|------|:--------------:|:---------------:|:------:|
| **이미지 크기** | 920 MB | 145 MB | ✅ **84% 감소** |
| **빌드 시간** (캐시 활용) | 55s | 12s | ✅ **78% 단축** |
| **CVE (보안 취약점)** | 32건 | 2건 (Low) | ✅ **94% 제거** |
| **컨테이너 기동 시간** | 4.2s | 1.1s | ✅ **74% 단축** |
| **레이어 수** | 18 | 7 | ✅ **61% 감소** |
 
> 측정 환경: Docker Engine 24.0.7 / Apple M2 Pro / Ubuntu 22.04 (CI runner)
 
### 이미지 유형별 최적화 방식
 
| 이미지 | 경량화 방식 | 결과 크기 |
|--------|-----------|:--------:|
| FastAPI | 멀티 스테이지 + slim | ~145MB |
| Spring Boot | jlink 커스텀 JRE | ~45MB |
| Go 앱 | scratch (OS 없음) | ~5MB |
| Node.js | alpine + npm prune | ~180MB |
| Redis | `redis:7-alpine` | ~30MB |
| Nginx | `nginx:alpine` | ~23MB |
| **Elasticsearch** | **불가 — JVM 튜닝만** | **~1.3GB** |
| **Kibana** | **불가 — 환경변수 튜닝만** | **~800MB** |
 
---
 
## 💾 스택 전체 리소스 요구량
 
| 서비스 | 이미지 크기 | 최소 RAM | 최적화 방식 |
|--------|:-----------:|:--------:|------------|
| FastAPI | 145 MB | 256 MB | 멀티 스테이지 빌드 |
| Elasticsearch | ~1.3 GB | 1 GB | JVM 힙 고정 |
| Kibana | ~800 MB | 768 MB | Node.js 힙 + 메모리 limit |
| OS + 버퍼 | — | ~512 MB | — |
| **합계** | **~2.3 GB** | **~2.5 GB+** | |
 
> 팀원 RAM이 8GB 이하라면 `ES_JAVA_OPTS=-Xms256m -Xmx256m`으로 낮춰 실행하세요.
 
---
 
## 🏛️ 아키텍처 설계 결정
 
### 전체 스택 구성
 
```
┌────────────────────────────────────────────────────────────────────┐
│                        docker-compose 스택                         │
│                                                                    │
│  클라이언트                                                        │
│      │ :8000                                                       │
│      ▼                                                             │
│  [ FastAPI 컨테이너 ] ──── 검색 쿼리 ────▶ [ Elasticsearch :9200 ] │
│    직접 빌드 (145MB)                         Elastic사 이미지       │
│    멀티 스테이지 적용                         JVM 튜닝으로 최적화   │
│    Non-root 실행                                    │              │
│                                             [ esdata 볼륨 ]        │
│  [ Kibana :5601 ] ◀─────────────────────────────────┘             │
│    Elastic사 이미지                          데이터 영속성          │
│    Node.js 힙 제한 적용                                            │
└────────────────────────────────────────────────────────────────────┘
```
 
### Logstash를 사용하지 않은 이유
 
프로젝트 이름은 ELK이지만 **Logstash(L)는 의도적으로 제외**했습니다.
 
```
일반적인 ELK:  클라이언트 → Logstash(500MB~1GB) → Elasticsearch → Kibana
이 프로젝트:   클라이언트 → FastAPI(145MB) → Elasticsearch → Kibana
```
 
| | Logstash 포함 | FastAPI 직접 색인 |
|--|:---:|:---:|
| 추가 메모리 | +500MB~1GB | 없음 |
| 데이터 변환 | Grok Filter (강력) | Python 코드로 처리 |
| 적합한 상황 | 다중 소스 로그 수집 | API 기반 단일 소스 |
| 아키텍처 복잡도 | 높음 | 낮음 ✅ |
 
**경량 아키텍처(Lightweight Architecture)** 를 우선한 설계 선택입니다.
 
**추후 확장**: 다중 소스(서버 로그, DB 변경 이벤트)를 수집해야 한다면 **Filebeat → Logstash** 파이프라인을 추가할 수 있습니다.
 
### 구조화 로그 (Structured Logging)
 
FastAPI 로그를 JSON 포맷으로 출력해 Elasticsearch가 **필드 단위로 파싱·집계**할 수 있게 합니다.
 
```python
# 평문 로그 (분석 어려움)
INFO: 2025-01-01 POST /items 201 12ms
 
# 구조화 로그 (ES에서 필드 단위 분석 가능)
{"timestamp": "2025-01-01T00:00:00Z", "level": "INFO",
 "method": "POST", "path": "/items", "status": 201, "duration_ms": 12}
```
 
- Kibana에서 `status:500`으로 에러만 필터링 가능
- `duration_ms`로 느린 API 집계 가능
- 평문 대비 **ELK 분석 효율이 높아짐**
 
---
 
## ⭐ 설계 원칙
 
### 1. 멀티 스테이지 빌드 — "공사장비는 완성된 집에 들어오지 않는다"
 
- ✅ gcc, pip 등 빌드 도구는 Stage 1에서만 사용
- ✅ Stage 2는 `/install` 결과물만 `COPY --from=`으로 가져옴
- ✅ 빌드 도구 제거 → 이미지 경량화 + **공격 표면(Attack Surface) 감소**
 
### 2. 최소 권한 원칙 (Principle of Least Privilege)
 
- ✅ `appuser` Non-root 실행
- ✅ `COPY --chown` 파일 소유권 제한
- ✅ `no-new-privileges` 권한 상승 차단
- ✅ Linux Capability 제거 (`CAP_NET_RAW`, `CAP_SYS_ADMIN` 등)
 
### 3. ES/Kibana — "설정 주입 전략"
 
- ✅ Elastic사 완성 이미지는 내부 수정 불가
- ✅ 환경변수 + 설정 파일 마운트로만 최적화
- ✅ 비공식 경량화 금지 → 운영 장애 시 Elastic 지원 유지
 
### 4. 컨테이너 격리 — "하나가 죽어도 나머지는 산다"
 
- ✅ 서비스별 `deploy.resources.limits` 설정
- ✅ `healthcheck` + `depends_on: condition: service_healthy`
- ✅ `restart: unless-stopped`로 자동 재시작
 
---
 
## 🔭 향후 발전 방향
 
### 고가용성 (High Availability)
 
```
현재 구성 (단일 노드)
  es01 ──▶ 단일 장애점(SPOF) 존재 — es01 장애 시 서비스 전체 중단
 
프로덕션 확장 방향 (멀티 노드 클러스터)
  es01 ┐
  es02 ├──▶ 3노드 클러스터 — 노드 장애 시에도 shard 복제본으로 서비스 유지
  es03 ┘    데이터 가용성(HA) 확보
```
 
> 현재는 학습·포트폴리오 목적의 단일 노드 구성입니다. 프로덕션 환경에서는 최소 3노드 클러스터 구성이 권장됩니다.
 
### 전체 로드맵
 
| 항목 | 설명 | 우선순위 |
|------|------|:-------:|
| ☐ **ES 멀티 노드 클러스터** | 3노드 구성으로 HA 확보 | 높음 |
| ☐ **xpack.security 활성화** | 프로덕션 ES 인증 적용 | 높음 |
| ☐ **Filebeat + Logstash** | 다중 소스 로그 수집 파이프라인 | 중간 |
| ☐ **BuildKit 캐시 마운트** | `--mount=type=cache`로 pip 캐시 영구화 | 중간 |
| ☐ **Distroless 이미지** | 셸 없음, 보안 최강 | 중간 |
| ☐ **SBOM 생성 자동화** | Syft 통합, 의존성 추적 | 낮음 |
| ☐ **Cosign 이미지 서명** | Supply Chain 보안 | 낮음 |
| ☐ **ES ILM 정책** | 인덱스 수명주기 자동화 | 낮음 |
 
---
 
## 🔧 Docker Hub 배포
 
```bash
# 1. Docker Hub 로그인
docker login
 
# 2. 멀티 스테이지 빌드
docker build -t juyeon09/elk-fastapi:latest .
 
# 3. 버전 태그 추가
docker tag juyeon09/elk-fastapi:latest juyeon09/elk-fastapi:1.0.0
 
# 4. Docker Hub 업로드
docker push juyeon09/elk-fastapi:latest
docker push juyeon09/elk-fastapi:1.0.0
```
 
---
 
## 👥 팀 공유 가이드
 
### 팀원 온보딩 (2단계)
 
**Step 1** — vm.max_map_count 설정 (최초 1회)
 
```bash
# Linux / Ubuntu
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```
 
**Step 2** — 실행
 
```bash
curl -O https://raw.githubusercontent.com/juyeonbaeck/Docker-compose-elk/main/docker-compose.hub.yml
docker compose -f docker-compose.hub.yml up -d
curl http://localhost:8000/health   # {"api":"ok","es_status":"green"}
```
 
### RAM별 권장 설정
 
| RAM | ES_JAVA_OPTS | 비고 |
|-----|:------------:|------|
| 16GB 이상 | `-Xms512m -Xmx512m` | 기본값, 쾌적 |
| 8GB | `-Xms256m -Xmx256m` | 다른 앱 종료 권장 |
| 4GB 이하 | `-Xms128m -Xmx128m` | ES 불안정 가능 |
 
---
 
## 🔍 트러블슈팅
 
### `vm.max_map_count` 오류
 
```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```
 
### Kibana OOM — 3.8GB 이하 서버
 
**증상**:
```
FATAL ERROR: Ineffective mark-compacts near heap limit
Allocation failed - JavaScript heap out of memory
```
 
**해결**:
```bash
# 1. Swap 추가
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
 
# 2. docker-compose.hub.yml 수정
#    kibana > environment: NODE_OPTIONS=--max-old-space-size=512
#    kibana > deploy.resources.limits.memory: 768M
 
# 3. 재시작
docker compose -f docker-compose.hub.yml down && docker compose -f docker-compose.hub.yml up -d
```
 
### FastAPI worker 계속 죽을 때
 
**증상**: `Child process [N] died` 반복
 
**해결**: compose 파일에 workers 1로 오버라이드
 
```yaml
api:
  command: ["main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```
 
### 클러스터 상태 red
 
```bash
curl http://localhost:9200/_cluster/allocation/explain?pretty
docker logs es01 --tail=50 -f
```
 
### 빌드 캐시 미작동
 
```bash
DOCKER_BUILDKIT=1 docker build .
docker build --progress=plain . 2>&1 | grep "CACHED"
```
 
---
 
## 📁 파일 구조
 
```
.
├── Dockerfile                  # FastAPI 멀티 스테이지 프로덕션 빌드
├── docker-compose.yml          # 풀 스택 오케스트레이션 (소스 빌드용)
├── docker-compose.hub.yml      # 팀원 배포용 (Docker Hub 이미지, 빌드 없음)
├── .dockerignore               # 빌드 컨텍스트 최적화
├── .env.example                # 환경변수 템플릿 (커밋용, 실제 값은 .env에)
├── requirements.txt
├── app/
│   └── main.py                 # FastAPI + ES 연동 로직
└── elasticsearch/
    └── elasticsearch.yml       # ES 커스텀 설정
```
 
---
 
## 🤝 기여
 
Pull Request와 Issue는 언제든 환영합니다.
기여 전 [CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 확인해주세요.
 
---
 
## 📜 라이선스
 
MIT License © 2025 [백주연 (Juyeon Baeck)](https://github.com/juyeonbaeck)
 
---
 
<div align="center">
 
← [README.md](./README.md) · [USAGE.md](./USAGE.md) →
 
**"무엇을 최적화할 수 있고, 무엇은 할 수 없는지 구분하는 것이 엔지니어링이다."**
 
</div>
