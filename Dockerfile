FROM --platform=linux/arm64 debian:bullseye-slim as builder

# Set environment variables
ENV CARGO_HOME=/root/.cargo \
    RUSTUP_HOME=/root/.rustup \
    PATH=/root/.cargo/bin:$PATH \
    RUST_VERSION=1.75.0 \
    SOLANA_VERSION=1.18.1 \
    ANCHOR_VERSION=0.29.0 \
    PYTHONUNBUFFERED=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

# Install build dependencies and create Python environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3-minimal \
    python3-pip \
    python3-venv \
    build-essential \
    pkg-config \
    libssl-dev \
    git \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /venv

# Set up Python dependencies in stages
COPY requirements.txt /tmp/
RUN . /venv/bin/activate \
    && pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    # Install numpy first as it's a key dependency
    && pip install --no-cache-dir numpy==1.26.4 \
    # Install BLIS separately with proper build flags
    && BLIS_ARCH="cortexa57" pip install --no-cache-dir blis==0.7.11 \
    # Install core dependencies
    && pip install --no-cache-dir \
        flask==3.0.2 \
        solana==0.32.0 \
        anchorpy==0.19.0 \
        python-dotenv==1.0.1 \
        aiohttp==3.9.3 \
    # Install ML dependencies separately
    && pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
        spacy==3.7.4 \
        transformers==4.37.2 \
        sentence-transformers==2.3.1 \
    && python -m spacy download en_core_web_trf

# Install Rust and Solana toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --default-toolchain ${RUST_VERSION} --profile minimal \
    && . "$CARGO_HOME/env" \
    # Install Solana CLI
    && mkdir -p /root/.local/share/solana/install/active_release \
    && curl -sSfL "https://github.com/solana-labs/solana/releases/download/v${SOLANA_VERSION}/solana-release-aarch64-apple-darwin.tar.bz2" | \
       tar -xj -C /root/.local/share/solana/install/active_release --strip-components=1 \
    && chmod +x /root/.local/share/solana/install/active_release/bin/* \
    # Install Anchor
    && cargo install --git https://github.com/coral-xyz/anchor --tag "v${ANCHOR_VERSION}" avm --locked --force \
    && avm install ${ANCHOR_VERSION} \
    && avm use ${ANCHOR_VERSION}

# Start fresh with minimal runtime image
FROM --platform=linux/arm64 debian:bullseye-slim as app

# Copy only necessary files from builder
COPY --from=builder /venv /venv
COPY --from=builder /root/.cargo /root/.cargo
COPY --from=builder /root/.rustup /root/.rustup
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/.avm /root/.avm

# Set environment variables
ENV PATH=/venv/bin:/root/.cargo/bin:/root/.local/share/solana/install/active_release/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    CARGO_HOME=/root/.cargo \
    RUSTUP_HOME=/root/.rustup

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-minimal \
    libssl1.1 \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.config/solana \
    && solana-keygen new --no-bip39-passphrase -o /root/.config/solana/id.json --force

# Set up working directory and copy application code
WORKDIR /app
COPY . .

# Copy and set up entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose ports
EXPOSE 5000 8899 8900

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"] 