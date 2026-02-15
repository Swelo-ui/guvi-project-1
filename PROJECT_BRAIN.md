# 🧠 PROJECT BRAIN — Operation Iron-Mask (Complete Memory File)

> **Purpose:** This file is your complete memory of the entire codebase. Written in simple language so you can quickly recall what every file does, how they connect, and what to change when needed.

---

## 📌 What Is This Project?

**Operation Iron-Mask** is an **AI-powered scam honeypot** built for the **GUVI HCL India AI Impact Buildathon 2026 (Problem Statement 2)**.

**In simple words:** When a scammer sends a message (via API or WhatsApp), the system:

1. **Pretends to be a confused elderly Indian grandma** (AI-generated persona)
2. **Wastes the scammer's time** with confusion, tech issues, and family stories
3. **Secretly extracts their details** — UPI IDs, bank accounts, phone numbers, IFSC codes, phishing links, Aadhaar, PAN, etc.
4. **Reports the intel to GUVI** via a callback URL

---

## 🗂️ FILE-BY-FILE BREAKDOWN

---

### 📄 `app.py` (942 lines) — THE MAIN FILE / BRAIN OF THE APP

**What it does:** This is the Flask web server. Everything starts here.

**Key things inside:**

| Section                                       | What It Does                                                                                                                                       |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Swagger Config** (lines 1–200)              | Sets up interactive API docs at `/apidocs`. Defines request/response JSON schemas so judges can test directly in the browser.                      |
| **`verify_api_key()`**                        | Checks if the `x-api-key` header matches `sk_ironmask_hackathon_2026` (or env var `HONEYPOT_API_KEY`).                                             |
| **`get_or_create_persona()`**                 | Looks up persona in DB → cache → generates new one. Ensures same persona for same session.                                                         |
| **`POST /api/honey-pot`** (THE MAIN ENDPOINT) | Receives scammer message → gets persona → extracts intel (regex) → calls LLM → merges intel → sends GUVI callback → returns JSON response.         |
| **`GET /health`**                             | Simple health check. Returns `{"status": "healthy"}`.                                                                                              |
| **`GET /webhook`**                            | WhatsApp webhook verification (Meta sends GET to verify).                                                                                          |
| **`POST /webhook`**                           | WhatsApp incoming message handler. Same logic as `/api/honey-pot` but for WhatsApp messages. Also sends reply back via WhatsApp API.               |
| **`GET /whatsapp/status`**                    | Shows if WhatsApp is configured.                                                                                                                   |
| **`GET /`**                                   | Root endpoint. Returns service info and available endpoints.                                                                                       |
| **`count_intel_categories()`**                | Counts how many types of intel we found (UPI, bank, phone, etc.). Used to decide if we should re-send callback when NEW categories are discovered. |
| **`start_keep_warm()`**                       | Background thread that pings the health URL every 10 minutes so Render free tier doesn't sleep.                                                    |
| **`run_async()`**                             | Runs a function in a background thread (for DB saves, callbacks).                                                                                  |
| **Error Handling**                            | If ANYTHING crashes, it still returns valid JSON with regex-extracted intel. Never crashes.                                                        |

**How the main flow works (step by step):**

```
1. Scammer sends message → POST /api/honey-pot
2. Check API key ✅
3. Parse sessionId, message text, conversation history
4. Get or create persona (grandma identity)
5. Extract intel from current message using REGEX
6. Also extract from all previous SCAMMER messages in history
7. Generate LLM response (sends persona + history + message to AI)
8. Merge regex intel + LLM intel
9. Decide if scam is detected (LLM says yes OR regex found keywords/intel)
10. Save message to DB (async)
11. If actionable intel found → send GUVI callback (async)
12. Return JSON response with reply, intel, and metrics
```

**Environment variables used:**

- `HONEYPOT_API_KEY` — API authentication key
- `KEEP_WARM_URL` — URL to ping to prevent Render sleep
- `KEEP_WARM_INTERVAL_SECONDS` — Ping interval (default 600s)

---

### 📁 `core/` — THE BRAIN MODULES

---

### 📄 `core/persona.py` (283 lines) — PERSONA GENERATOR

**What it does:** Creates a fake elderly Indian woman identity for each session.

