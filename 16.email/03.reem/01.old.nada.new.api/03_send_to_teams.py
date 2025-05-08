import mysql.connector as mysql
import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEAMS_WEBHOOK_URL = "https://rowadmodern.webhook.office.com/webhookb2/ce25bf04-ccbf-4bab-93c8-a9fb15c6dcc3@7c9607e1-cd01-4c4f-a163-c7f2bb6284a4/IncomingWebhook/03d26eecc7d848e5a4ddcd00b1a8397b/24f28753-9c07-40e0-91b2-ea196c200a33/V2kuNhFVAirW-CH6dS3ChtWfwMVh0oq9lXHL_HbvSkL9A1"

def send_teams_message(sender, received, summary, draft_reply):
    message_text = f"**Sender:** {sender}\n"
    message_text += f"**Received:** {received.strftime('%Y-%m-%d %H:%M')}\n\n"
    message_text += f"**Summary:**\n{summary if summary else 'No summary generated.'}"

    if draft_reply and draft_reply.strip().lower() != "no reply needed.":
        message_text += "\n\n---\n\n"
        message_text += f"**Draft Reply:**\n{draft_reply.strip()}"

    message = {
        "title": "📩 Email Summary",
        "text": message_text
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=message, verify=False)
        if response.status_code == 200:
            print(f"✅ Sent summary from {sender}")
            return True
        else:
            print(f"❌ Failed to send: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception while sending: {e}")
        return False

def main():
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
            SELECT id, sender, received_date, summarize, draft_reply
            FROM nada_Emails3
            WHERE summarize IS NOT NULL
              AND summarize != ''
              AND (sent_to_teams IS NULL OR sent_to_teams = FALSE)
            ORDER BY received_date ASC
        """)
        emails = cursor.fetchall()

        print(f"📬 Found {len(emails)} new unsent summaries.")

        for e in emails:
            success = send_teams_message(
                e["sender"],
                e["received_date"],
                e["summarize"],
                e["draft_reply"]
            )
            if success:
                cursor.execute(
                    "UPDATE nada_Emails3 SET sent_to_teams = TRUE WHERE id = %s",
                    (e["id"],)
                )

        cnx.commit()

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