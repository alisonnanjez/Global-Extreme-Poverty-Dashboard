# Global Extreme Poverty Dashboard

A Dockerized Streamlit dashboard visualizing the share of the population living in
extreme poverty (below the $3/day International Poverty Line), by country, region,
and year — built as a hands-on project to practice Docker fundamentals and
security-conscious container design.

## Features

- **Interactive world map** (choropleth) showing poverty rate by country for any year
- **Region filter** (Africa, Asia, South America, etc.) using OWID's region classification
- **Trend line comparison** across any countries you choose, over the full available time range
- **Top-N bar chart** of the highest poverty rates for a selected year
- **Region comparison** — average poverty rate by world region
- **Auto-generated key insights** — highest/lowest countries, biggest improvement/decline,
  and region comparisons, recalculated live from whatever filters are applied
- **CSV export** of the currently filtered view
- Custom light theme with turquoise accent

## Data source

World Bank Poverty and Inequality Platform (2026), with processing by
[Our World in Data](https://ourworldindata.org/grapher/share-of-population-in-extreme-poverty),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Running locally with Docker

```bash
docker build -t poverty-dashboard .
docker run --name poverty-dashboard -p 8501:8501 poverty-dashboard
```

Then open http://localhost:8501

To stop/restart later without rebuilding:
```bash
docker stop poverty-dashboard
docker start poverty-dashboard
```

## Project structure

```
.
├── app.py                    # Streamlit dashboard
├── data/                     # CSV data (share-of-population-in-extreme-poverty.csv)
├── .streamlit/
│   └── config.toml           # Custom theme
├── requirements.txt          # Pinned dependencies
├── Dockerfile
├── .dockerignore
└── README.md
```

## Security choices made in this project

- **Minimal base image** — `python:3.11-slim` instead of the full image, to shrink
  the attack surface and image size.
- **Non-root user** — the app runs as a dedicated `appuser`, not root, inside the
  container.
- **Pinned dependency versions** — `requirements.txt` pins exact versions to avoid
  unpredictable upstream changes.
- **No secrets in the image** — `.dockerignore` excludes `.env` files and other
  local artifacts; the app needs no API keys or credentials.
- **Healthcheck** — a lightweight Python-based healthcheck (no extra OS packages
  installed just to support `curl`).
- **Layer caching** — dependencies are installed before the app code is copied in,
  so rebuilds are fast and only reinstall packages when `requirements.txt` changes.

## Possible next steps

- Scan the built image with `docker scout` or Trivy and record the result here.
- Add automated tests for the data-loading logic.
