# Operation Iron-Mask: Deployment Guide

## 🚀 Quick Start (Local Development)

### 1. Install Dependencies
```bash
cd "H:\guvi project"
pip install -r requirements.txt
```

### 2. Set Up Environment
The `.env` file is already configured with your API keys.

### 3. Set Up Database
1. Open your InsForge project dashboard
2. Navigate to the SQL editor
3. Copy the contents of `database/schema.sql`
4. Run the SQL to create tables

### 4. Run Locally
```bash
python app.py
```
Server starts at: `http://localhost:5000`

### 5. Test the API
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/honey-pot" `
  -Method POST `
  -Headers @{"x-api-key"="sk_ironmask_hackathon_2026";"Content-Type"="application/json"} `
  -Body '{"sessionId":"test-001","message":{"sender":"scammer","text":"Your bank account is blocked! Send OTP now!"},"conversationHistory":[]}'
```

---

## ☁️ Cloud Deployment (Render)

### 1. Create Render Account
Go to [render.com](https://render.com) and sign up.

### 2. Create New Web Service
- Connect your GitHub repository OR use manual deploy
- Select **Python 3** environment

### 3. Configuration
| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | Free |

### 4. Environment Variables
Add these in Render dashboard:
```
HONEYPOT_API_KEY=sk_ironmask_hackathon_2026
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct:free
INSFORGE_BASE_URL=https://your-project.insforge.app
INSFORGE_ANON_KEY=your_insforge_anon_key
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
```

### 5. Deploy
Click "Create Web Service" and wait for deployment.

Your URL will be: `https://your-app-name.onrender.com`

---

## 📝 GUVI Submission

### Submit to Hackathon Portal

1. Go to GUVI Hackathon Portal
2. Navigate to **API Endpoint Submission**
3. Enter:
   - **API Endpoint**: `https://your-app-name.onrender.com/api/honey-pot`
   - **API Key**: `sk_ironmask_hackathon_2026`

### Test with GUVI Tester
Use the "Honeypot API Endpoint Tester" on GUVI dashboard to verify.

---

## 🔍 Project Structure

```
H:\guvi project\
├── app.py                    # Main Flask API
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
├── core/
│   ├── persona.py            # Dynamic persona generator
│   ├── llm_client.py         # OpenRouter integration
│   └── fake_data.py          # Realistic fake data
├── models/
│   ├── schemas.py            # Pydantic models
│   └── intelligence.py       # Extraction patterns
├── utils/
│   ├── luhn.py               # Card number validation
│   ├── insforge_client.py    # Database operations
│   └── guvi_callback.py      # GUVI reporting
├── data/
│   └── indian_data.json      # Names, cities, banks
└── database/
    └── schema.sql            # Database schema
```

---

## 🧪 Test Cases

### Test 1: Bank Fraud Detection
```json
{
  "sessionId": "test-bank-001",
  "message": {
    "sender": "scammer",
    "text": "Your SBI account will be blocked today. Send your UPI PIN immediately to verify."
  },
  "conversationHistory": []
}
```

### Test 2: Digital Arrest Scam
```json
{
  "sessionId": "test-arrest-001",
  "message": {
    "sender": "scammer",
    "text": "This is CBI calling. You are under digital arrest. Pay ₹50,000 fine to avoid jail."
  },
  "conversationHistory": []
}
```

### Test 3: Multi-turn with UPI Extraction
```json
{
  "sessionId": "test-upi-001",
  "message": {
    "sender": "scammer",
    "text": "Send ₹1000 to my UPI fraudster99@ybl to unlock your account"
  },
  "conversationHistory": [
    {"sender": "scammer", "text": "Your account is blocked!"},
    {"sender": "user", "text": "Oh no! What happened?"}
  ]
}
```

---

## ✅ Verification Checklist

- [ ] API returns `status: success`
- [ ] `scamDetected: true` for scam messages
- [ ] `reply` contains confused elderly persona response
- [ ] UPI/Bank extraction works (check `extractedIntelligence`)
- [ ] Same session returns same persona details
- [ ] GUVI callback sent when intel extracted
