### Project Documentation: Daily Vocabulary Bot (OpenRouter + Telegram)

---

## 1. Overview

This project is an automated **Vocabulary Learning Bot** that:

* Extracts words from CSV files categorized by difficulty level.
* Selects one word each from **Beginner, Intermediate, Advanced** levels.
* Uses an LLM via **OpenRouter API** to generate structured linguistic details.
* Sends the formatted output to users via **Telegram Bot API**.

Core objective: deliver **daily structured vocabulary training** with minimal API usage (single request for multiple words).

---

## 2. System Architecture

**Flow:**

1. Load environment variables
2. Read and merge CSV datasets
3. Sample 3 words (one per level)
4. Generate prompt dynamically
5. Send request to OpenRouter
6. Receive formatted response
7. Send output to Telegram users

---

## 3. Key Components

### 3.1 Environment Configuration

Uses `.env` file to store sensitive data:

* `CSV_PATH` → directory of vocabulary CSV files
* `OPEN_ROUTER_KEY` → OpenRouter API key
* `MODEL_ID` → LLM model identifier
* `TELEGRAM_KEY` → Telegram bot token
* `TELEGRAM_CHAT_ID` → recipient chat ID

---

### 3.2 Data Source (CSV Files)

Expected structure:

| Word     | Level        |
| -------- | ------------ |
| example  | beginner     |
| analyze  | intermediate |
| paradigm | advanced     |

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
```

---

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
