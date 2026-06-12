# Artixcore ContentPilot

**Artixcore ContentPilot** is a Python-based AI content agent with a Streamlit control panel. It helps Artixcore generate, review, approve, manage, publish, and export content for Facebook, Instagram, LinkedIn, Twitter/X, and the Artixcore website.

## What It Does

- **AI content generation** — Platform-specific posts via OpenAI or Anthropic (no mock provider)
- **Approval workflow** — Human review before any publishing
- **Social publishing** — Real connectors for LinkedIn, X/Twitter, Facebook, Instagram, and Website API
- **Training data** — Saves prompts, responses, edits, and feedback for future fine-tuning
- **Local SQLite database** — Full audit trail, provider logs, and publishing logs

## Requirements

- Python 3.11+
- **OpenAI or Anthropic API key** (required for content generation)
- Social platform tokens (optional, for publishing)

## Setup

```bash
cd artixcore-contentpilot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your API keys and platform tokens. **Never commit `.env`.**

## How to Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

If no valid OpenAI or Anthropic API key is configured, the app shows:

> Please provide a valid OpenAI or Anthropic API key to use Artixcore ContentPilot.

Content generation is blocked until a real provider is configured.

## How to Test

```bash
pytest
```

## Configure OpenAI / Anthropic

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

### Provider Router Modes

| Mode | Behavior |
|------|----------|
| **auto** | OpenAI → Anthropic |
| **quality** | Anthropic → OpenAI |
| **manual** | Selected provider only |
| **fallback** | Selected → other available provider |

## Configure Social Platforms

Tokens are configured manually in `.env`. OAuth login is not implemented yet.

### LinkedIn

```env
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_AUTHOR_URN=urn:li:person:XXXX
LINKEDIN_API_VERSION=202506
```

Posts to `POST https://api.linkedin.com/rest/posts`. Requires valid author URN and posting permission.

### X / Twitter

```env
X_ACCESS_TOKEN=
```

Posts to `POST https://api.x.com/2/tweets`. Requires API access level that supports posting. Content must be ≤280 characters.

### Facebook Page

```env
META_PAGE_ID=
META_PAGE_ACCESS_TOKEN=
META_GRAPH_VERSION=v23.0
```

Posts to Facebook Page feed via Graph API. Requires Page access token with `pages_manage_posts`.

### Instagram

```env
META_IG_USER_ID=
META_PAGE_ACCESS_TOKEN=
META_GRAPH_VERSION=v23.0
```

Two-step image publish via Graph API. Requires Business/Creator account and a **public image URL**.

### Website API

```env
WEBSITE_API_BASE_URL=https://your-cms.example.com
WEBSITE_API_TOKEN=
WEBSITE_POST_ENDPOINT=/api/posts
```

Publishes blog drafts to your Artixcore website CMS API.

## Local Database

Database path: `data/contentpilot.db` (configurable via `DATABASE_URL`).

### Tables

- `brand_profiles` — Artixcore brand voice
- `posts` — Content with full AI generation metadata
- `campaigns` — Campaign planning
- `provider_logs` — AI provider usage (sanitized)
- `publishing_logs` — Publish attempts and results
- `training_examples` — Clean examples for fine-tuning
- `content_events` — Audit trail (generated, edited, approved, published, etc.)
- `social_accounts` — Future OAuth account storage (env references for MVP)
- `post_analytics` — Engagement metrics (manual/future fetch)

Migrations run safely on startup — missing columns are added without deleting data.

## AI Training Data

On generation, the app saves:

- `input_prompt`, `system_prompt`
- `raw_ai_response`, `parsed_ai_response`
- Provider, model, latency, token estimates

On approval/edit/publish, training examples are created or updated with human feedback and quality scores.

### Export Training Data

Use the **Training Data** or **Exports** page:

- **JSONL** — OpenAI fine-tune format with system/user/assistant messages
- **CSV** — Tabular export for analysis

Rejected examples are excluded by default.

## Security Notes

- API keys and tokens are loaded from `.env` only — never hard-coded
- Full secrets are never shown in the UI (masked display only)
- Request/response payloads are sanitized before logging
- Human approval is required before publishing
- Manual publish click is required — no auto-publishing

## Current Limitations

- **No OAuth** — Tokens configured manually through `.env`
- **Instagram** — Image posts only; requires public image URL
- **X/Twitter** — Text only; 280 character limit enforced
- **Production publishing** — May require platform review and approved permissions
- **Analytics** — Table ready; platform fetch not implemented (manual entry only)
- **Single brand profile** — Multi-brand support planned
- **No image generation** — Image prompts are text only

## Future Roadmap

- OAuth flows for LinkedIn, X, Meta
- Scheduling calendar with queue
- Platform analytics auto-fetch
- Image generation integration
- Multi-brand support
- Team approval workflow with RBAC
- SaaS version with authentication and billing

## Project Structure

```
artixcore-contentpilot/
├── app.py
├── core/           # Agent, router, database, publishing, training data
├── providers/      # OpenAI, Anthropic
├── publishers/     # LinkedIn, X, Facebook, Instagram, Website
├── prompts/        # Brand voice and generation prompts
├── ui/             # Streamlit pages
├── data/           # SQLite database
└── tests/          # pytest suite
```

## License

Internal MVP for Artixcore. All rights reserved.
