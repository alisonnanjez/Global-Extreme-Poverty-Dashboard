# Small, minimal base image — reduces attack surface and image size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching) with pinned versions
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app (respects .dockerignore — no secrets, no local junk)
COPY . .

# Create a dedicated non-root user and switch to it.
# Running as root inside a container is a classic, avoidable risk.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

# Basic healthcheck so orchestrators can detect a dead app (uses Python, no extra packages needed)
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
