# Artixcore ContentPilot

**Artixcore ContentPilot** is a Python-based AI content agent with a Streamlit control panel. It helps Artixcore generate, review, approve, manage, publish, and export content for Facebook, Instagram, LinkedIn, Twitter/X, and the Artixcore website.

## What It Does

- **AI content generation** — Platform-specific posts via OpenAI or Anthropic (no mock provider)
- **AI chatbot** — Facebook, LinkedIn, and X/Twitter chat connectors with Telegram admin control
- **Approval workflow** — Human review before any publishing or chatbot replies
- **Social publishing** — Real connectors for LinkedIn, X/Twitter, Facebook, Instagram, and Website API
- **Training data** — Saves prompts, responses, edits, and feedback for future fine-tuning
- **Local SQLite database** — Full audit trail, provider logs, publishing logs, and chat history

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

For the chatbot, if no valid provider is configured:

> Please provide a valid OpenAI or Anthropic API key to use Artixcore ContentPilot Chatbot.

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

## Chatbot Overview

The chatbot module replies to Facebook, LinkedIn, and X/Twitter messages using OpenAI or Anthropic. **No mock AI provider exists.** Auto-reply is **disabled by default**; approval mode is **enabled by default**.

### Chat Control

Use **Chat Control** in the sidebar to:

- View AI provider and connector status
- Enable/disable auto reply, approval mode, and human handoff
- Configure personality, gender style (tone-only), language, tone, reply length, emoji usage, and CTA style

### Chat Inbox

Use **Chat Inbox** to:

- Review conversations and AI draft replies
- Approve, reject, regenerate, or send manual replies
- Simulate incoming messages locally (no public webhook required)

### Chat Settings

Use **Chat Settings** for chatbot name, custom personality prompt, blocked keywords, business hours, and fallback message.

### Personality Configuration

Personality types: Professional Consultant, Friendly Support Agent, Technical Expert, Sales Assistant, Founder-like Visionary, Minimal Direct Agent, Custom Personality.

Gender style (Male, Female, Neutral) affects tone and phrasing only — not biological claims or stereotypes.

Languages: English, Bangla, English + Bangla Mixed, Hindi, Arabic, Spanish, French, German, Portuguese, Custom.

### Facebook Connector Setup

```env
META_PAGE_ID=
META_PAGE_ACCESS_TOKEN=
META_VERIFY_TOKEN=
META_GRAPH_VERSION=v23.0
```

Webhook verification uses `META_VERIFY_TOKEN`. For production, deploy a public webhook endpoint. For local MVP, use **Simulate Incoming Message** in Chat Inbox.

### LinkedIn Connector (Limitation)

LinkedIn direct messaging APIs are restricted. The connector returns:

> LinkedIn messaging requires approved API access. Configure valid permissions or use manual inbox mode.

Set `LINKEDIN_MESSAGING_ENABLED=true` only if you have approved messaging API access.

### X/Twitter Connector Setup

```env
X_ACCESS_TOKEN=
X_DM_ENABLED=false
```

Reply support depends on your X API access tier. DMs require `X_DM_ENABLED=true` and appropriate API permissions.

