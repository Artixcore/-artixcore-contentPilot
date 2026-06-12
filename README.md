# Artixcore ContentPilot

**Artixcore ContentPilot** is a Python-based AI content agent with a Streamlit control panel. It helps Artixcore generate, review, approve, manage, and export content for Facebook, Instagram, LinkedIn, Twitter/X, and the Artixcore website.

This is an **MVP v1** — local-first, modular, and designed to expand into real social publishing, scheduling, analytics, and multi-brand SaaS.

## Features

- **Streamlit dashboard** — Overview of posts, approvals, and provider status
- **Brand profile management** — Editable Artixcore brand voice and guidelines
- **AI content generation** — Platform-specific posts via OpenAI, Anthropic, or Mock provider
- **Provider router** — Auto, manual, fallback, budget, and quality modes with graceful fallback
- **Approval workflow** — Review, edit, approve, reject, schedule, and mark as manually published
- **Campaign planning** — Save campaigns and generate post ideas
- **Exports** — Download posts as CSV, Markdown, or JSON
- **SQLite storage** — Local database at `data/contentpilot.db`
- **No API keys required** — Mock provider enables full local development

## Supported Platforms

| Platform | Notes |
|----------|-------|
| Facebook | Friendly business tone, 3–6 hashtags |
| Instagram | Visual tone, 8–15 hashtags, image prompt |
| LinkedIn | B2B professional, strong hook |
| Twitter/X | Under 280 characters |
| Website Blog | SEO title, meta, slug, outline, article, CTA |

## Setup

### Requirements

- Python 3.11+
- pip

### Install

```bash
cd artixcore-contentpilot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Copy the example file and configure as needed:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (empty) |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4.1-mini` |
| `ANTHROPIC_API_KEY` | Anthropic API key | (empty) |
| `ANTHROPIC_MODEL` | Anthropic model name | `claude-3-5-sonnet-latest` |
| `APP_ENV` | Environment | `development` |
| `DATABASE_URL` | SQLite connection string | `sqlite:///data/contentpilot.db` |
| `APP_DEBUG` | Show debug errors in UI | `false` |

**Never commit your `.env` file.** API keys are read from environment variables only.

## How to Run

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

### Quick Start (No API Keys)

1. Run the app without configuring API keys
2. Go to **Create Post**
3. Select a platform and topic
4. Set **Provider Mode** to `budget` (uses Mock)
5. Click **Generate Post**
6. Review in **Approvals**

## How to Test

```bash
pytest
```

Tests cover:

- Provider router fallback behavior
- Mock provider generation
- Database initialization and default brand profile
- Post creation and status updates
- Invalid platform and empty topic handling

## Provider Fallback

The router selects providers based on mode:

| Mode | Priority |
|------|----------|
| **auto** | OpenAI → Anthropic → Mock |
| **quality** | Anthropic → OpenAI → Mock |
| **budget** | Mock (unless a real provider is manually selected) |
| **manual** | Selected provider → fallback chain |
| **fallback** | Selected → any available → Mock |

If API keys are missing or API calls fail, the app falls back gracefully and **never crashes**. All provider usage is logged to the database.

## Project Structure

```
artixcore-contentpilot/
├── app.py                 # Streamlit entry point
├── core/                  # Agent, router, database, schemas
├── providers/             # OpenAI, Anthropic, Mock
├── prompts/               # Brand voice and generation prompts
├── ui/                    # Streamlit pages
├── data/                  # SQLite database
└── tests/                 # pytest suite
```

## Current Limitations (MVP)

- **No real social media publishing** — Posts are not posted to Facebook, Instagram, LinkedIn, Twitter/X, or any CMS
- **Single brand profile** — Multi-brand support is planned
- **No scheduling calendar** — Schedule status is manual metadata only
- **No image generation** — Image prompts are text only
- **No team approvals or RBAC** — Single-user local workflow
- **No analytics** — No engagement or performance tracking

## Future Roadmap

- Facebook Graph API integration
- Instagram Graph API integration
- LinkedIn API integration
- Twitter/X API integration
- Website CMS publishing
- Scheduling calendar with cron/queue
- Analytics dashboard
- Image generation (DALL·E, Stable Diffusion)
- Multi-brand support
- Team approval workflow with roles
- SaaS version with authentication and billing

## Security Notes

- API keys are never hard-coded or printed in logs
- Full API keys are never shown in the UI
- Content requires human approval before marking as published
- No auto-publishing to external platforms

## License

Internal MVP for Artixcore. All rights reserved.
