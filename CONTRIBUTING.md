# 🤝 Contributing Guide

이 레포지토리에 기여해주셔서 감사합니다.
버그 리포트, 오타 수정, 새로운 최적화 패턴 추가 모두 환영합니다.

---

## 📋 기여 전 확인사항

- 이미 열려있는 [Issues](../../issues)와 [Pull Requests](../../pulls)를 먼저 확인해주세요.
- 큰 변경사항(새 스택 추가, 구조 변경)은 PR 전에 Issue로 먼저 논의해주세요.

---

## 🔀 기여 흐름

```
1. 이 레포지토리를 Fork
2. feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 오픈
```

### 상세 절차

```bash
# 1. Fork 후 클론
git clone https://github.com/your-username/docker-optimized-production.git
cd docker-optimized-production

# 2. 브랜치 생성 (브랜치명 컨벤션은 아래 참고)
git checkout -b feat/add-redis-alpine

# 3. 변경 후 커밋
git add .
git commit -m "feat: Redis alpine 이미지 구성 추가"

# 4. 원격 브랜치에 푸시
git push origin feat/add-redis-alpine

# 5. GitHub에서 Pull Request 오픈
```

---

## 🌿 브랜치 네이밍 컨벤션

| 유형 | 형식 | 예시 |
|------|------|------|
| 새 기능 추가 | `feat/설명` | `feat/add-redis-alpine` |
| 버그 수정 | `fix/설명` | `fix/healthcheck-timeout` |
| 문서 수정 | `docs/설명` | `docs/update-readme-slim` |
| 리팩토링 | `refactor/설명` | `refactor/dockerfile-stage2` |
| 성능 개선 | `perf/설명` | `perf/layer-cache-order` |

---

## ✍️ 커밋 메시지 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/) 형식을 따릅니다.

```
<type>: <제목>

<본문 — 선택사항>
<왜 이 변경이 필요한지 설명>

<푸터 — 선택사항>
Closes #이슈번호
```

### type 목록

| type | 사용 상황 |
|------|----------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서만 변경 |
| `refactor` | 기능 변경 없는 코드 개선 |
| `perf` | 성능 개선 |
| `chore` | 빌드 설정, 패키지 업데이트 등 |

### 예시

```bash
# 좋은 예
git commit -m "feat: Node.js alpine 멀티 스테이지 예시 추가"
git commit -m "fix: ES healthcheck start_period 40s로 조정"
git commit -m "docs: slim vs alpine 선택 기준 설명 보완"

# 나쁜 예
git commit -m "수정"
git commit -m "update"
git commit -m "fix bug"
```

---

## 🧪 PR 전 로컬 검증

PR을 올리기 전에 아래를 로컬에서 확인해주세요.

```bash
# 1. 전체 스택 정상 기동 확인
docker compose up --build -d
docker compose ps   # 모든 서비스 healthy 상태인지 확인

# 2. FastAPI 이미지 크기 확인 (최적화 이전보다 커지면 안 됨)
docker image ls | grep fastapi

# 3. 헬스체크 확인
curl http://localhost:8000/health
curl http://localhost:9200/_cluster/health?pretty

# 4. 기본 동작 확인
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title": "test", "description": "contributing test", "tag": "test"}'

curl "http://localhost:8000/items/search?q=test"

# 5. 컨테이너 정리
docker compose down -v
```

---

## 📝 PR 작성 가이드

PR을 열 때 아래 항목을 포함해주세요.

```markdown
## 변경 내용
<!-- 무엇을 왜 변경했는지 -->

## 변경 유형
- [ ] 버그 수정
- [ ] 새 기능
- [ ] 문서 수정
- [ ] 리팩토링
- [ ] 성능 개선

## 테스트
- [ ] docker compose up --build 정상 실행 확인
- [ ] 모든 서비스 healthy 상태 확인
- [ ] 기존 API 동작 확인

## 이미지 크기 변화 (Dockerfile 수정 시)
| 서비스 | 변경 전 | 변경 후 |
|--------|--------|--------|
| fastapi | MB | MB |
```

---

## 🚫 이런 PR은 받지 않습니다

- `.env` 파일이 커밋에 포함된 경우
- 시크릿/API 키가 코드에 하드코딩된 경우
- 이미지 크기가 의미 없이 증가하는 변경
- 테스트 없이 기존 동작을 깨는 변경
- `docker-compose.yml`에서 `ES_JAVA_OPTS` Xms ≠ Xmx 설정 (GC pause 유발)

---

## 💬 질문이 있다면

Issue를 열거나, PR 코멘트로 남겨주세요.

---

## 📜 라이선스

이 레포지토리에 기여하면 [MIT License](./LICENSE) 조건에 동의한 것으로 간주합니다.
