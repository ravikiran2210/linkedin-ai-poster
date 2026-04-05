# LinkedIn AI Poster

Automated daily LinkedIn content pipeline for AI, ML, LLM, and AI agent news. Fetches updates from multiple sources, scores and ranks them, generates a LinkedIn post with carousel images, and publishes after manual approval.

## Architecture

```
Collectors → Dedup → Classify → Score → Select → Caption + Carousel → Draft → Approve → Publish
```

**Data flow:**
1. **Collectors** (RSS, arXiv, GitHub, tech blogs) fetch fresh items
2. **Deduplicator** removes repeated stories via title/URL/content hashing
3. **Classifier** assigns topics (llm, ai_agents, ml_research, etc.)
4. **Scorer** computes weighted score: 40% recency + 25% interest + 20% authority + 15% clarity
5. **Selector** picks the single best candidate with diversity guard-rails
6. **Caption Writer** generates a LinkedIn post via Gemini 2.5 Flash (with template fallback)
7. **Carousel Renderer** creates 4 branded slides using Pillow
8. **Approval API** lets you review before publishing
9. **Publisher** posts to LinkedIn via the official API

**Tech stack:** Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy, Pydantic, httpx, APScheduler, Pillow, Google Gemini API

## Setup

### 1. Clone and install

```bash
cd linkedin_ai_poster
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

Key environment variables:
- `DATABASE_URL` – PostgreSQL connection string
- `GEMINI_API_KEY` – Google Gemini API key for caption generation
- `LINKEDIN_ACCESS_TOKEN` – LinkedIn OAuth2 access token
- `LINKEDIN_PERSON_URN` – Your LinkedIn person URN (e.g., `urn:li:person:abc123`)
- `AUTO_APPROVE` – Set to `true` to skip manual approval (default: `false`)

### 3. Start PostgreSQL

```bash
docker-compose up -d db
```

### 4. Seed sources

```bash
python scripts/seed_sources.py
```

### 5. Start the app

```bash
uvicorn app.main:app --reload
```

The app starts with a daily scheduler. The pipeline runs automatically at 07:00 UTC (configurable).

## Running the Daily Job Manually

```bash
python scripts/run_daily.py
```

Or via the API:

```bash
curl -X POST http://localhost:8000/pipeline/run
```

## Backfill Items

Fetch items from all sources without running the full pipeline:

```bash
python scripts/backfill_items.py
```

## Review and Approve Drafts

### List pending drafts

```bash
curl http://localhost:8000/drafts
```

### View a specific draft

```bash
curl http://localhost:8000/drafts/1
```

### Approve and publish

```bash
curl -X POST http://localhost:8000/approve/1
```

### Reject a draft

```bash
curl -X POST http://localhost:8000/reject/1
```

## Plugging In Real Credentials

### Google Gemini API
1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set `GEMINI_API_KEY` in `.env`
3. The caption writer will automatically use Gemini 2.5 Flash

### LinkedIn API
1. Create a LinkedIn app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Request `w_member_social` and `r_liteprofile` permissions
3. Generate an OAuth2 access token
4. Set `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN` in `.env`

Without credentials, the system runs in stub mode — drafts are created but not published.

## Running Tests

```bash
pytest
```

## Project Structure

```
linkedin_ai_poster/
  app/
    main.py                  # FastAPI app + scheduler
    config.py                # Pydantic settings from env vars
    constants.py             # Weights, topics, thresholds
    collectors/              # RSS, arXiv, GitHub, blog collectors
    processors/              # Dedup, classify, score, select
    content/                 # Caption writer, carousel renderer
    publisher/               # LinkedIn API client, media upload
    storage/                 # SQLAlchemy models + repositories
    services/                # Business logic orchestration
    workflows/               # Daily pipeline, approval flow
    api/                     # FastAPI routes
  scripts/                   # CLI scripts
  tests/                     # pytest tests
```

## Future Enhancements

- Semantic deduplication with embeddings
- Slack/Telegram approval notifications
- Analytics-informed scoring (learn from past engagement)
- More collectors (Twitter/X, HN, Product Hunt)
- A/B testing of caption styles
- Full auto-publishing mode with safety checks
