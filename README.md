# ⚽ SatisGraph – World Cup 2026 Predictions Tracker

A Python data pipeline + interactive dashboard that collects, extracts, and aggregates **YouTube creator predictions** for the 2026 FIFA World Cup.

---

## Features

| Module | Description |
|--------|-------------|
| **Ingestion** | Scans configured YouTube channels for WC2026-related videos (keyword filter + optional YouTube Data API v3) |
| **Transcript extraction** | Fetches subtitles/transcripts via `youtube-transcript-api` (falls back to stub in dev) |
| **Prediction extraction** | Rule-based + optional LLM layer to detect winners, exact scores, dark horses, confidence levels |
| **Storage** | SQLite (WAL mode) with a clean Repository pattern – ready to migrate to PostgreSQL |
| **Dashboard** | 6-page Streamlit app with Plotly charts |
| **Scoring** | Weighted consensus ranking across creators (accuracy × freshness × confidence) |

---

## Project Structure

```
SatisGraph/
├── app/
│   ├── pipeline.py              # Main orchestrator
│   ├── dashboard/
│   │   ├── main.py              # Streamlit entry point
│   │   └── pages/               # One file per dashboard page
│   ├── ingestion/               # YouTube scanning & filtering
│   ├── extraction/              # Transcript + prediction extractors
│   ├── storage/                 # Database + Repository layer
│   ├── models/                  # Pydantic domain models
│   ├── scoring/                 # Aggregation & consensus
│   └── utils/                   # Config loader, logger
├── config/
│   ├── channels.yml             # YouTube channel list
│   └── settings.yml             # App-wide settings
├── data/
│   └── demo/seed_data.py        # Demo data loader
├── tests/                       # Pytest unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

---

## Quick Start (local, no API key needed)

```bash
# 1. Clone and install
git clone https://github.com/Nazano/SatisGraph.git
cd SatisGraph
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Load demo data (creates SQLite DB with realistic fake data)
python -m data.demo.seed_data

# 3. Launch the dashboard
streamlit run app/dashboard/main.py
# → Open http://localhost:8501
```

---

## Quick Start (Docker)

```bash
cp .env.example .env    # edit YOUTUBE_API_KEY if you have one
docker compose up --build
# → Open http://localhost:8501
```

---

## Full Pipeline (with YouTube API)

```bash
export YOUTUBE_API_KEY="your_key_here"

# 1. Uncomment in requirements.txt:
#    google-api-python-client
#    youtube-transcript-api
pip install google-api-python-client youtube-transcript-api

# 2. Run full pipeline
python -m app.pipeline

# Or step by step:
python -m app.pipeline --scan-only          # ingest new videos
python -m app.pipeline --transcripts-only   # fetch transcripts
python -m app.pipeline --predictions-only   # extract predictions
```

---

## LLM-enhanced extraction (via Ollama)

1. Install and start [Ollama](https://ollama.com):
   ```bash
   ollama serve
   ollama pull llama3.2
   ```
2. In `config/settings.yml`, confirm:
   ```yaml
   llm:
     enabled: true
     model: "llama3.2"
     base_url: "http://localhost:11434"
   ```
3. Run the pipeline:
   ```bash
   python -m app.pipeline --predictions-only
   ```

Set `OLLAMA_BASE_URL` to override the default Ollama server address.

---

## Configuration

Edit `config/channels.yml` to add/remove YouTube channels:

```yaml
channels:
  - name: "MyChannel"
    channel_id: "UCxxxxxxxxxxxxxxxxxx"
    url: "https://www.youtube.com/@MyChannel"
    language: "fr"   # fr | en | es
    country: "FR"
```

Edit `config/settings.yml` to tune behaviour (max results, DB path, log level, etc.).

---

## Running Tests

```bash
pytest -v
# With coverage:
pytest --cov=app --cov-report=term-missing
```

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 📊 Vue d'ensemble | KPIs, language breakdown, recent videos |
| 🎬 Explorateur | Filterable video table |
| 🔍 Détail vidéo | Metadata, transcript, predictions |
| 👥 Comparateur | Side-by-side creator picks |
| ⚽ Pronos par match | Aggregated consensus, score picks |
| 🏆 Fiabilité | Creator accuracy ranking |

---

## Extending the project

### Add a FastAPI REST layer
The Repository class is framework-agnostic. To add an API:
```bash
pip install fastapi uvicorn
# Create app/api/main.py, import get_repo() and expose endpoints.
```

### Switch to PostgreSQL
1. Change `database.driver` in `settings.yml`.
2. Replace the `sqlite3` calls in `app/storage/database.py` with `psycopg2` or `asyncpg`.
3. The `Repository` class needs no changes (SQL is standard).

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 key |
| `OLLAMA_BASE_URL` | Ollama server URL for LLM extraction (default: `http://localhost:11434`) |

---

## Roadmap / TODOs

- [ ] Real YouTube API integration (`app/ingestion/youtube_client.py`)
- [ ] Real transcript fetching (`app/extraction/transcript.py`)
- [x] LLM extraction layer (`app/extraction/predictions.py`) — implemented via Ollama
- [ ] FastAPI REST endpoints (`app/api/`)
- [ ] Scheduled pipeline (Airflow / cron / APScheduler)
- [ ] PostgreSQL migration path
- [ ] User-facing result validation (mark predictions correct/wrong)
