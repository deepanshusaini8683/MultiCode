FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-21-jdk-headless \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 runner

RUN mkdir -p /workspace && \
    chown runner:runner /workspace

WORKDIR /workspace

USER runner

CMD ["java", "--version"]