# 🚀 USAGE — ELK 스택 활용 가이드

<div align="center">

스택 실행 이후 실제로 사용하는 방법을 단계별로 설명합니다.

[포트포워딩](#-포트포워딩-설정-vm-환경) · [API 사용법](#-api-사용법) · [데이터 색인검색 실습](#-데이터-색인검색-실습) · [Kibana 대시보드](#-kibana-대시보드-설정)

</div>

> 스택 실행이 아직 안 됐다면 → [README.md 빠른 시작](./README.md#-빠른-시작-3단계) 먼저 진행하세요.

---

## 🔌 포트포워딩 설정 (VM 환경)

VirtualBox/VMware 같은 로컬 VM에서 실행하는 경우, 호스트(내 PC) 브라우저에서 VM 안 컨테이너로 접근하려면 포트포워딩이 필요합니다.

```
내 PC 브라우저 → localhost:8000
      ↓ (VirtualBox NAT)
VM (10.0.2.15):8000
      ↓
Docker 컨테이너:8000
```

### VirtualBox 포트포워딩 설정

1. VirtualBox GUI에서 해당 VM 선택
2. `설정 → 네트워크 → 어댑터 1 → 고급 → 포트 포워딩`
3. 아래 규칙 3개 추가

| 이름 | 호스트 포트 | 게스트 IP | 게스트 포트 |
|------|:----------:|:---------:|:----------:|
| fastapi | 8000 | 10.0.2.15 | 8000 |
| kibana | 5601 | 10.0.2.15 | 5601 |
| elasticsearch | 9200 | 10.0.2.15 | 9200 |

> VM 재시작 없이 바로 적용됩니다.

### VM IP 확인 방법

```bash
hostname -I
# 예시: 10.0.2.15 172.17.0.1 172.18.0.1
# → 첫 번째 IP가 게스트 IP
```

### 접속 확인

포트포워딩 설정 후 호스트 PC 브라우저에서 접속:

| 서비스 | URL |
|--------|-----|
| FastAPI Swagger | http://localhost:8000/docs |
| Elasticsearch | http://localhost:9200 |
| Kibana | http://localhost:5601 |

> macOS Docker Desktop / Windows WSL 환경은 포트포워딩 없이 `localhost`로 바로 접속됩니다.

---

## 📡 API 사용법

FastAPI는 `http://localhost:8000`에서 REST API를 제공합니다.
브라우저에서 `http://localhost:8000/docs`에 접속하면 Swagger UI로 모든 엔드포인트를 테스트할 수 있습니다.

### 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/health` | API 및 ES 상태 확인 |
| `POST` | `/items` | 데이터 색인 (ES에 문서 저장) |
| `GET` | `/items/search?q=검색어` | 전문 검색 |
| `DELETE` | `/items/{id}` | 문서 삭제 |

### Swagger UI 사용법

1. `http://localhost:8000/docs` 접속
2. 엔드포인트 클릭 → `Try it out` 버튼
3. 파라미터 입력 → `Execute`
4. 응답 결과 확인

---

## 🗂️ 데이터 색인/검색 실습

터미널에서 curl로 전체 흐름을 실습합니다.

### 1단계 — 상태 확인

```bash
curl http://localhost:8000/health
```

```json
{"api": "ok", "es_status": "green"}
```

`es_status`가 `green`이면 준비 완료입니다.

---

### 2단계 — 데이터 색인

`POST /items`로 ES에 문서를 저장합니다.

```bash
# 첫 번째 문서
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Docker 최적화", "description": "멀티 스테이지 빌드로 이미지 크기를 84% 줄였습니다.", "tag": "devops"}'

# 두 번째 문서
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Elasticsearch 검색", "description": "역색인 구조로 빠른 전문 검색을 지원합니다.", "tag": "search"}'

# 세 번째 문서
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Kibana 대시보드", "description": "ES 데이터를 시각화하는 도구입니다.", "tag": "visualization"}'
```

응답 예시:
```json
{"id": "abc123", "title": "Docker 최적화", "description": "...", "tag": "devops"}
```

---

### 3단계 — 검색

`GET /items/search?q=검색어`로 전문 검색합니다. `title` 필드에 가중치 2배가 적용됩니다.

```bash
# "Docker" 검색
curl "http://localhost:8000/items/search?q=Docker"

# "검색" 검색
curl "http://localhost:8000/items/search?q=검색"

# "시각화" 검색
curl "http://localhost:8000/items/search?q=시각화"
```

응답 예시:
```json
{
  "total": 1,
  "results": [
    {
      "id": "abc123",
      "title": "Docker 최적화",
      "description": "멀티 스테이지 빌드로 이미지 크기를 84% 줄였습니다.",
      "tag": "devops"
    }
  ]
}
```

---

### 4단계 — ES 직접 조회

FastAPI를 거치지 않고 ES에 직접 쿼리할 수도 있습니다.

```bash
# 전체 인덱스 목록
curl http://localhost:9200/_cat/indices?v

# items 인덱스 전체 문서 조회
curl http://localhost:9200/items/_search?pretty

# 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty
```

---

### 5단계 — 문서 삭제

```bash
# 색인 시 응답받은 id로 삭제
curl -X DELETE http://localhost:8000/items/abc123
```

```json
{"deleted": "abc123"}
```

---

## 📊 Kibana 대시보드 설정

Kibana에서 ES에 저장된 데이터를 시각화합니다.

### 1단계 — Kibana 접속

브라우저에서 `http://localhost:5601` 접속

---

### 2단계 — Data View 생성

ES 인덱스를 Kibana에서 인식하도록 Data View를 먼저 만들어야 합니다.

1. 좌측 메뉴 → `Stack Management`
2. `Kibana` → `Data Views`
3. `Create data view` 클릭
4. 아래와 같이 입력:

| 항목 | 값 |
|------|-----|
| Name | `items` |
| Index pattern | `items*` |
| Timestamp field | `I don't want to use the time filter` |

5. `Save data view to Kibana` 클릭

---

### 3단계 — Discover로 데이터 확인

1. 좌측 메뉴 → `Discover`
2. 상단 Data View 드롭다운에서 `items` 선택
3. 색인한 문서들이 목록으로 표시됨

---

### 4단계 — 간단한 시각화 만들기

1. 좌측 메뉴 → `Visualize Library`
2. `Create visualization` 클릭
3. `Lens` 선택
4. 우측 패널에서 Data View → `items` 선택
5. 예시: `tag` 필드를 X축으로 드래그 → 태그별 문서 수 막대 차트 생성
6. `Save` 클릭 → 이름 지정 후 저장

---

### 5단계 — 대시보드에 추가

1. 좌측 메뉴 → `Dashboard`
2. `Create dashboard` 클릭
3. `Add from library` → 방금 만든 시각화 선택
4. `Save` 클릭

---

## 💡 팁

**데이터 초기화가 필요할 때**
```bash
docker compose -f docker-compose.hub.yml down -v
docker compose -f docker-compose.hub.yml up -d
```
> `-v` 옵션으로 ES 볼륨까지 삭제되어 인덱스가 초기화됩니다.

**실시간 로그 모니터링**
```bash
docker compose -f docker-compose.hub.yml logs -f
```

**특정 서비스 로그만 보기**
```bash
docker logs fastapi01 -f
docker logs es01 -f
docker logs kibana01 -f
```

---

<div align="center">

← [README.md](./README.md) · [DETAILS.md](./DETAILS.md) →

</div>
