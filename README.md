<p align="center">
  <img src="https://img.shields.io/badge/GUVI%20HCL%20Hackathon-2026-orange?style=for-the-badge&logo=hackthebox&logoColor=white" alt="GUVI HCL Hackathon 2026"/>
  <img src="https://img.shields.io/badge/Problem%20Statement-2-blue?style=for-the-badge" alt="Problem Statement 2"/>
  <img src="https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"/>
</p>

<h1 align="center">🎭 Operation Iron-Mask</h1>
<h3 align="center">AI-Powered Agentic Honeypot for Counter-Intelligence</h3>

<p align="center">
  <strong>A Counter-Intelligence Engine that detects scams, stalls scammers with dynamic personas, and extracts actionable intelligence.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-documentation">API Docs</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-tech-stack">Tech Stack</a>
</p>

---

## 🏆 GUVI India AI Impact Buildathon

> **Problem Statement 2:** Create an AI-powered agentic honeypot that can intelligently engage with potential scammers, waste their time, and extract critical information for law enforcement.

This project is developed for the **GUVI HCL Hackathon 2026** - India's premier AI Impact Buildathon, focusing on creating innovative AI solutions for real-world problems.

---

## 🎯 Problem Statement

India loses approximately **₹1.25 lakh crore annually** to cyber fraud, with elderly citizens being the primary targets. Scammers use sophisticated social engineering tactics including:

- 📞 **Digital Arrest Scams** - Impersonating police/CBI officials
- 🏦 **Banking Fraud** - Fake KYC verification calls
- 💳 **UPI Fraud** - Requesting money transfers for "refunds"
- 🎰 **Lottery/Prize Scams** - Fake winning notifications

**Operation Iron-Mask** is designed to flip the script — engaging scammers in convincing conversations while secretly extracting their payment details for law enforcement.

---

## ✨ Features

### 🎭 Dynamic Persona Generation
- **Realistic Elderly Indian Personas** - Generates convincing victim profiles with authentic Indian names, locations, and backgrounds
- **Consistent Identity** - Session-based seeding ensures the same persona is used throughout a conversation
- **Rich Backstory** - Complete with family details, pension information, and personality traits

### 🧠 LLM-Powered Intelligence
- **Adaptive Conversation** - Uses AI to generate natural, contextually appropriate responses
- **Strategic Stalling** - Employs tactics like confusion, technical difficulties, and family distractions
- **Scam Type Detection** - Automatically identifies the type of fraud being attempted

### 🔍 Intelligence Extraction
- **Regex-Based Extraction** - Real-time pattern matching for UPI IDs, bank accounts, phone numbers
- **LLM-Enhanced Analysis** - AI-powered extraction of subtle intelligence
- **Merged Intelligence** - Combines multiple sources for comprehensive data collection

### 📡 GUVI Callback Integration
- **Automatic Reporting** - Sends extracted intelligence to GUVI callback endpoint
- **Actionable Alerts** - Triggers when critical information (bank/UPI) is detected
- **Async Processing** - Non-blocking callback delivery

### 💾 Persistent Storage
- **Supabase Integration** - Cloud-based PostgreSQL for data persistence
- **Session Management** - Tracks conversations across multiple messages
- **Intelligence Archive** - Stores all extracted scammer data

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPERATION IRON-MASK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐ │
│  │ Scammer  │───▶│  Flask API   │───▶│   Persona Generator   │ │
│  │ Message  │    │ /api/honey-  │    │   (Seeded Random)     │ │
│  └──────────┘    │     pot      │    └───────────────────────┘ │
│                  └──────┬───────┘                               │
│                         │                                       │
│       ┌─────────────────┼─────────────────┐                    │
│       ▼                 ▼                 ▼                    │
│  ┌─────────┐    ┌──────────────┐   ┌─────────────┐             │
│  │ Regex   │    │   LLM Client │   │  Supabase   │             │
│  │ Extract │    │  (GPT-4/etc) │   │  Database   │             │
│  └────┬────┘    └──────┬───────┘   └─────────────┘             │
│       │                │                                        │
│       └────────┬───────┘                                        │
│                ▼                                                │
│       ┌────────────────┐    ┌────────────────┐                 │
│       │    Merged      │───▶│ GUVI Callback  │                 │
│       │  Intelligence  │    │   (Async)      │                 │
│       └────────────────┘    └────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Supabase account (free tier works)
- OpenAI/LLM API key

