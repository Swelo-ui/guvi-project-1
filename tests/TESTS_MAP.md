# Tests Map (Simple Guide)

## Quick Commands

```bash
# All automated tests
python -m pytest tests/

# Coverage report ke saath
python -m pytest tests/ --cov=. --cov-report=term-missing

# Sirf ek file
python -m pytest tests/test_extraction.py

# Integration tests (API server aur env vars chahiye)
set RUN_INTEGRATION_TESTS=true
python -m pytest tests/test_all.py
```

```bash
# Manual scripts (pytest nahi)
python tests/test_local_api.py
python tests/test_remote_api.py
python tests/test_wa_send.py
python tests/test_llm_connection.py
python tests/test_advanced_conversation.py
```

## Tests Map (File wise)

### test_api_robustness.py
- Kya check hota hai: API endpoints galat/adhure payloads par crash na karein.
- Example: empty webhook payload ko handle karna.
- Benefit: production me random payloads se API down nahi hoti.

### test_extraction.py
- Kya check hota hai: regex-based extraction (UPI, phone, IFSC, URLs, keywords) sahi chalti hai.
- Example: archetype messages se expected keywords nikalna.
- Benefit: scam intelligence extraction reliable hota hai.

### test_get_results_script.py
- Kya check hota hai: get_results.py InsForge REST calls sahi endpoints par ja rahi hain.
- Example: intelligence aur conversations fetch ka flow.
- Benefit: reporting data safely export hota hai.

### test_integration_points.py
- Kya check hota hai: GUVI callback payload ka structure aur deduplication.
- Example: duplicate fields ko single value me convert karna.
- Benefit: downstream system clean data receive karta hai.

### test_llm_client.py
- Kya check hota hai: LLM response cleaning, parsing, fallback behavior.
- Example: malformed JSON ko clean karke parseable banana.
- Benefit: LLM failures se pipeline break nahi hoti.

### test_memory.py
- Kya check hota hai: session memory aur conversation context ka behavior.
- Example: memory state ko update/merge.
- Benefit: multi-turn consistency bani rehti hai.

### test_performance_and_errors.py
- Kya check hota hai: analyzer performance basic limits me rahe.
- Example: repeated scam messages ko < 2.5s me analyze karna.
- Benefit: latency spikes control me rehte hain.

### test_schemas.py
- Kya check hota hai: Pydantic models ke defaults aur format mapping.
- Example: ExtractedIntelligence ka default behavior.
- Benefit: API schema stable aur predictable hota hai.

### test_insforge_client.py
- Kya check hota hai: InsForge headers aur auth correctness.
- Example: Authorization header present hona.
- Benefit: DB calls auth issues se fail nahi hoti.

### test_whatsapp_handler_extra.py
- Kya check hota hai: WhatsApp handler ke helper functions.
- Example: webhook verification aur read receipt behavior.
- Benefit: WhatsApp integration stable rehta hai.

### test_analyzer.py
- Kya check hota hai: intent detection (otp, urgency, click_link).
- Example: message “Share OTP immediately” se intent match.
- Benefit: conversation logic sahi branch leta hai.

### test_anti_repetition.py
- Kya check hota hai: conversation analyzer repeat answers avoid kare.
- Example: repeated prompts par response variety.
- Benefit: scammer ko realistic feel hota hai.

### test_all.py
- Kya check hota hai: live API par 12 scam archetypes end-to-end.
- Example: “Digital Arrest” message par scamDetected true.
- Benefit: end-to-end health verify hota hai.

### test_advanced_conversation.py
- Kya check hota hai: multi-turn realistic conversation flow.
- Example: style-switch detection jab scammer tactics change kare.
- Benefit: real-world multi-turn behavior validate hota hai.

### test_local_api.py
- Kya check hota hai: local API par manual consistency.
- Example: repeated calls me persona info consistent hai ya nahi.
- Benefit: local dev me fast sanity check.

### test_remote_api.py
- Kya check hota hai: deployed API ka manual health check.
- Example: Render URL par response JSON verify.
- Benefit: production deployment ka quick smoke check.

### test_wa_send.py
- Kya check hota hai: WhatsApp send API manual test.
- Example: test message send with WhatsApp credentials.
- Benefit: WhatsApp configuration quickly validate hota hai.

### test_llm_connection.py
- Kya check hota hai: OpenRouter LLM connectivity.
- Example: simple prompt par response aata hai ya nahi.
- Benefit: model access issues early detect ho jate hain.
