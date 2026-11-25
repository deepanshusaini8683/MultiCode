FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 runner

RUN mkdir -p /workspace && \
    chown runner:runner /workspace

WORKDIR /workspace

USER runner

CMD ["python3"]