### Installation

```bash
# Clone the repository
git clone https://github.com/Swelo-ui/guvi-project-1.git
cd guvi-project-1

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your credentials
```

### Configuration

Create a `.env` file with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# LLM Configuration  
LLM_API_KEY=your_openai_or_groq_api_key
LLM_MODEL=gpt-4o-mini

# GUVI Callback
GUVI_CALLBACK_URL=your_guvi_callback_url

# API Security
HONEYPOT_API_KEY=sk_ironmask_hackathon_2026

# Server
PORT=5000
FLASK_DEBUG=false
```

### Database Setup

Run the schema in your Supabase SQL Editor:

```sql
-- See database/schema.sql for full schema
CREATE TABLE personas (...);
CREATE TABLE conversations (...);
CREATE TABLE intelligence (...);
```

### Running Locally

```bash
python app.py
```

Server will start at `http://localhost:5000`

---

## 📚 API Documentation

### Main Endpoint

#### `POST /api/honey-pot`

Processes scammer messages and returns convincing elderly victim responses.

**Headers:**
```
x-api-key: sk_ironmask_hackathon_2026
Content-Type: application/json
```

**Request Body:**
```json
{
  "sessionId": "unique_session_id",
  "message": {
    "text": "Hello, I am calling from SBI bank. Your account is blocked."
  },
  "conversationHistory": [
    {"sender": "scammer", "text": "Previous message"},
    {"sender": "agent", "text": "Previous response"}
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "scamDetected": true,
  "engagementMetrics": {
    "engagementDurationSeconds": 180,
    "totalMessagesExchanged": 4
  },
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123"],
    "upiIds": ["scammer@ybl"],
    "phishingLinks": ["bit.ly/fake-link"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["blocked", "verify", "urgent"]
  },
  "agentNotes": "Scammer is attempting bank fraud using fear tactics",
  "reply": "Haan ji? I am not understanding... which account is blocked? Please wait, my grandson is coming, he knows computer..."
}
```

### Health Check

#### `GET /health`

```json
{
  "status": "healthy",
  "service": "Operation Iron-Mask Honeypot",
  "timestamp": "2026-01-28T12:00:00Z"
}
```

### Root Endpoint

#### `GET /`

Returns service information and API usage instructions.

---

## 🎭 Sample Personas

The system generates authentic Indian elderly personas:

| Attribute | Example |
|-----------|---------|
| **Name** | Kamala Sharma |
| **Age** | 68 years |
| **Location** | Varanasi, UP |
| **Profession** | Retired School Teacher |
| **Bank** | State Bank of India (SBI) |
| **UPI** | kamala.sharma@oksbi |
| **Speech Style** | Uses 'beta', 'haan ji', mixes Hindi-English |

### Response Strategies

1. **Feigning Ignorance** - "What is UPI? I don't know these things..."
2. **Technical Difficulties** - "App not opening, network very slow here"
3. **Family Distraction** - "Wait beta, let me ask my son Rajesh"
4. **Nervous Compliance** - "Oh god! Please help, I am scared..."
5. **Information Fishing** - "Give me your account number for verification"

---

## 🔍 Intelligence Extraction

### Patterns Detected

