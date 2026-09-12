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

# Default port for local `docker run`. Render (and similar platforms) override
# this by injecting their own $PORT env var at runtime, and the CMD below
# picks that up automatically.
ENV PORT=8501

# Basic healthcheck so orchestrators can detect a dead app (uses Python, no extra packages needed).
# Shell form so $PORT is expanded correctly.
HEALTHCHECK CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ['PORT'] + '/_stcore/health')" || exit 1

# Shell form (not exec form) so $PORT is expanded at container start —
# locally this resolves to 8501, on Render it resolves to whatever port Render assigns.
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
