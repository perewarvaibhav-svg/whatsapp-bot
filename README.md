# SmartVenue AI 🏟️

A WhatsApp-based AI assistant that improves attendee experience at large sporting venues. Users can ask for real-time navigation, wait times, food recommendations, parking guidance, and emergency help — all through WhatsApp, with no app download required.

## 📁 File Structure
```
├── app.py              ← Main Flask application (Meta API + Groq Llama3)
├── requirements.txt    ← Python dependencies
├── .env.example        ← Environment variable template
└── README.md
```

## ⚙️ Environment Variables
Create a `.env` file in the project root with your API keys:
```
GROQ_API_KEY=your_groq_api_key
WHATSAPP_PHONE_NUMBER_ID=your_meta_phone_number_id
WHATSAPP_TOKEN=your_meta_access_token
WHATSAPP_VERIFY_TOKEN=smartvenue123
PORT=5000
```

---

## 🚀 Local Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your keys to .env file

# 4. Run the server
python app.py

# 5. Expose to internet (new terminal)
ngrok http 5000
```

---

## 📞 Meta WhatsApp Cloud API Setup

1. **Sign up** at [developers.facebook.com](https://developers.facebook.com/) and create a **Business** App.
2. In your app dashboard, add **WhatsApp** and click **Set up**.
3. Go to **WhatsApp > API Setup**. You will be given a **Temporary Access Token** and a **Phone Number ID**. Paste these into your `.env` file.
4. Under the "To" field, click **Manage phone number list** and add your personal WhatsApp number to verify it as a tester.
5. Go to **WhatsApp > Configuration** to set up your Webhook.
6. Click **Edit** next to Webhook:
   - **Callback URL**: `https://your-ngrok-url.ngrok-free.app/webhook` (or Render URL)
   - **Verify Token**: `smartvenue123`
7. Click **Verify and Save**. Then subscribe to the **messages** webhook!

---

## ☁️ Deploying on Render

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repository.
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Add environment variables in the Render dashboard:
   - `GROQ_API_KEY`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_TOKEN`
   - `WHATSAPP_VERIFY_TOKEN` (set to `smartvenue123`)
6. Deploy! Copy the live URL and paste `<url>/webhook` into your Meta Webhook Configuration.

---

## 💬 Example Queries

| User Message | Bot Response |
|---|---|
| `Route to Gate 3` | Navigation path with crowd level & time |
| `Which food stall has less wait` | All stall wait times + best recommendation |
| `Nearest washroom` | Closest washroom with crowd level |
| `Emergency exit` | 🚨 Emergency mode with calm evacuation steps |
| `Best time to leave parking` | Parking lot capacity + optimal exit window |