### Telegram Controller Setup

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_IDS=123456789,987654321
```

The Telegram bot starts automatically when `TELEGRAM_BOT_TOKEN` is set. Only user IDs in `TELEGRAM_ADMIN_IDS` can control the chatbot.

#### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and status |
| `/status` | Provider, mode, pending count, platform status |
| `/pause` | Disable auto replies |
| `/resume` | Enable auto replies |
| `/mode_auto` | Auto reply without approval |
| `/mode_approval` | Approval required, auto reply off |
| `/pending` | List pending replies |
| `/approve {message_id}` | Approve and send |
| `/reject {message_id}` | Reject draft |
| `/reply {conversation_id} {message}` | Manual reply |
| `/handoff {conversation_id}` | Human handoff |
| `/close {conversation_id}` | Close conversation |
| `/personality {type}` | Change personality |
| `/gender {male\|female\|neutral}` | Change gender style |
| `/language {language}` | Change language |
| `/help` | Show commands |

### Approval vs Auto Reply

| Mode | `auto_reply_enabled` | `approval_required` |
|------|---------------------|---------------------|
| **Default (Approval)** | `false` | `true` |
| **Auto Reply** | `true` | `false` |

Safety checks run before any automatic send. Failed safety checks block auto-send.

### Human Handoff

When enabled, conversations marked `human_handoff` skip AI auto-replies. Use Chat Inbox or `/handoff` to escalate.

### Chat Training Data Export

Export from **Training Data** or **Exports**:

- Content posts training data
- Chatbot training data
- Both (combined JSONL)

Format includes system/user/assistant messages plus metadata (platform, personality, gender style, language, quality score, approval status).

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
- `chatbot_settings` — Chatbot personality and behavior config
- `chat_conversations` — Cross-platform conversation threads
- `chat_messages` — Full message audit with AI prompts and safety
- `chat_events` — Chatbot event log
- `chat_training_examples` — Chat fine-tuning examples
- `telegram_admins` — Telegram admin registry
- `telegram_commands` — Telegram command audit log

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
- Telegram controller only accepts configured admin IDs
- Chatbot replies require safety pass before auto-send
- System prompts are never exposed to end users

## Reliability & Error Handling

ContentPilot includes a production-grade reliability layer to prevent crashes from normal runtime errors.

### Global Error Handling

- Custom `AppError` hierarchy in `core/errors.py` with `message`, `reason`, `user_action`, and `error_code`
- `core/error_handler.py` formats user-facing errors and logs sanitized details
- Stack traces shown only when `APP_ENV=development` (or `APP_DEBUG=true`)
- Secrets (API keys, tokens, Authorization headers) are redacted from logs and UI

### Logging

- Rotating log file: `logs/contentpilot.log` (5MB, 5 backups)
- Configure level with `LOG_LEVEL=INFO`
- Important events logged: startup, migrations, AI generation, publishing, exports, Telegram commands, rate limits, circuit breaker state

### Loading States

- `ui/loading.py` provides spinners, skeletons, and progress steps
- Long operations (AI generation, publishing, exports, database queries) show loading feedback

### Provider & Connector Failure Handling

- OpenAI/Anthropic: timeouts, retries, rate limits, circuit breaker, structured errors
- Social publishers: timeout, retry on 5xx, circuit breaker per platform
- Missing API keys show clear configuration guidance instead of crashing

### Database Safety

- Safe session handling with rollback on errors
- SQLite lock retries
- Idempotent migrations
- Database unavailable page on startup failure

### Rate Limiting

Configurable per-minute limits via `.env`:

| Action | Default |
|--------|---------|
| AI generation | 20/min |
| Chatbot replies | 30/min |
| Publishing | 10/min |
| Exports | 5/min |
| Telegram commands | 30/min |

### Circuit Breaker

After repeated external API failures, connectors pause temporarily with a user-friendly message. Configure with `CIRCUIT_BREAKER_FAILURE_THRESHOLD` and `CIRCUIT_BREAKER_COOLDOWN_SECONDS`.

### Load Handling

Concurrency limits for AI, publishing, and exports via `MAX_CONCURRENT_*` env vars. Overload returns: *"ContentPilot is handling many tasks right now."*

### Health Checks

Dashboard **System Health** section shows status for database, providers, connectors, logs, and data directory.

### Troubleshooting

| Issue | What to do |
|-------|------------|
| Missing OpenAI/Anthropic key | Add keys in `.env` → Provider Settings |
| Database locked | Wait and retry; avoid concurrent writes |
| LinkedIn permission denied | Check token scopes and author URN |
| X content too long | Keep posts under 280 characters |
| Facebook token expired | Refresh `META_PAGE_ACCESS_TOKEN` |
| Instagram image URL invalid | Use a public HTTPS image URL |
| Telegram unauthorized user | Add user ID to `TELEGRAM_ADMIN_IDS` |
| Export permission denied | Check disk permissions and path |
| App under heavy load | Wait briefly; reduce concurrent actions |

### How to Read Logs

```bash
tail -f logs/contentpilot.log
```

Look for `ERROR` lines with `error_code` and sanitized context. Never paste raw tokens from logs.

### Load Test

```bash
python scripts/load_test.py
```

Set `ENABLE_REAL_API_LOAD_TEST=true` only if you intend to hit paid APIs.

## Current Limitations

- **No OAuth** — Tokens configured manually through `.env`
- **Instagram** — Image posts only; requires public image URL
- **X/Twitter** — Text only; 280 character limit enforced
- **LinkedIn messaging** — API access may be restricted; manual inbox mode for MVP
- **Facebook webhooks** — Real-time messaging requires public deployment
- **Telegram** — Polling mode only; webhook mode not implemented
- **Production publishing** — May require platform review and approved permissions
- **Analytics** — Table ready; platform fetch not implemented (manual entry only)
- **Single brand profile** — Multi-brand support planned
- **No image generation** — Image prompts are text only
- **Chatbot auto-reply off by default** — Approval required unless explicitly changed
- **In-memory rate limits/circuit breaker** — Resets on app restart; use Redis for multi-instance production

## Future Roadmap

- OAuth flows for LinkedIn, X, Meta
- Facebook/LinkedIn/X real-time webhooks in production
- Telegram webhook mode
- Scheduling calendar with queue
- Platform analytics auto-fetch
- Image generation integration
- Multi-brand support
- Team approval workflow with RBAC
- RAG over chat training data
- SaaS version with authentication and billing

## Project Structure

```
artixcore-contentpilot/
├── app.py
├── chatbot/        # Chatbot agent, connectors, Telegram controller
├── core/           # Agent, router, database, reliability layer, publishing, training data
├── scripts/        # load_test.py stress test
├── providers/      # OpenAI, Anthropic
├── publishers/     # LinkedIn, X, Facebook, Instagram, Website
├── prompts/        # Brand voice and generation prompts
├── ui/             # Streamlit pages (including Chat Control, Inbox, Settings)
├── data/           # SQLite database
└── tests/          # pytest suite
```

## License

Internal MVP for Artixcore. All rights reserved.
