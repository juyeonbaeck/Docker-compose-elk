# 🐳 ELK 기반 검색 API 환경 — Docker Hub에서 바로 실행하기

<div align="center">

![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED?style=flat-square&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.13-005571?style=flat-square&logo=elasticsearch&logoColor=white)
![Kibana](https://img.shields.io/badge/Kibana-8.13-E8488B?style=flat-square&logo=kibana&logoColor=white)
![Docker Hub](https://img.shields.io/badge/Docker%20Hub-juyeon%2Ffastapi--es-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**`docker compose up` 하나로 FastAPI + Elasticsearch + Kibana를 실행합니다.**

git clone 없이, Python/Java 설치 없이, Docker만 있으면 됩니다.

</div>

---

## 📋 목차
 [프로젝트 개요](#-프로젝트-개요)
 
🚀 시작하기 —— 
[요구사항](#-요구사항) · [빠른 시작 3단계](#-빠른-시작-3단계)  $${\color{hotpink} ← 여기만 봐도 실행 가능⭐}$$

🌐 서비스 정보 — 
[서비스 포트](#-서비스-포트) · [접속 성공 화면](#-접속-성공-화면) · [동작 확인](#-동작-확인)

⚙️ 설정 ———— 
[RAM별 권장 설정](#-ram별-권장-설정) · [환경변수](#-환경변수)

🛠️ 운영 ———— 
[종료 방법](#-종료-방법) · [최신 버전 업데이트](#-최신-버전-업데이트) · [트러블슈팅](#-트러블슈팅)

👩‍💻 개발자용 —— 
[소스 빌드](#-소스-빌드) · [파일 구조](#-파일-구조)

📖 기타 ———— 
[상세 문서](#-상세-문서) · [활용 가이드](#-활용-가이드) · [기여](#-기여) · [라이선스](#-라이선스)

---

## 📦 프로젝트 개요

FastAPI(Python 웹 서버) + Elasticsearch(검색 엔진) + Kibana(시각화 대시보드)를 Docker로 묶은 풀 스택 검색 API 환경입니다.

| 서비스 | 역할 | 이미지 출처 |
|--------|------|------------|
| **FastAPI** | 검색 API 서버. 클라이언트 요청 → ES 쿼리 → 결과 반환 | Docker Hub (`juyeon09/elk-fastapi`) |
| **Elasticsearch** | 데이터 색인 및 전문 검색 엔진 | Elastic 공식 이미지 |
| **Kibana** | ES 데이터 시각화 대시보드 | Elastic 공식 이미지 |

<img width="700" alt="image" src="https://github.com/user-attachments/assets/935f2a9b-789c-41dd-a5fd-8f8d1ec59969" />

> FastAPI 이미지는 멀티 스테이지 빌드로 최적화돼 있습니다 (920MB → 145MB, CVE 94% 제거). <br/>
> 최적화 상세 내용은 [DETAILS.md](./DETAILS.md)를 참고하세요.



---

## ✅ 요구사항

| 항목 | 버전 | 확인 방법 |
|------|------|----------|
| Docker Engine | 24.0 이상 | `docker --version` |
| Docker Compose V2 | 2.0 이상 | `docker compose version` |

> Python, Java, Elasticsearch 별도 설치 불필요. 전부 컨테이너 안에 들어있습니다.

---

## ⚡ 빠른 시작 3단계
 
> **이 섹션만 따라하면 전체 스택이 실행됩니다.**
 
### Step 1 — vm.max_map_count 설정 (처음 한 번만)
 
ES가 요구하는 커널 설정입니다. 컨테이너 밖 호스트 OS에서 실행하세요.
 
```bash
# Linux / Ubuntu (VM 포함)
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
 
# macOS (Docker Desktop)
# Docker Desktop → Settings → Resources → Advanced → vm.max_map_count = 262144
```

<img width="831" height="233" alt="image" src="https://github.com/user-attachments/assets/4f95fa03-5fcd-466a-9524-39dcbed635a8" />

 
### Step 2 — compose 파일 받기
 
```bash
curl -O https://raw.githubusercontent.com/juyeonbaeck/Docker-compose-elk/main/docker-compose.hub.yml
```

<img width="1216" height="123" alt="image" src="https://github.com/user-attachments/assets/7f03d8c6-77cc-4443-94f9-a0f8d71833e3" />

 
### Step 3 — 전체 스택 실행
 
```bash
docker compose -f docker-compose.hub.yml up -d
```

<img width="1445" height="199" alt="image" src="https://github.com/user-attachments/assets/6c222f8c-da10-4295-b570-19c8a50d4e68" />
<br/><br/>

FastAPI 이미지는 Docker Hub(`juyeon09/elk-fastapi`)에서 자동으로 받아옵니다.<br/>
ES가 완전히 뜨는 데 약 80초 걸립니다.

<img width="1442" height="255" alt="image" src="https://github.com/user-attachments/assets/e782106b-9d95-482e-9d2f-86660f931cac" /> 
<br/><br/>
 
```bash
# 실행 상태 확인 — 모든 서비스 healthy 이면 준비 완료
docker compose -f docker-compose.hub.yml ps
```

<img width="1685" height="130" alt="image" src="https://github.com/user-attachments/assets/42ac620e-6874-4fa1-bf40-4c90f2de48a0" /><br/>
<img width="1692" height="114" alt="image" src="https://github.com/user-attachments/assets/657813c3-e1b9-464b-a06f-63cf3d22b610" />


---
 
## 🌐 서비스 포트

| 서비스 | 주소 | 용도 |
|--------|------|------|
| FastAPI | http://localhost:8000 | REST API 서버 |
| FastAPI Docs | http://localhost:8000/docs | Swagger UI (자동 생성 API 문서) |
| Elasticsearch | http://localhost:9200 | ES HTTP API |
| Kibana | http://localhost:5601 | 데이터 시각화 대시보드 |

---

## 🖥️ 접속 성공 화면
 
모든 서비스가 `healthy` 상태가 되면 브라우저에서 아래 화면을 확인할 수 있습니다.
 
> 💡 로컬 VM 환경이라면 브라우저 접속 전에 **포트포워딩 설정**이 필요합니다. → [USAGE.md — 포트포워딩 가이드](./USAGE.md#-포트포워딩-설정-vm-환경)
 
<br/>
 
| FastAPI Swagger UI (`localhost:8000/docs`) | Elasticsearch (`localhost:9200`) | Kibana (`localhost:5601`) |
|:------------------------------------------:|:--------------------------------:|:-------------------------:|
|  <img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/100579d8-e640-4806-866f-a69783dc4f66" /> | <img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/bccc7ac0-088c-4bce-98f1-5d149f5422ca" /> | <img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/a4daee82-2623-4773-b5f8-df1e62003930" /> |
| API 엔드포인트 목록 및 테스트 UI | 클러스터 상태 및 인덱스 조회 | 데이터 시각화 대시보드 |
 
<br/>
 
```bash
# 터미널에서 한 번에 상태 확인
curl http://localhost:8000/health      # → {"api":"ok","es_status":"green"}
curl http://localhost:9200/_cluster/health?pretty   # → "status" : "green"
curl http://localhost:5601/api/status | python3 -m json.tool | grep level
```
 
> 다음 단계로 → **[USAGE.md](./USAGE.md)** — API 사용법 · 데이터 색인/검색 · Kibana 대시보드 설정
 
---

## 🧪 동작 확인
 
```bash
# 1. API 상태 확인
curl http://localhost:8000/health
# → {"api": "ok", "es_status": "green"}
 
# 2. 데이터 색인
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Docker 최적화", "description": "멀티 스테이지 빌드 가이드", "tag": "devops"}'
 
# 3. 검색
curl "http://localhost:8000/items/search?q=Docker"
 
# 4. ES 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty
 
# 5. Kibana 대시보드
open http://localhost:5601
```

  
---

## 💻 RAM별 권장 설정

ES는 기본 512MB JVM 힙을 사용합니다. 로컬 RAM이 부족하면 `docker-compose.hub.yml`에서 아래 값을 조정하세요.
 
| 로컬 RAM | 권장 ES 설정 | 비고 |
|---------|------------|------|
| 16GB 이상 | `-Xms512m -Xmx512m` (기본값) | 쾌적 |
| 8GB | `-Xms256m -Xmx256m` | 다른 앱 종료 권장 |
| 8GB 이하 | ES 실행 불안정 가능 | — |

---

## 💻 환경변수
 
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `ES_JAVA_OPTS` | ES JVM 힙 설정 | `-Xms512m -Xmx512m` |
| `APP_ENV` | 실행 환경 | `development` |
| `LOG_LEVEL` | 로그 레벨 | `info` |
 
---

## 🛑 종료 방법

```bash
# 컨테이너만 종료 (Elasticsearch 데이터 유지)
docker compose down

# 컨테이너 + 데이터까지 완전 삭제
docker compose down -v
```

> `down`만 하면 ES에 색인한 데이터가 볼륨에 남아있어서 다음에 `up`해도 데이터가 그대로입니다.
> `-v` 옵션을 붙이면 볼륨까지 삭제되어 초기화됩니다.

---

 
## 🔄 최신 버전 업데이트
 
```bash
docker pull juyeon09/elk-fastapi:latest
docker compose -f docker-compose.hub.yml up -d
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
 
`docker-compose.yml` 또는 `docker-compose.hub.yml`에서 호스트 포트(앞 숫자)만 변경하세요.
```yaml
ports:
  - "9201:9200"   # 9200 사용 중이면 9201로 변경
```
 
**RAM 부족으로 ES가 죽을 때**
```yaml
# ES_JAVA_OPTS 값 낮추기
ES_JAVA_OPTS=-Xms256m -Xmx256m
```
 
**클러스터 상태가 red일 때**
```bash
curl http://localhost:9200/_cluster/allocation/explain?pretty
```

 ---

## 🛠 소스 빌드
 
소스 코드를 직접 보거나 수정하고 싶을 때 사용합니다.
 
```bash
git clone https://github.com/juyeonbaeck/Docker-compose-elk.git
cd docker-optimized-production
docker compose up --build -d
```
 
---

## 📁 파일 구조

```
.
├── docker-compose.hub.yml      # ← 팀원 배포용 (이것만 있으면 실행 가능)
├── docker-compose.yml          # 소스 직접 빌드용
├── Dockerfile                  # FastAPI 멀티 스테이지 빌드
├── .dockerignore
├── .env.example                # 환경변수 템플릿
├── requirements.txt
├── app/
│   └── main.py
└── elasticsearch/
    └── elasticsearch.yml
```
 

---

## 📖 상세 문서

멀티 스테이지 빌드 원리, 이미지 빌드 & Docker Hub 배포 방법, slim vs alpine 선택 기준, ES JVM 튜닝 전략, docker run vs compose 차이 등 기술 상세 내용은 아래를 참고하세요.

→ **[DETAILS.md](./DETAILS.md)** — Docker 최적화 전략 전체 가이드

---

 
## 🚀 활용 가이드
 
스택 실행 이후 실제로 활용하는 방법을 담은 가이드입니다.
 
→ **[USAGE.md](./USAGE.md)** — 포트포워딩 설정 · API 사용법 · 데이터 색인/검색 실습 · Kibana 대시보드 설정

---

## 🤝 기여

[CONTRIBUTING.md](./CONTRIBUTING.md)를 먼저 확인해주세요.

---

## 📜 라이선스

MIT License © 2025 [백주연 (Juyeon Baeck)](https://github.com/juyeonbaeck)
