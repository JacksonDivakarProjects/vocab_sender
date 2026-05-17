"""
Vocab Sender — Daily Vocabulary Bot
Picks one word per level from CSV files, generates linguistic details
via OpenRouter, and broadcasts the result to Telegram users.
"""

import logging
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("vocab_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"

LEVELS = ("beginner", "intermediate", "advanced")

TENSES = [
    "Simple Present",
    "Present Continuous",
    "Present Perfect",
    "Simple Past",
    "Past Continuous",
    "Future Simple",
]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
@dataclass
class TelegramUser:
    token: str
    chat_id: str


@dataclass
class Config:
    csv_dir: Path
    openrouter_key: str
    model_id: str
    users: list[TelegramUser] = field(default_factory=list)
    request_timeout: int = 30


def load_config() -> Config:
    """Load and validate all required environment variables."""
    load_dotenv()

    missing = []
    required = {
        "CSV_PATH": os.getenv("CSV_PATH"),
        "OPEN_ROUTER_KEY": os.getenv("OPEN_ROUTER_KEY"),
        "MODEL_ID": os.getenv("MODEL_ID"),
        "TELEGRAM_KEY": os.getenv("TELEGRAM_KEY"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    }

    for key, val in required.items():
        if not val:
            missing.append(key)

    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    csv_dir = Path(required["CSV_PATH"])
    if not csv_dir.is_dir():
        log.error("CSV_PATH '%s' is not a valid directory.", csv_dir)
        sys.exit(1)

    return Config(
        csv_dir=csv_dir,
        openrouter_key=required["OPEN_ROUTER_KEY"],
        model_id=required["MODEL_ID"],
        users=[
            TelegramUser(
                token=required["TELEGRAM_KEY"],
                chat_id=required["TELEGRAM_CHAT_ID"],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
WordList = list[tuple[str, str]]  # [(word, level), ...]


def load_vocabulary(csv_dir: Path) -> Optional[pd.DataFrame]:
    """Merge all CSV files in *csv_dir* into a single normalised DataFrame."""
    csv_files = list(csv_dir.glob("*.csv"))
    if not csv_files:
        log.error("No CSV files found in '%s'.", csv_dir)
        return None

    frames = []
    for path in csv_files:
        try:
            df = pd.read_csv(path)
            df.columns = [str(c).strip().capitalize() for c in df.columns]
            frames.append(df)
        except Exception as exc:
            log.warning("Skipping '%s': %s", path.name, exc)

    if not frames:
        log.error("All CSV files failed to load.")
        return None

    combined = pd.concat(frames, ignore_index=True)
    combined["Level"] = combined["Level"].astype(str).str.strip().str.lower()
    return combined


def pick_words(df: pd.DataFrame) -> Optional[WordList]:
    """Return one random word per level; *None* if any level is missing."""
    result: WordList = []
    filtered = df[df["Level"].isin(LEVELS)]

    for level in LEVELS:
        group = filtered[filtered["Level"] == level]
        if group.empty:
            log.warning("No words found for level '%s'.", level)
            continue
        row = group.sample(1).iloc[0]
        result.append((str(row["Word"]).strip(), level.capitalize()))

    return result if result else None


# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------
def build_prompt(words: WordList) -> str:
    tense = random.choice(TENSES)
    lines = ["You are a professional English tutor. Analyse the following words.\n\nWords:\n"]
    for word, level in words:
        lines.append(f"- {word} ({level})")

    lines.append(
        f"\n\nFor EACH word, use this exact format:\n\n"
        f"📖 **[WORD IN UPPERCASE]** `[Level]`\n\n"
        f"🔹 **Part of Speech**: [text]\n\n"
        f"🔹 **Synonyms**: [3 synonyms]\n\n"
        f"🔹 **Example**: [one clear sentence]\n\n"
        f"🔹 **Grammar Tip**: [one usage rule]\n\n"
        f"🔹 **Tense Tip** ({tense}): [one example sentence]\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Return only the word details. No intro or outro text."
    )
    return "\n".join(lines)


def fetch_word_details(words: WordList, cfg: Config, retries: int = 3) -> Optional[str]:
    """Call OpenRouter once for all words; retry on transient failures."""
    headers = {
        "Authorization": f"Bearer {cfg.openrouter_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Vocabulary Bot",
    }
    payload = {
        "model": cfg.model_id,
        "messages": [{"role": "user", "content": build_prompt(words)}],
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=cfg.request_timeout
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            log.warning("OpenRouter timeout (attempt %d/%d).", attempt, retries)
        except requests.exceptions.HTTPError as exc:
            log.error("OpenRouter HTTP error: %s", exc)
            break
        except Exception as exc:
            log.error("OpenRouter unexpected error: %s", exc)
            break

        if attempt < retries:
            time.sleep(2**attempt)  # exponential back-off

    return None


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def send_telegram(user: TelegramUser, text: str, timeout: int = 20) -> bool:
    """Send *text* to a single Telegram user; return success flag."""
    url = TELEGRAM_URL.format(token=user.token)
    payload = {"chat_id": user.chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return True
    except requests.exceptions.HTTPError as exc:
        log.error("Telegram HTTP error for chat_id=%s: %s", user.chat_id, exc)
    except Exception as exc:
        log.error("Telegram error for chat_id=%s: %s", user.chat_id, exc)
    return False


def broadcast(users: list[TelegramUser], message: str) -> None:
    """Send *message* to every user and log results."""
    for user in users:
        ok = send_telegram(user, message)
        if ok:
            log.info("✅ Sent to chat_id=%s", user.chat_id)
        else:
            log.warning("❌ Failed for chat_id=%s", user.chat_id)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def build_message(content: str) -> str:
    return "🌟 *DAILY VOCABULARY BOOST* 🌟\n\n" + content


def main() -> None:
    cfg = load_config()
    log.info("Starting Vocab Sender (model=%s)…", cfg.model_id)

    df = load_vocabulary(cfg.csv_dir)
    if df is None:
        sys.exit(1)

    words = pick_words(df)
    if not words:
        log.error("Could not select words. Aborting.")
        sys.exit(1)

    log.info("Selected words: %s", [w for w, _ in words])

    content = fetch_word_details(words, cfg)
    if not content:
        log.error("Failed to fetch word details from OpenRouter.")
        sys.exit(1)

    broadcast(cfg.users, build_message(content))


if __name__ == "__main__":
    main()
