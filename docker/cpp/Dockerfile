FROM ubuntu:24.04

# Install C++ compiler and essential tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    build-essential \
    coreutils && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --uid 10001 runner

# Create workspace
RUN mkdir -p /workspace && \
    chown runner:runner /workspace

WORKDIR /workspace

# Run as non-root user
USER runner

CMD ["bash"]
