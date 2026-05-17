# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into an isolated prefix so the final image stays lean
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for security
RUN useradd --create-home --shell /bin/bash vocabbot
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY vocab_sender.py .

# vocabulary CSVs will be mounted at /app/vocab_data at runtime
RUN mkdir -p /app/vocab_data && chown vocabbot:vocabbot /app/vocab_data

# Log file lives inside the container (persist via volume if needed)
RUN touch /app/vocab_bot.log && chown vocabbot:vocabbot /app/vocab_bot.log

USER vocabbot

# ── Environment defaults (override via --env-file or -e flags) ───────────────
ENV CSV_PATH=./vocab_data \
    MODEL_ID=google/gemini-2.0-flash-exp:free \
    PYTHONUNBUFFERED=1

# The container runs the bot once and exits (designed for cron / scheduler).
CMD ["python", "vocab_sender.py"]