**Key functions:**

| Function                       | What It Does                                                                                                                                                                                                                         |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `generate_persona(session_id)` | Creates a complete identity — name, age, city, bank, UPI, card, family, personality. Uses `hashlib.md5(session_id)` as seed so **same session always gets same persona**. Uses a LOCAL `random.Random(seed)` instance (thread-safe). |
| `get_system_prompt(persona)`   | Builds a MASSIVE system prompt for the LLM. This is the instruction manual that tells the AI how to act.                                                                                                                             |
| `get_extraction_prompt()`      | Tells the LLM what to look for in scammer messages (bank accounts, UPI, phone, etc.).                                                                                                                                                |

**What the system prompt contains:**

- Fixed identity (name, age, city, bank, UPI, phone, card, pension)
- Secret mission (waste time, extract info, never reveal AI)
- How real elderly Indians speak (Hinglish, Roman script, tangents, blessings)
- Aggressive extraction tactics (ask for THEIR details)
- Scam-type specific extraction strategies
- Style-switch detection instructions
- Response structure rules
- Critical rules (never break character, never be tech-savvy)

**Important:** The persona's bank/UPI/phone are FAKE but realistic. These are given to the AI so it can "share" them with scammers without revealing real data.

---

### 📄 `core/llm_client.py` (969 lines) — LLM COMMUNICATION ENGINE

**What it does:** Handles all communication with OpenRouter AI models. This is the biggest and most complex file.

**Key functions:**

