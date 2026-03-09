FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies if needed (e.g. for some ML libs)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy only what's needed for pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Copy source code only (exclude junk via .dockerignore)
COPY src/ ./src/

# Optional: if you need data/scripts at build time (usually mount at runtime instead)
# COPY data/ ./data/
# COPY scripts/ ./scripts/

# Create non-root user (good practice)
RUN useradd -m appuser
USER appuser

EXPOSE 8501

# Streamlit command - use module style or full path
CMD ["streamlit", "run", "src/interfaces/web.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]