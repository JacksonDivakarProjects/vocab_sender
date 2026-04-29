import os
import random
import time
import pandas as pd
import requests
from dotenv import load_dotenv

# === Configuration ===
load_dotenv()

# Path to your CSV folder
CSV_DIR = os.getenv("CSV_PATH")

# API Keys from your .env file
OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_KEY")

USERS = [
    {
        "token": os.getenv("TELEGRAM_KEY"),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID")
    }
]

# OpenRouter Settings
# You can change this to any free model, e.g., "google/gemini-2.0-flash-exp:free"
MODEL_ID = os.getenv("MODEL_ID")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

TENSES = [
    "Simple Present", "Present Continuous", "Present Perfect",
    "Simple Past", "Past Continuous", "Future Simple"
]

def pick_three_words():
    """Picks one word from each level with robust header and group handling."""
    try:
        csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith(".csv")]
        if not csv_files: 
            print("❌ No CSV files found.")
            return None
            
        all_dfs = []
        for f in csv_files:
            temp_df = pd.read_csv(os.path.join(CSV_DIR, f))
            # Standardize headers to 'Word' and 'Level'
            temp_df.columns = [str(col).strip().capitalize() for col in temp_df.columns]
            all_dfs.append(temp_df)
            
        df = pd.concat(all_dfs, ignore_index=True)
        df["Level"] = df["Level"].astype(str).str.strip().str.lower()
        
        levels = ["beginner", "intermediate", "advanced"]
        filtered_df = df[df["Level"].isin(levels)]

        # FIX: We use a list to store results instead of .apply() to avoid group-exclusion errors
        sampled_list = []
        for level in levels:
            group = filtered_df[filtered_df["Level"] == level]
            if not group.empty:
                sampled_list.append(group.sample(1).iloc[0])
        
        if not sampled_list:
            return None

        # Create a clean list of tuples
        return [(str(row["Word"]).strip(), str(row["Level"]).capitalize()) for row in sampled_list]
        
    except Exception as e:
        print(f"❌ Data Error: {e}")
        return None
    

def get_combined_details(word_list):
    """
    Sends all 3 words in ONE request to OpenRouter to save quota.
    """
    random_tense = random.choice(TENSES)
    
    # Build the same prompt as before
    prompt = (
        "You are a professional English tutor. Analyze the following 3 words for a vocabulary bot.\n\n"
        "Words to analyze:\n"
    )
    
    for word, level in word_list:
        prompt += f"- {word} ({level})\n"
        
    prompt += (
        f"\nFor EACH word, provide the following details strictly formatted with double newlines for legibility:\n\n"
        f"📖 **[WORD IN UPPERCASE]** `[Level]`\n\n"
        f"🔹 **Part of Speech**: [Text]\n\n"
        f"🔹 **Synonyms**: [List 3 synonyms]\n\n"
        f"🔹 **Example**: [One clear sentence]\n\n"
        f"🔹 **Grammar Tip**: [One usage rule]\n\n"
        f"🔹 **Tense Tip** ({random_tense}): [One example sentence]\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Do not include any intro or outro text. Only return the word details."
    )
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000", # Optional: for OpenRouter rankings
        "X-Title": "Vocabulary Bot" 
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"⚠️ OpenRouter API Error: {e}"

def send_to_telegram(token, chat_id, text):
    """Sends the final combined message to Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        res.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def main():
    print(f"🚀 Starting OpenRouter Vocabulary Bot ({MODEL_ID})...")
    words = pick_three_words()
    if not words: return

    print(f"Generating details for: {', '.join([w[0] for w in words])}...")
    
    # ONE API call instead of three
    content = get_combined_details(words)

    # Assemble the final message
    full_message = "🌟 *DAILY VOCABULARY BOOST* 🌟\n"
    full_message += "\n\n"
    full_message += content

    for user in USERS:
        if send_to_telegram(user['token'], user['chat_id'], full_message):
            print(f"✅ Success! Message sent to: {user['chat_id']}")

if __name__ == "__main__":
    main()