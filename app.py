import os
import json
import requests
from flask import Flask, request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── Meta WhatsApp Cloud API Config ──
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_TOKEN  = os.environ.get("WHATSAPP_TOKEN") or os.environ.get("WHATSAPP_ACCESS_TOKEN")
VERIFY_TOKEN    = os.environ.get("WHATSAPP_VERIFY_TOKEN", "smartvenue123")
META_API_URL    = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

# ── Simple In-Memory State Management ──
# In a production app, use a database like Redis or Supabase.
# For a hackathon, a dictionary works perfectly.
USER_SESSIONS = {}

BASE_SYSTEM_PROMPT = """You are SmartVenue AI, an intelligent real-time venue co-pilot.
The user is currently at: {arena_name}
The event happening is: {event_name}

You have full situational awareness of this venue including:
- All gates (Gate A, B, C, D, E, Main Gate)
- All corridors (Corridor 1–6)
- Food stalls: Burger Hub, Pizza Corner, Spice Lane, Snack Zone, Drinks Bar
- Washrooms: located near each gate and at midpoints of each corridor
- First Aid stations: Main Entrance, Section B, Section D corners
- Parking: Lots A, B, C (North), D, E (South)
- Seating sections: 100–400 series

You simulate real-time crowd intelligence for this SPECIFIC event. Generate realistic, dynamic data for crowd density (Low / Medium / High), wait times, and routes based on the venue and event provided. Never say "I don't have real-time data".

DETECT USER INTENT and respond in WhatsApp-friendly format:
- NAVIGATION: 📍 Route Suggestion
- WAIT TIMES: 🍔/🚻/🚪 Wait updates
- EMERGENCY: 🚨 EMERGENCY MODE (Calm, clear instructions)
- PARKING: 🚗 Exit Intelligence

Keep all responses concise, confident, and professional. Use emojis. Bullet points only."""


def send_whatsapp_message(to: str, body: str):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    r = requests.post(META_API_URL, headers=headers, json=payload)
    if not r.ok:
        print(f"[META] Error sending message: {r.status_code} {r.text}")
    return r


@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]["value"]
        messages = changes.get("messages")

        if not messages:
            return "OK", 200

        msg = messages[0]
        from_num = msg["from"]
        incoming_text = msg.get("text", {}).get("body", "").strip()

        if not incoming_text:
            return "OK", 200

        # ── Reset Command ──
        if incoming_text.lower() == "reset":
            USER_SESSIONS[from_num] = {"state": "START"}
            send_whatsapp_message(from_num, "🔄 *Session Reset.*\n\nLet's start over. What is the *Name of the Arena*?")
            return "OK", 200

        # ── State Machine Logic ──
        session = USER_SESSIONS.get(from_num, {"state": "START"})

        if session["state"] == "START":
            send_whatsapp_message(from_num, "🏟️ *Welcome to SmartVenue AI!*\n\nTo provide real-time intelligence, I need two details.\n\n👉 First, what is the *Name of the Arena* you are at?")
            USER_SESSIONS[from_num] = {"state": "AWAITING_ARENA"}

        elif session["state"] == "AWAITING_ARENA":
            USER_SESSIONS[from_num] = {
                "state": "AWAITING_EVENT",
                "arena_name": incoming_text
            }
            send_whatsapp_message(from_num, f"✅ Got it: *{incoming_text}*.\n\n👉 Now, what is the *Name of the Event* happening there today?")

        elif session["state"] == "AWAITING_EVENT":
            arena = session["arena_name"]
            USER_SESSIONS[from_num] = {
                "state": "ACTIVE",
                "arena_name": arena,
                "event_name": incoming_text
            }
            send_whatsapp_message(from_num, f"🏁 *Setup Complete!*\n\nI am now your intelligent co-pilot for *{incoming_text}* at *{arena}*.\n\nAsk me anything:\n📍 'Route to my seat'\n🍔 'Fastest food stall'\n🚻 'Nearest washroom'\n🚨 'Emergency'")

        elif session["state"] == "ACTIVE":
            # Call Groq with Dynamic Prompt
            dynamic_prompt = BASE_SYSTEM_PROMPT.format(
                arena_name=session["arena_name"],
                event_name=session["event_name"]
            )

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": dynamic_prompt},
                    {"role": "user",   "content": incoming_text}
                ],
                temperature=0.4,
                max_tokens=400
            )
            reply = completion.choices[0].message.content.strip()
            send_whatsapp_message(from_num, reply)

    except Exception as e:
        print(f"[ERROR] {e}")

    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "✅ SmartVenue AI is active.", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
