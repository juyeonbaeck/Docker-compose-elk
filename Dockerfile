# ==========================================
# STAGE 1: deps
# 빌드 도구 포함 환경에서 의존성만 설치
# ==========================================
FROM python:3.12-slim AS deps

WORKDIR /build

# 레이어 캐싱 전략: requirements 먼저 → 소스 코드 나중
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================================
# STAGE 2: runtime
# 빌드 도구 없는 경량 이미지 — 실제 서버에 올라가는 것
# ==========================================
FROM python:3.12-slim AS runtime

# non-root 유저 생성 (PoLP)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# deps 스테이지에서 설치된 패키지만 복사 (gcc, pip 제외)
COPY --from=deps /install /usr/local
COPY --chown=appuser:appgroup ./app .

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

USER appuser
EXPOSE 8000

ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
