FROM --platform=linux/arm64 python:3.11-slim-bullseye as builder

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    BLIS_ARCH="cortexa57" \
    PATH=/venv/bin:$PATH

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python dependencies in stages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Install numpy first as it's a key dependency
    pip install --no-cache-dir numpy==1.26.4 && \
    # Install BLIS with proper ARM64 optimization
    BLIS_ARCH="cortexa57" pip install --no-cache-dir blis==0.7.11 && \
    # Install core dependencies
    pip install --no-cache-dir \
        flask==3.0.2 \
        solana==0.32.0 \
        anchorpy==0.19.0 \
        python-dotenv==1.0.1 \
        aiohttp==3.9.3 && \
    # Install ML dependencies optimized for ARM64
    pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        spacy==3.7.4 \
        transformers==4.37.2 \
        sentence-transformers==2.3.1 && \
    python -m spacy download en_core_web_trf

# Runtime stage
FROM --platform=linux/arm64 python:3.11-slim-bullseye

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatlas3-base \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app
COPY . .

# Create necessary directories
RUN mkdir -p /root/.config/solana

EXPOSE 5000
CMD ["python", "app.py"] 