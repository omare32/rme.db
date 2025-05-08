from openai import OpenAI
import mysql.connector as mysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Keywords for forced summarization even if short
action_keywords = [
    "please", "kindly", "appreciate", "request", "approve",
    "send", "update", "feedback", "urgent", "important",
    "reply", "respond", "need", "required", "inform", "attached"
]

# Check if email should be summarized
def should_summarize(body):
    lines = body.strip().splitlines()
    char_count = len(body.strip())
    has_keywords = any(word in body.lower() for word in action_keywords)

    if len(lines) >= 3 or char_count >= 400 or has_keywords:
        return True  # Summarize large emails or short actionable ones

    print(f"⚠️ Skipped — too short & no keywords (lines={len(lines)}, chars={char_count})")
    return False

# Summarize + Draft reply generation
def summarize_and_draft(body):
    print(f"📨 Processing email...")

    summary_prompt = (
        "Summarize the core purpose of this email in **one concise sentence**. "
        "Ignore footers, names, greetings, and email signatures. "
        "Do not include phrases like 'Best regards' or sender information. "
        "Just the essence of the message:\n\n" + body.strip()
    )

    draft_prompt = (
        "Based on the following email, write a short and polite draft reply "
        "that acknowledges the sender and provides an appropriate response. "
        "If no reply is needed, reply with: 'No reply needed.'\n\n"
        + body.strip()
    )

    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.3
    )
    summary = summary_response.choices[0].message.content.strip()

    draft_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": draft_prompt}],
        temperature=0.3
    )
    draft_reply = draft_response.choices[0].message.content.strip()

    print(f"✅ Summary & Draft generated.")
    return summary, draft_reply

def main():
    # Connect to MySQL
    try:
        print("🔌 Connecting to MySQL...")
        cnx = mysql.connect(
            host="10.10.11.242",
            user="omar2",
            password="Omar_54321",
            database="RME_TEST"
        )
        cursor = cnx.cursor(dictionary=True)
        print("✅ Connected.")

        cursor.execute("""
            SELECT id, body FROM nada_Emails3
            WHERE summarize IS NULL OR summarize = ''
        """)
        rows = cursor.fetchall()

        summarized_count = 0

        for row in rows:
            if not should_summarize(row["body"]):
                continue

            summary, draft_reply = summarize_and_draft(row["body"])
            cursor.execute("""
                UPDATE nada_Emails3 
                SET summarize = %s, draft_reply = %s
                WHERE id = %s
            """, (summary, draft_reply, row["id"]))
            print(f"📝 Email ID {row['id']} updated.")
            summarized_count += 1

        cnx.commit()
        print(f"\n✅ All eligible emails summarized and draft replies generated. Total: {summarized_count}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnx' in locals() and cnx.is_connected():
            cnx.close()
            print("🔒 MySQL connection closed.")

if __name__ == "__main__":
    main() 