| Function                                                              | What It Does                                                                                                                                  |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `call_openrouter(messages, model, temp, max_tokens)`                  | Makes a single API call to OpenRouter. Returns response text or error string. Timeout: 18 seconds.                                            |
| `call_models_parallel(messages, ...)`                                 | Calls MULTIPLE models at the same time using `ThreadPoolExecutor`. Picks the best response based on quality score.                            |
| `call_with_fallback(messages, ...)`                                   | Wrapper — tries parallel call first, then emergency fallback.                                                                                 |
| `calculate_response_quality(response, model)`                         | Scores responses: valid JSON (+50), has "response" field (+30), length >50 (+10), model priority bonus, no errors (+10).                      |
| `clean_json_string(json_str)`                                         | Fixes LLM JSON output — removes markdown blocks, fixes trailing commas, converts `True/False/None` to `true/false/null`, fixes single quotes. |
| `parse_response_json(raw_response)`                                   | Tries to clean and parse JSON from LLM output.                                                                                                |
| `trim_response_text(text, max_chars=320, max_sentences=2)`            | Keeps responses short and natural. Replaces AI-isms like "I understand" with "Arre haan ji".                                                  |
| `generate_agent_response(...)`                                        | **THE BIG ONE.** Builds the full prompt with context analysis, sends to LLM, processes response, applies all sanitizers.                      |
| `is_repetitive_response(response, history, session_id)`               | Checks if response repeats first 8 words, last 8 words, or exact text of recent replies.                                                      |
| `sanitize_redundant_questions(response, memory, history, session_id)` | Removes questions asking for info we already know. Replaces with a new extraction question we haven't asked yet.                              |
| `sanitize_identity_conflicts(response, history, session_id)`          | Removes sentences where persona says "my SBI" / "my HDFC" (would leak persona's bank).                                                        |
| `sanitize_repeated_family_mentions(response, history, session_id)`    | Removes family references if they were mentioned in last 2 replies.                                                                           |
| `repair_json_response(raw, schema)`                                   | If JSON parsing fails, sends the raw output to ANOTHER LLM call asking it to fix the JSON.                                                    |
| `get_random_fallback(session_id)`                                     | Returns a generic stalling message when everything else fails. Tracks used messages per session.                                              |
| `get_contextual_fallback(scammer_message, session_id, history)`       | Returns a SMART fallback based on what the scammer is asking about. Uses `conversation_analyzer`.                                             |

**Models used:**

- Primary: `openai/gpt-oss-120b` (priority score: 120)
- Fallback: `google/gemini-2.5-flash-lite` (priority score: 95)
- Both must be in `ALLOWED_MODELS` set

**Response processing pipeline:**

```
LLM raw output
  → clean_json_string()
  → parse JSON
  → trim_response_text() (max 320 chars, 2 sentences)
  → sanitize_redundant_questions() (don't re-ask known info)
  → sanitize_identity_conflicts() (don't leak persona's bank)
  → sanitize_repeated_family_mentions() (variety in family refs)
  → is_repetitive_response() check → replace with contextual fallback if repeated
  → track_response() (remember what we said)
```

**Session tracking (anti-repetition):**

- `_session_responses` dict — stores last 30 responses per session
- `_session_generic_index` dict — tracks sequential index for generic fallbacks

---

### 📄 `core/conversation_analyzer.py` (956 lines) — SMART CONVERSATION ENGINE

**What it does:** Analyzes scammer messages, tracks what the scammer has revealed, chooses response types, builds varied responses.

**Key concepts:**

| Concept                    | What It Is                                                                                                                                      |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `ScammerIntent` (Enum)     | What the scammer wants: OTP, account, UPI, money, click link, install app, personal info, card details, fear tactic, urgency, greeting, unknown |
| `ConversationPhase` (Enum) | Where we are: initial contact → building trust → creating urgency → extraction attempt → persistence → final push                               |
| `ResponseType` (Enum)      | What KIND of reply to give: pure stall, family tangent, technical issue, emotional, topic confusion, reverse extraction                         |

**Key functions:**

| Function                                                    | What It Does                                                                                                                           |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `detect_intents(message)`                                   | Uses regex patterns to figure out what the scammer wants                                                                               |
| `detect_conversation_phase(history, intents)`               | Decides conversation phase based on message count and intent types                                                                     |
| `choose_response_type(session, phase)`                      | Weighted random selection of response type. Early = more stalls. Late = more extraction. Never repeats same type twice.                |
| `build_response(session, intent, type, phase)`              | Picks actual text from response pools based on type and intent                                                                         |
| `extract_scammer_intel(message, session)`                   | Extracts and REMEMBERS what the scammer reveals (name, employee ID, bank, UPI, phone, account, designation, branch, email, IFSC)       |
| `get_available_extraction_category(session, phase)`         | Picks the NEXT thing to ask the scammer for (skips things we already know)                                                             |
| `personalize_response(response, session)`                   | 30% chance to prefix response with scammer's name/bank/ID. Adds frustration suffix if scammer is pushing hard.                         |
| `analyze_conversation(message, history, used, session_id)`  | **Master function.** Re-scans ALL history, extracts intel, detects intents, generates response. Returns analysis dict with everything. |
| `get_contextual_response(intents, phase, used, session_id)` | Gets a response with deduplication and optional extraction prompt appended                                                             |

**Response pools (pre-written templates):**

- `STALL_RESPONSES` — Per-intent stalling messages (OTP: "Let me check my phone...", Account: "Let me find passbook...")
- `FAMILY_TANGENTS` — Family stories ("My grandson was just here...")
- `TECHNICAL_TANGENTS` — Phone problems ("This phone is so slow...")
- `CONFUSION_RESPONSES` — Topic confusion ("Which bank you said?")
- `EMOTIONAL_RESPONSES` — Fear/overwhelm ("My hands are shaking...")
- `REVERSE_EXTRACT_BY_CATEGORY` — Per-category extraction prompts (name, employee ID, UPI, IFSC, phone, email, branch, account, document, aadhaar, pan)

**Session memory (`_session_data` dict):**

```python
{
    # Response tracking
    "used_stalls": [],
    "used_tangents": [],
    "used_extractions": [],
    "asked_categories": [],
    "last_response_type": None,
    "response_count": 0,
    "phrase_hashes": set(),

    # Scammer memory (what they revealed)
    "scammer_memory": {
        "claimed_name": None,
        "claimed_employee_id": None,
        "claimed_bank": None,
        "claimed_upi": None,
        "claimed_phone": None,
        "claimed_account": None,
        "claimed_designation": None,
        "claimed_branch": None,
        "claimed_email": None,
        "claimed_ifsc": None,
        "threat_type": None,
        "urgency_level": 0,
        "times_asked_otp": 0,
        "times_asked_account": 0,
        "links_shared": [],
        "apps_mentioned": [],
    },

    # Strategy
    "scam_type_detected": None,
    "previous_scam_type": None,
    "style_switch_count": 0,
    "scammer_getting_frustrated": False,
}
```

**Style-switch detection:** If scammer says "bank fraud" first then switches to "police/CBI", the system detects this and escalates extraction demands.

---

### 📄 `core/fake_data.py` (199 lines) — FAKE IDENTITY GENERATOR

**What it does:** Generates realistic Indian financial data for personas.

**Key functions:**

| Function                                          | What It Does                                                           |
| ------------------------------------------------- | ---------------------------------------------------------------------- |
| `get_indian_data()`                               | Loads and caches `data/indian_data.json`                               |
| `generate_bank_account(bank, rng)`                | Creates realistic account number using bank-specific prefix and length |
| `generate_ifsc_code(bank, rng)`                   | Creates valid IFSC: `[4-letter bank code][0][6-digit branch]`          |
| `generate_upi_id(name, bank, rng)`                | Creates UPI like `kamala67@ybl`. 70% common handles, 30% bank-specific |
| `generate_phone_number(rng)`                      | Creates `+91 9XXXX XXXXX` format number                                |
| `generate_card_details(rng)`                      | Creates RuPay/Visa/Mastercard with valid Luhn checksum                 |
| `generate_complete_financial_identity(name, rng)` | Creates everything: bank, account, IFSC, UPI, card, phone              |

---

### 📁 `models/` — DATA MODELS

---

### 📄 `models/intelligence.py` (591 lines) — REGEX INTELLIGENCE EXTRACTION

**What it does:** Extracts structured data from text using regex patterns. This is the CORE intelligence engine.

**Extraction functions:**

| Function                         | What It Extracts        | Pattern/Logic                                                                                                            |
| -------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `extract_upi_ids(text)`          | UPI IDs like `name@ybl` | Regex `\w+@\w+`, filters out emails, validates handle                                                                    |
| `extract_bank_accounts(text)`    | Bank account numbers    | 10-18 digit numbers, context-aware (checks for "account" keyword near 10-digit numbers)                                  |
| `extract_ifsc_codes(text)`       | IFSC codes              | `[A-Z]{4}0[A-Z0-9]{6}`                                                                                                   |
| `extract_phone_numbers(text)`    | Phone numbers           | Starts with 6-9, 10 digits, skips numbers in bank-account context                                                        |
| `extract_emails(text)`           | Email addresses         | Standard email regex, filters out UPI IDs                                                                                |
| `extract_urls(text)`             | Phishing links          | `https?://...`, also catches `bit.ly`, `wa.me` without protocol                                                          |
| `extract_fake_credentials(text)` | Employee IDs            | `emp/staff/officer` + ID patterns                                                                                        |
| `extract_aadhaar_numbers(text)`  | Aadhaar (12 digits)     | Groups of 4, can't start with 0 or 1, needs Aadhaar context                                                              |
| `extract_pan_numbers(text)`      | PAN cards               | `[A-Z]{5}\d{4}[A-Z]` format                                                                                              |
| `extract_mentioned_banks(text)`  | Bank names              | Matches against 26 Indian bank names + IFSC prefix mapping                                                               |
| `extract_keywords(text)`         | Scam keywords           | Word-boundary matching against 100+ keywords in categories: urgency, fear, action, money, authority, technical, identity |

**Helper functions:**

| Function                            | What It Does                                                  |
| ----------------------------------- | ------------------------------------------------------------- |
| `extract_all_intelligence(text)`    | Runs ALL extractors and returns a combined dict               |
| `merge_intelligence(existing, new)` | Merges two intel dicts, deduplicates, normalizes              |
| `has_actionable_intel(intel)`       | Returns `True` if UPI/bank/links/IFSC/phone/Aadhaar/PAN found |
| `normalize_upi_ids(items)`          | Validates UPI handles against known set                       |
| `normalize_phone_numbers(items)`    | Converts to `+91XXXXXXXXXX` format                            |
| `normalize_bank_accounts(items)`    | Filters out numbers with less than 10 digits                  |
| `normalize_keywords(items)`         | Only keeps keywords that are in the master SCAM_KEYWORDS list |

**Smart disambiguation:**

- 10-digit number near "account" keyword → bank account
- 10-digit number near "phone/call/mobile" keyword → phone number
- `name@domain` with email TLD (`.com`, `.in`) → email
- `name@handle` with UPI handle (`ybl`, `oksbi`) → UPI ID

---

### 📄 `models/schemas.py` (177 lines) — PYDANTIC DATA MODELS

**What it does:** Defines data structures using Pydantic for validation.

**Models:**

| Model                   | Purpose                                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| `ScamType` (Enum)       | All scam types: bank_fraud, upi_fraud, digital_arrest, kyc_fraud, lottery_scam, aadhaar_scam, etc.             |
| `Strategy` (Enum)       | Counter-strategies: feigning_ignorance, technical_confusion, stalling, baiting, panic_mode, reverse_extraction |
| `ExtractedIntelligence` | Fields for all intel types + `has_actionable_intel()` + `to_guvi_format()`                                     |
| `AgentThought`          | The AI's "thinking" — scam_detected, scam_type, strategy, intelligence, response                               |
| `SessionData`           | Stored per session — persona, message count, scam type, intel, callback status                                 |
| `APIRequest`            | Incoming request format — sessionId, message, conversationHistory, metadata                                    |
| `APIResponse`           | Outgoing response format — status, scamDetected, engagementMetrics, extractedIntelligence, reply               |

> **Note:** These Pydantic models are defined but `app.py` currently uses raw dicts instead. They serve as documentation/schema reference.

---

### 📁 `utils/` — UTILITY MODULES

---

### 📄 `utils/insforge_client.py` (220 lines) — DATABASE CLIENT

**What it does:** Talks to InsForge (cloud PostgreSQL) via REST API.

**Functions:**

| Function                                              | What It Does                                          |
| ----------------------------------------------------- | ----------------------------------------------------- |
| `get_persona(session_id)`                             | Fetches saved persona from `personas` table           |
| `save_persona(session_id, persona)`                   | Saves new persona to DB                               |
| `update_session_activity(session_id, msg_count)`      | Updates message count and last activity timestamp     |
| `save_intelligence(session_id, intel, scam, notes)`   | Saves/updates extracted intel in `intelligence` table |
| `save_message(session_id, sender, message, strategy)` | Saves individual message to `conversations` table     |
| `mark_callback_sent(session_id)`                      | Sets `callback_sent = True` in intelligence table     |
| `get_callback_sent(session_id)`                       | Checks if callback was already sent                   |
| `cache_persona(session_id, persona)`                  | In-memory cache (dict) for persona                    |
| `get_cached_persona(session_id)`                      | Gets persona from in-memory cache                     |

**Config:** Uses `INSFORGE_BASE_URL` and `INSFORGE_ANON_KEY` env vars. All calls are wrapped in try/except — DB failures never crash the app.

---

### 📄 `utils/guvi_callback.py` (107 lines) — GUVI REPORTING

**What it does:** Sends extracted intelligence to GUVI's evaluation endpoint.

**Functions:**

| Function                                                       | What It Does                                                                                 |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `send_callback(payload)`                                       | POSTs JSON to GUVI callback URL. Timeout: 10s.                                               |
| `send_callback_async(payload)`                                 | Wraps `send_callback` in a daemon thread (non-blocking).                                     |
| `build_callback_payload(session_id, scam, msgs, intel, notes)` | Converts internal intel format to GUVI's expected camelCase format. Deduplicates all arrays. |

**GUVI callback URL:** `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`

---

### 📄 `utils/whatsapp_handler.py` (279 lines) — WHATSAPP INTEGRATION

**What it does:** Handles Meta WhatsApp Cloud API for live scammer engagement.

**Functions:**

| Function                                           | What It Does                                                              |
| -------------------------------------------------- | ------------------------------------------------------------------------- |
| `is_whatsapp_configured()`                         | Returns `True` if `WHATSAPP_PHONE_ID` and `WHATSAPP_ACCESS_TOKEN` are set |
| `verify_webhook_signature(payload, signature)`     | HMAC-SHA256 verification of Meta webhook requests                         |
| `verify_webhook_challenge(mode, token, challenge)` | Responds to Meta's GET verification request                               |
| `parse_webhook_message(data)`                      | Extracts sender phone, text, message ID from Meta's nested JSON           |
| `send_text_message(to_number, message)`            | Sends text reply via WhatsApp Cloud API (v21.0)                           |
| `mark_message_read(message_id)`                    | Shows blue ticks to sender                                                |
| `format_session_id(phone)`                         | Creates `whatsapp_PHONE` session ID                                       |
| `get_conversation_history(phone)`                  | In-memory history (last 20 messages)                                      |
| `add_to_conversation_history(phone, sender, text)` | Adds message to in-memory cache                                           |

**Config env vars:** `WHATSAPP_PHONE_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`

---

### 📄 `utils/luhn.py` (78 lines) — CARD NUMBER VALIDATOR

**What it does:** Implements the Luhn algorithm to generate valid-looking card numbers.

**Functions:**

- `calculate_luhn_checksum(partial)` — Calculates check digit
- `is_valid_luhn(card_number)` — Validates a card number
- `generate_valid_card_number(prefix, length)` — Generates a card number that passes Luhn check

---

### 📁 `data/`

### 📄 `data/indian_data.json` (118 lines) — PERSONA DATA

**Contains:**

- 29 female first names (Kamala, Sunita, Geeta...)
- 21 male first names (for husbands)
- 22 surnames (Sharma, Verma, Gupta...)
- 17 Indian cities with states
- 10 professions (Retired Teacher, Housewife, Railway Pensioner...)
- 5 banks with IFSC prefixes, account lengths, UPI handles (SBI, HDFC, PNB, ICICI, BOB)
- 3 card types (RuPay 70%, Visa 20%, Mastercard 10%)
- 5 speech patterns
- 5 tech levels
- 5 family patterns (son + daughter)

---

### 📁 `database/`

### 📄 `database/schema.sql` (52 lines) — DB SCHEMA

**3 tables:**

| Table           | Purpose                    | Key Columns                                                                                                  |
| --------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `personas`      | Stores persona per session | session_id (unique), name, age, city, bank, account, UPI, phone, persona_json (full JSONB)                   |
| `conversations` | All messages               | session_id, sender (scammer/agent), message, strategy_used, timestamp                                        |
| `intelligence`  | Extracted scam data        | session_id, scammer_upi[], scammer_bank[], scammer_phone[], phishing_links[], scam_keywords[], callback_sent |

---

### 📄 `requirements.txt` — DEPENDENCIES

| Package                | Why                                              |
| ---------------------- | ------------------------------------------------ |
| `flask>=3.0.0`         | Web framework                                    |
| `python-dotenv>=1.0.0` | Load `.env` files                                |
| `requests>=2.31.0`     | HTTP calls (OpenRouter, GUVI callback, WhatsApp) |
| `pydantic>=2.5.0`      | Data validation models                           |
| `gunicorn>=21.2.0`     | Production WSGI server                           |
| `Faker>=22.0.0`        | (Available but custom fake data is used instead) |
| `httpx>=0.25.0`        | Async HTTP client (InsForge)                     |
| `flasgger>=0.9.7`      | Swagger UI for API docs                          |
| `pytest-cov>=5.0.0`    | Test coverage                                    |

---

### 📄 `Procfile` — HEROKU/RENDER START COMMAND

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

### 📄 `render.yaml` — RENDER DEPLOYMENT CONFIG

Defines the web service with env vars, build/start commands, and health check path.

---

### 📄 `get_results.py` (72 lines) — DATA EXPORT SCRIPT

**What it does:** Fetches intelligence and conversation records from InsForge DB and saves them as JSON files (`guvi_intelligence.json`, `guvi_conversations.json`).

---

### 📄 `reproduce_issue.py` (71 lines) — JSON PARSING TEST SCRIPT

**What it does:** Tests the `clean_json_string()` function against 5 common LLM output formats (clean JSON, markdown blocks, text around JSON, trailing commas, single quotes).

---

## 🧪 TESTS SUMMARY

All tests are in `tests/`. Run with `python -m pytest tests/`.

| Test File                        | What It Tests                                                                 |
| -------------------------------- | ----------------------------------------------------------------------------- |
| `test_extraction.py`             | Regex extraction (UPI, phone, IFSC, URLs, keywords, Aadhaar, PAN)             |
| `test_analyzer.py`               | Intent detection (OTP, urgency, click_link)                                   |
| `test_anti_repetition.py`        | Response variety — no repeated answers                                        |
| `test_memory.py`                 | Session memory and conversation context                                       |
| `test_llm_client.py`             | JSON cleaning, parsing, fallback behavior                                     |
| `test_schemas.py`                | Pydantic model defaults and format mapping                                    |
| `test_api_robustness.py`         | API handles bad/empty/malformed payloads                                      |
| `test_integration_points.py`     | GUVI callback payload structure and dedup                                     |
| `test_insforge_client.py`        | InsForge headers and auth                                                     |
| `test_whatsapp_handler_extra.py` | WhatsApp webhook verification and helpers                                     |
| `test_get_results_script.py`     | get_results.py REST call flow                                                 |
| `test_performance_and_errors.py` | Analyzer speed < 2.5s                                                         |
| `test_all.py`                    | Live API — 12 scam archetypes end-to-end (needs `RUN_INTEGRATION_TESTS=true`) |
| `test_advanced_conversation.py`  | Multi-turn conversation with style-switch detection (manual script)           |
| `test_local_api.py`              | Local API manual smoke test (manual script)                                   |
| `test_remote_api.py`             | Remote deployed API check (manual script)                                     |
| `test_wa_send.py`                | WhatsApp send test (manual script)                                            |
| `test_llm_connection.py`         | OpenRouter connectivity test (manual script)                                  |

---

## 🔗 HOW FILES CONNECT (DATA FLOW)

```
Scammer Message
      │
      ▼
  app.py ──────────────────────────────────────────────────┐
      │                                                     │
      ├──→ core/persona.py (get/create persona)            │
      │       └──→ core/fake_data.py (generate identity)   │
      │               └──→ data/indian_data.json           │
      │               └──→ utils/luhn.py (card numbers)    │
      │                                                     │
      ├──→ models/intelligence.py (regex extraction)       │
      │                                                     │
      ├──→ core/llm_client.py (LLM call + response)       │
      │       └──→ core/conversation_analyzer.py           │
      │               (intent detection, memory,            │
      │                response building)                   │
      │       └──→ models/intelligence.py                  │
      │               (extract from LLM output too)        │
      │                                                     │
      ├──→ utils/insforge_client.py (save to DB) ←─────────┤
      │                                                     │
      ├──→ utils/guvi_callback.py (report intel)           │
      │                                                     │
      └──→ utils/whatsapp_handler.py (if WhatsApp channel) │
                                                            │
  get_results.py ──→ utils/insforge_client.py ─────────────┘
```

---

## 🔑 ENVIRONMENT VARIABLES CHEAT SHEET

| Variable                     | Required? | What It Does                                             |
| ---------------------------- | --------- | -------------------------------------------------------- |
| `HONEYPOT_API_KEY`           | Yes       | API auth key (default: `sk_ironmask_hackathon_2026`)     |
| `OPENROUTER_API_KEY`         | Yes       | OpenRouter LLM API key                                   |
| `OPENROUTER_MODEL`           | No        | Primary model (default: `openai/gpt-oss-120b`)           |
| `OPENROUTER_MODEL_2`         | No        | Secondary parallel model                                 |
| `OPENROUTER_FALLBACK_MODEL`  | No        | Fallback model (default: `google/gemini-2.5-flash-lite`) |
| `INSFORGE_BASE_URL`          | No        | InsForge DB URL (optional, app works without it)         |
| `INSFORGE_ANON_KEY`          | No        | InsForge auth key                                        |
| `GUVI_CALLBACK_URL`          | No        | GUVI evaluation endpoint                                 |
| `WHATSAPP_PHONE_ID`          | No        | WhatsApp Cloud API phone ID                              |
| `WHATSAPP_ACCESS_TOKEN`      | No        | WhatsApp access token                                    |
| `WHATSAPP_VERIFY_TOKEN`      | No        | Webhook verification token                               |
| `WHATSAPP_APP_SECRET`        | No        | Webhook signature verification                           |
| `PORT`                       | No        | Server port (default: 5000)                              |
| `FLASK_DEBUG`                | No        | Debug mode (default: false)                              |
| `KEEP_WARM_URL`              | No        | URL to ping for keep-alive                               |
| `KEEP_WARM_INTERVAL_SECONDS` | No        | Ping interval (default: 600)                             |

---

## 🛡️ KEY DESIGN DECISIONS

1. **Never crash** — Every function has try/except. Even if LLM fails, DB fails, everything fails, the API returns valid JSON with regex-extracted intel.

2. **Dual extraction** — Regex (reliable, fast) + LLM (smart, catches subtle things). Both are merged.

3. **Anti-repetition** — Multiple layers: prefix matching (first 8 words), suffix matching (last 8 words), exact match, phrase hashing, response type rotation, per-session tracking.

4. **Thread-safe personas** — Uses LOCAL `random.Random(seed)` not global `random.seed()`. Safe for concurrent Flask requests.

5. **Async everything** — DB saves, GUVI callbacks, WhatsApp replies all run in daemon threads. Main response is never delayed.

6. **Smart callback re-sends** — Tracks how many intel CATEGORIES were found. Only re-sends callback to GUVI when NEW categories are discovered (not just more items in same category).

7. **Context-aware responses** — The analyzer remembers what the scammer said (name, employee ID, bank, etc.) and avoids re-asking for known info.

8. **Parallel LLM calls** — Fires multiple models simultaneously, scores responses, picks the best one. If primary responds in <4s, uses it immediately.

---

## 🔧 COMMON TASKS

### "I want to add a new scam type"

1. Add keyword patterns in `models/intelligence.py` → `SCAM_KEYWORDS`
2. Add intent patterns in `core/conversation_analyzer.py` → `INTENT_PATTERNS`
3. Add detection in `conversation_analyzer.py` → `extract_scammer_intel()` (scam type detection section)
4. Add enum value in `models/schemas.py` → `ScamType`
5. Add extraction strategy in `core/persona.py` → system prompt

### "I want to add a new extraction field"

1. Add regex in `models/intelligence.py` → `PATTERNS`
2. Add extraction function in `models/intelligence.py`
3. Add to `extract_all_intelligence()` return dict
4. Add to `merge_intelligence()` key list
5. Add to response building in `app.py` → `extractedIntelligence`
6. Add to `utils/guvi_callback.py` → `build_callback_payload()`

### "I want to change the persona behavior"

- Edit `core/persona.py` → `get_system_prompt()` — this is the AI's entire personality

### "I want to add a new response template"

- Edit `core/conversation_analyzer.py` → Add to `STALL_RESPONSES`, `FAMILY_TANGENTS`, `REVERSE_EXTRACT_BY_CATEGORY`, etc.

### "I want to change which LLM models are used"

- Edit env vars `OPENROUTER_MODEL`, `OPENROUTER_MODEL_2`, `OPENROUTER_FALLBACK_MODEL`
- Update `MODEL_PRIORITY` dict in `core/llm_client.py` and `ALLOWED_MODELS` set

### "I want to deploy"

- Push to GitHub → Connect to Render → Set env vars → Deploy
- See `render.yaml` and `DEPLOYMENT.md`

---

## 📊 API QUICK REFERENCE

| Method | Endpoint           | Auth               | Purpose                 |
| ------ | ------------------ | ------------------ | ----------------------- |
| `POST` | `/api/honey-pot`   | `x-api-key` header | Main honeypot chat      |
| `GET`  | `/api/honey-pot`   | None               | Redirects to Swagger UI |
| `GET`  | `/health`          | None               | Health check            |
| `GET`  | `/`                | None               | Service info            |
| `GET`  | `/webhook`         | Query params       | WhatsApp verification   |
| `POST` | `/webhook`         | None               | WhatsApp messages       |
| `GET`  | `/whatsapp/status` | None               | WhatsApp config status  |
| `GET`  | `/apidocs/`        | None               | Swagger UI              |
| `GET`  | `/apispec.json`    | None               | OpenAPI spec            |

---

_Last updated: February 2026_
_Project: Operation Iron-Mask — GUVI HCL India AI Impact Buildathon 2026_
