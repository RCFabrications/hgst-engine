FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY hgst/ ./hgst/

RUN make -C hgst libhgst_runtime.so
RUN pip install --no-cache-dir .

ARG GIT_COMMIT_SHA=unknown
LABEL org.opencontainers.image.revision="${GIT_COMMIT_SHA}"
LABEL org.opencontainers.image.title="hgst-engine"

ENV HGST_NATIVE_LIBRARY=/app/hgst/libhgst_runtime.so
ENV PROMETHEUS_PORT=9090

EXPOSE 9090

CMD ["python3", "-m", "hgst.apex_substrate_daemon"]
