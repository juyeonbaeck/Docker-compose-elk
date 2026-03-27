# 🐳 ELK 기반 검색 API 환경 — Docker Hub에서 바로 실행하기

<div align="center">

![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED?style=flat-square&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.13-005571?style=flat-square&logo=elasticsearch&logoColor=white)
![Kibana](https://img.shields.io/badge/Kibana-8.13-E8488B?style=flat-square&logo=kibana&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**`docker compose up` 하나로 FastAPI + Elasticsearch + Kibana 풀 스택을 실행합니다.**

Python, Java, Elasticsearch를 로컬에 설치할 필요 없습니다.

</div>

---

## 📦 프로젝트 설명

FastAPI(Python 웹 서버) + Elasticsearch(검색 엔진) + Kibana(시각화 대시보드)를 Docker로 묶어서 실행하는 풀 스택 구성입니다.

- **FastAPI** — 검색 API 서버. 클라이언트 요청을 받아 ES에 쿼리를 날리고 결과를 반환합니다.
- **Elasticsearch** — 데이터 색인 및 검색 엔진입니다.
- **Kibana** — ES 데이터를 브라우저에서 시각화합니다.

> FastAPI 이미지는 멀티 스테이지 빌드로 최적화돼 있습니다 (920MB → 145MB, CVE 94% 제거).
> 최적화 상세 내용은 [DETAILS.md](./DETAILS.md)를 참고하세요.

---

## 사전 요구사항

로컬에 아래 두 가지만 설치돼 있으면 됩니다.

| 항목 | 버전 | 확인 방법 |
|------|------|----------|
| Docker Engine | 24.0 이상 | `docker --version` |
| Docker Compose V2 | 2.0 이상 | `docker compose version` |

> Python, Java, Elasticsearch를 따로 설치할 필요 없습니다. 전부 컨테이너 안에 들어있습니다.

---

## 🚀 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/username/docker-optimized-production.git
cd docker-optimized-production
```

### 2. vm.max_map_count 설정 (처음 한 번만)

Elasticsearch가 요구하는 Linux 커널 설정입니다. 컨테이너가 아닌 **호스트 OS**에서 실행해야 합니다.

```bash
# Linux
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# macOS (Docker Desktop)
# Docker Desktop → Settings → Resources → Advanced → vm.max_map_count = 262144
```

### 3. 전체 스택 실행

```bash
docker compose up --build -d
```

처음 실행 시 이미지 다운로드와 FastAPI 빌드로 수 분이 걸릴 수 있습니다.
ES가 완전히 뜨는 데 약 40초 걸립니다.

### 4. 실행 상태 확인

```bash
docker compose ps
```

모든 서비스가 `healthy` 상태이면 준비 완료입니다.

---

## 🌐 서비스 포트

| 서비스 | 주소 | 용도 |
|--------|------|------|
| FastAPI | http://localhost:8000 | REST API 서버 |
| FastAPI Docs | http://localhost:8000/docs | Swagger UI (자동 생성 API 문서) |
| Elasticsearch | http://localhost:9200 | ES HTTP API |
| Kibana | http://localhost:5601 | 데이터 시각화 대시보드 |

---

## 🧪 동작 확인

```bash
# API 상태 확인
curl http://localhost:8000/health

# 데이터 색인
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Docker 최적화", "description": "멀티 스테이지 빌드 가이드", "tag": "devops"}'

# 검색
curl "http://localhost:8000/items/search?q=Docker"

# ES 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty

# Kibana 브라우저 접속
open http://localhost:5601
```

---

## 🛑 종료 방법

```bash
# 컨테이너만 종료 (데이터 유지)
docker compose down

# 컨테이너 + 데이터까지 완전 삭제
docker compose down -v
```

> `down`만 하면 ES에 색인한 데이터가 볼륨에 남아있어서 다음에 `up`해도 데이터가 그대로입니다.
> `-v` 옵션을 붙이면 볼륨까지 삭제되어 초기화됩니다.

---

## 💻 RAM별 권장 설정

ES는 기본적으로 512MB 힙을 사용합니다. 로컬 RAM이 부족하면 `docker-compose.yml`에서 아래 값을 조정하세요.

| 로컬 RAM | 권장 설정 |
|---------|----------|
| 16GB 이상 | `ES_JAVA_OPTS=-Xms512m -Xmx512m` (기본값) |
| 8GB | `ES_JAVA_OPTS=-Xms256m -Xmx256m` |
| 8GB 이하 | ES 실행이 불안정할 수 있습니다 |

---

## 📁 파일 구조

```
.
├── Dockerfile                  # FastAPI 멀티 스테이지 빌드
├── docker-compose.yml          # 풀 스택 오케스트레이션
├── docker-compose.hub.yml      # Docker Hub 이미지 사용 버전 (빌드 없음)
├── .dockerignore
├── .env.example                # 환경변수 템플릿
├── requirements.txt            # Python 패키지 목록
├── app/
│   └── main.py                 # FastAPI 앱
└── elasticsearch/
    └── elasticsearch.yml       # ES 커스텀 설정
```

---

## 🔍 트러블슈팅

**ES가 시작 안 될 때**
```bash
# vm.max_map_count 설정이 안 된 경우
sudo sysctl -w vm.max_map_count=262144

# 로그 확인
docker logs es01 --tail=50
```

**포트가 이미 사용 중일 때**

`docker-compose.yml`에서 포트 앞부분을 변경하세요.
```yaml
ports:
  - "9201:9200"   # 9200이 막혀있으면 9201로 변경
```

**RAM 부족으로 ES가 죽을 때**

`docker-compose.yml`에서 JVM 힙을 낮추세요.
```yaml
ES_JAVA_OPTS=-Xms256m -Xmx256m
```

---

## 📖 상세 문서

Docker 최적화 전략, 멀티 스테이지 빌드 설계 원칙, 이미지 vs 컨테이너 개념, 베이스 이미지 선택 기준, Docker Hub 배포 방법 등 기술 상세 내용은 아래 문서를 참고하세요.

→ **[DETAILS.md](./DETAILS.md)** — Docker 최적화 전략 전체 가이드

---

## 🤝 기여

[CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 확인해주세요.

---

## 📜 라이선스

MIT License © 2025 [백주연 (Juyeon Baeck)](https://github.com/username)
