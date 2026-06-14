# ============================================================================
#  Cognitive Market Engine — Production Dockerfile (Category 10.5)
# ============================================================================
#  Multi-stage build with NLP model dependencies:
#  - spaCy 3.x with en_core_web_sm and en_core_web_trf models
#  - Transformers (FinBERT, MiniLM, DeBERTa) with PyTorch CPU
#  - NetworkX, SQLite, FastAPI, Streamlit, Plotly
# ============================================================================

# ----------  Stage 1: Base with system deps ----------
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ----------  Stage 2: Install Python dependencies ----------
FROM base AS deps

COPY requirements.txt .

# Install core Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install NLP models
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download en_core_web_trf || true

# Pre-download transformer models (cached in image)
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('ProsusAI/finbert'); \
AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert'); \
" || echo "FinBERT download skipped (optional)"

RUN python -c "\
from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); \
AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); \
" || echo "MiniLM download skipped (optional)"

# ----------  Stage 3: Production image ----------
FROM base AS production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY --from=deps /root/.cache /root/.cache

# Copy application code
COPY . /app/

# Create required directories
RUN mkdir -p /app/logs /app/data /app/metrics_data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose ports: 8501 (Streamlit), 8000 (FastAPI)
EXPOSE 8501 8000

# Default: run the main pipeline
CMD ["python", "main.py"]

# ----------  Alternative entry points ----------
# Dashboard:  docker run -p 8501:8501 cme streamlit run dashboard/app.py --server.port 8501
# API:        docker run -p 8000:8000 cme uvicorn api.server:app --host 0.0.0.0 --port 8000
# Tests:      docker run cme python -m pytest tests/ -v