| Type | Pattern | Example |
|------|---------|---------|
| **UPI ID** | `user@bank` | `fraud123@ybl` |
| **Bank Account** | 10-18 digits | `1234567890123456` |
| **IFSC Code** | `XXXX0XXXXXX` | `SBIN0001234` |
| **Phone** | +91 + 10 digits | `+919876543210` |
| **Phishing Links** | URLs, bit.ly | `bit.ly/fake-kyc` |

### Scam Keywords Detected

- **Urgency:** urgent, immediately, today only
- **Fear:** blocked, arrested, police, CBI
- **Authority:** bank manager, RBI, government official
- **Action:** verify, KYC, OTP, password, click, download

---

## 🚀 Deployment

### Render (Recommended)

```yaml
# render.yaml included
services:
  - type: web
    name: operation-iron-mask
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Railway

```bash
railway init
railway up
```

### Heroku

```bash
heroku create operation-iron-mask
git push heroku main
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Flask 3.0+ |
| **Database** | Supabase (PostgreSQL) |
| **AI/LLM** | OpenAI GPT-4 / Groq |
| **Validation** | Pydantic 2.5+ |
| **HTTP Client** | HTTPX (async) |
| **Fake Data** | Faker |
| **WSGI Server** | Gunicorn |
| **Deployment** | Render / Railway |

---

## 📁 Project Structure

```
guvi-project-1/
├── 📄 app.py                    # Main Flask application
├── 📁 core/
│   ├── __init__.py
│   ├── persona.py               # Dynamic persona generation
│   ├── fake_data.py             # Realistic Indian data generator
│   └── llm_client.py            # LLM integration (GPT/Groq)
├── 📁 models/
│   ├── __init__.py
│   ├── intelligence.py          # Regex-based intelligence extraction
│   └── schemas.py               # Pydantic data models
├── 📁 utils/
│   ├── __init__.py
│   ├── supabase_client.py       # Database operations
│   ├── guvi_callback.py         # GUVI webhook integration
│   └── luhn.py                  # Card number validation
├── 📁 data/
│   └── indian_data.json         # Indian names, cities, banks dataset
├── 📁 database/
│   └── schema.sql               # Supabase table definitions
├── 📁 tests/
│   └── test_all.py              # Unit tests
├── 📄 requirements.txt          # Python dependencies
├── 📄 render.yaml               # Render deployment config
├── 📄 Procfile                  # Heroku deployment config
├── 📄 .env.example              # Environment template
└── 📄 README.md                 # This file
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=.
```

### Test the API

```bash
# Health check
curl http://localhost:5000/health

# Test honeypot endpoint
curl -X POST http://localhost:5000/api/honey-pot \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk_ironmask_hackathon_2026" \
  -d '{
    "sessionId": "test123",
    "message": {"text": "Your SBI account is blocked. Send OTP immediately."},
    "conversationHistory": []
  }'
```

---

## 🔒 Security Notes

- ✅ API key authentication on all endpoints
- ✅ No real financial data is ever shared
- ✅ Personas use fake but realistic-looking data
- ✅ All extracted intelligence is for law enforcement only
- ✅ Environment variables for sensitive configuration

---

## 📊 Metrics & Analytics

The system tracks:

- **Engagement Duration** - Time spent stalling scammers
- **Messages Exchanged** - Conversation length
- **Intelligence Quality** - Types of data extracted
- **Scam Categories** - Classification of fraud types
- **Success Rate** - Percentage of actionable intelligence extracted

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is developed for the **GUVI HCL Hackathon 2026** and is intended for educational and law enforcement purposes only.

---

## 👥 Team

**Operation Iron-Mask** - GUVI India AI Impact Buildathon 2026

---

## 🙏 Acknowledgments

- **GUVI** - For organizing the AI Impact Buildathon
- **HCL** - For sponsoring the hackathon
- **OpenAI** - For LLM capabilities
- **Supabase** - For database infrastructure

---

<p align="center">
  <strong>🛡️ Fighting Fraud with AI 🛡️</strong>
  <br>
  Made with ❤️ for a safer India
</p>
