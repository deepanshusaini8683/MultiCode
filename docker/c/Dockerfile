FROM ubuntu:24.04

# Install C compiler and essential tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root execution user
RUN useradd --create-home --uid 10001 runner

# Create workspace
RUN mkdir -p /workspace && \
    chown runner:runner /workspace

WORKDIR /workspace

# Run programs as non-root
USER runner

CMD ["bash"]