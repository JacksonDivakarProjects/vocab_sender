# Vocab Sender — Daily Vocabulary Bot

Picks one word per difficulty level from CSV files, generates structured
linguistic details via **OpenRouter**, and broadcasts the result to
**Telegram** users.

---

## Project Structure

```
vocab_sender/
├── vocab_sender.py      # Main application
├── Dockerfile           # Multi-stage Docker build
├── docker-compose.yml   # Compose file for local runs
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore
└── vocab_data/          # Mount your vocabulary CSVs here
```

---

## Quick Start (Docker)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Add vocabulary CSVs

Place your CSV files inside `vocab_data/`. Expected columns:

| Word     | Level        |
|----------|--------------|
| example  | beginner     |
| analyze  | intermediate |
| paradigm | advanced     |

### 3. Run with Docker Compose

```bash
docker compose up --build
```

### 4. Schedule daily runs (cron)

```bash
# Run every day at 09:00
0 9 * * * docker compose -f /path/to/docker-compose.yml up --build >> /var/log/vocab_sender.log 2>&1
```

Or with `docker run` directly:

```bash
docker build -t vocab-sender .
docker run --rm --env-file .env \
  -v "$(pwd)/vocab_data:/data/vocab:ro" \
  vocab-sender
```

---

## Environment Variables

| Variable         | Description                          | Required |
|------------------|--------------------------------------|----------|
| `CSV_PATH`       | Path to vocabulary CSV directory     | Yes      |
| `OPEN_ROUTER_KEY`| OpenRouter API key                   | Yes      |
| `MODEL_ID`       | LLM model identifier                 | Yes      |
| `TELEGRAM_KEY`   | Telegram bot token                   | Yes      |
| `TELEGRAM_CHAT_ID`| Recipient Telegram chat ID          | Yes      |

---

## Refactoring Changes

| Area | Before | After |
|------|--------|-------|
| Config | Inline `os.getenv` calls scattered | `Config` dataclass + `load_config()` with startup validation |
| Logging | `print()` statements | Structured `logging` to stdout + file |
| Retry logic | None | Exponential back-off on OpenRouter calls |
| Error handling | Generic `except Exception` | Specific exception types with clear messages |
| Code structure | Single flat script | Functions grouped by responsibility |
| Dependencies | Included unused `google-genai` | Removed; only needed packages kept |
| Docker | Not containerised | Multi-stage Dockerfile + Compose file |
| Security | — | Non-root container user |

---

## Architecture

```
load_config()
    └─ load_vocabulary() → pick_words()
                                └─ fetch_word_details()   [OpenRouter, with retry]
                                        └─ broadcast()    [Telegram, per user]
```
