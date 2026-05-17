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

<<<<<<< HEAD
Processing steps:

* Normalize column names
* Convert levels to lowercase
* Filter only valid levels

---

### 3.3 Word Selection Logic

Function: `pick_three_words()`

* Reads all CSV files
* Merges into a single DataFrame
* Filters by levels:

  * beginner
  * intermediate
  * advanced
* Randomly selects:

  * 1 word per level
* Returns:

```python
[(word1, level1), (word2, level2), (word3, level3)]
```

Design decision:

* Avoids `.groupby().apply()` to prevent sampling errors
* Uses controlled iteration per level

---

### 3.4 Prompt Engineering

Function: `get_combined_details()`

Key design:

* Sends **all 3 words in one request** → reduces API cost
* Injects **random tense variation**:

  * Simple Present
  * Present Continuous
  * Present Perfect
  * Simple Past
  * Past Continuous
  * Future Simple

Prompt enforces strict structure:

* Word in uppercase
* Part of speech
* 3 synonyms
* Example sentence
* Grammar tip
* Tense-based sentence

Output constraint:

* No extra text
* Clean formatting for Telegram Markdown

---

### 3.5 OpenRouter API Integration

Endpoint:

```
https://openrouter.ai/api/v1/chat/completions
```

Request structure:

```json
{
  "model": MODEL_ID,
  "messages": [
    {"role": "user", "content": prompt}
  ]
}
```

Headers include:

* Authorization (Bearer token)
* Content-Type
* Optional ranking metadata

Error handling:

* Timeout protection
* HTTP status validation
* Graceful fallback message

---

### 3.6 Telegram Integration

Function: `send_to_telegram()`

API:

```
https://api.telegram.org/bot<TOKEN>/sendMessage
```

Payload:

```json
{
  "chat_id": "...",
  "text": "...",
  "parse_mode": "Markdown"
}
```

Features:

* Markdown formatting support
* Multi-user broadcasting via USERS list
* Error logging for failures

---

### 3.7 Main Execution Flow

Function: `main()`

Steps:

1. Initialize bot
2. Fetch 3 words
3. Generate vocabulary content (single API call)
4. Construct final message
5. Send to all configured users

Message format:

```
🌟 DAILY VOCABULARY BOOST 🌟

[Generated content]
=======
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
>>>>>>> master
```

---

<<<<<<< HEAD
## 4. Efficiency Design

### API Optimization

* Traditional approach: 3 API calls (one per word)
* Current approach: **1 API call for 3 words**
* Result: ~66% cost reduction

### Data Handling

* Batch CSV loading
* Single DataFrame processing

---

## 5. Error Handling Strategy

| Component    | Handling                      |
| ------------ | ----------------------------- |
| CSV loading  | Checks for empty directory    |
| Data parsing | Exception capture with logs   |
| API request  | Timeout + HTTP validation     |
| Telegram     | Failure logging without crash |

---

## 6. Extensibility

### Possible Enhancements

* Add **pronunciation (IPA)**
* Include **antonyms**
* Store history in database (SQLite / PostgreSQL)
* Schedule automation using:

  * cron (Linux)
  * Task Scheduler (Windows)
* Add **user-level personalization**
* Integrate spaced repetition logic

---

## 7. Limitations

* Depends on external APIs (OpenRouter, Telegram)
* No persistent storage
* No retry mechanism for failures
* CSV schema must be consistent

---

## 8. Deployment

### Local Execution

```
python script.py
```

### Automation

Use cron job:

```
0 9 * * * python /path/to/script.py
```

---

## 9. Summary

This system combines:

* Structured data processing (Pandas)
* Prompt-engineered LLM output
* API orchestration (OpenRouter + Telegram)

Core strength: **high efficiency + structured linguistic output with minimal API cost**.
=======
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
>>>>>>> master
