# 📱 WhatsApp Integration Setup Guide

Complete step-by-step guide to connect your Operation Iron-Mask Honeypot to WhatsApp.

---

## 🎯 Why WhatsApp Integration?

| Benefit | For Buildathon |
|---------|----------------|
| **Multi-Channel** | Shows judges your system works on real platforms |
| **Real-world Demo** | Live demo capability during presentation |
| **Evaluation Criteria** | Problem statement mentions "WhatsApp/SMS/Email" channels |

---

## ⏱️ Time Required: 30-45 minutes

## 💰 Cost: **FREE** (1,000 conversations/month included)

---

## Step 1: Create Meta Developer Account (5 min)

1. Go to **[developers.facebook.com](https://developers.facebook.com)**
2. Log in with your Facebook account
3. Accept the Developer Terms

---

## Step 2: Create a Meta App (5 min)

1. Click **"My Apps"** → **"Create App"**
2. Select **"Other"** use case → Click **Next**
3. Select **"Business"** app type → Click **Next**
4. Fill in details:
   - App Name: `IronMask Honeypot`
   - Contact Email: Your email
   - Business Account: Create one if needed
5. Click **"Create App"**

---

## Step 3: Add WhatsApp Product (3 min)

1. In your app dashboard, scroll down to **"Add Products"**
2. Find **"WhatsApp"** and click **"Set Up"**
3. You'll see the WhatsApp Getting Started page

---

## Step 4: Get Your Credentials (5 min)

On the WhatsApp → **API Setup** page, note down:

### A. Phone Number ID
```
Located under: "From" → Phone Number ID
Example: 123456789012345
```

### B. Access Token (Temporary)
```
Click "Generate" next to "Temporary access token"
Copy the token (valid for 24 hours)
```

### C. For Production (Permanent Token)
1. Go to **Business Settings** → **System Users**
2. Create a System User
3. Generate a permanent token with `whatsapp_business_messaging` permission

---

## Step 5: Configure Your App (2 min)

Add to your `.env` file:

```env
WHATSAPP_PHONE_ID=your_phone_number_id_here
WHATSAPP_ACCESS_TOKEN=your_access_token_here
WHATSAPP_VERIFY_TOKEN=honeypot_verify_2026
```

---

## Step 6: Deploy to Render (5 min)

1. Your app is already configured! Just deploy:

```bash
git add .
git commit -m "Add WhatsApp integration"
git push
```

2. In **Render Dashboard**, add the new environment variables

3. Redeploy your service

---

## Step 7: Configure Webhook in Meta Console (10 min)

1. In Meta Developer Console → WhatsApp → **Configuration**

2. Click **"Edit"** next to Webhook

3. Enter:
   - **Callback URL**: `https://your-app.onrender.com/webhook`
   - **Verify Token**: `honeypot_verify_2026` (same as in .env)

4. Click **"Verify and Save"**

5. Subscribe to webhook fields:
   - ✅ `messages` (required)
   - ✅ `message_template_status_update` (optional)

---

## Step 8: Test Your Integration (5 min)

### Option A: Use Test Number
1. In API Setup → **"To"** field, add your personal WhatsApp number
2. Click **"Send"** to verify you can receive messages
3. Reply to the message - your honeypot will process it!

### Option B: Use cURL
```bash
curl -X POST https://your-app.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "919876543210",
            "text": {"body": "Your account is blocked. Send OTP now!"},
            "id": "test123",
            "timestamp": "1234567890"
          }],
          "contacts": [{"profile": {"name": "Test Scammer"}}]
        }
      }]
    }]
  }'
```

---

## 📊 How GUVI Gets the Results

When scam intel is extracted, your system automatically:

1. **Sends GUVI Callback** with this JSON:
```json
{
  "sessionId": "whatsapp_919876543210",
  "scamDetected": true,
  "totalMessagesExchanged": 5,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123"],
    "upiIds": ["scammer@upi"],
    "phoneNumbers": ["+919876543210"],
    "phishingLinks": [],
    "suspiciousKeywords": ["blocked", "OTP"]
  },
  "agentNotes": "WhatsApp | reverse_extraction | Digital arrest scam"
}
```

2. **Saves to Supabase** for your records

3. **Logs to Console** for monitoring

---

## 🔧 Troubleshooting

### Webhook Not Verifying?
- Check your app is deployed and running
- Verify the token matches exactly
- Check Render logs for errors

### Messages Not Receiving?
- Ensure you subscribed to `messages` webhook field
- Check the phone number is added in API Setup

### Token Expired?
- Generate new temporary token (24h validity)
- Or create permanent token via System User

---

## 🎓 For Grand Finals Presentation

**Demo Flow:**
1. Show judges your WhatsApp test number
2. Have them send a "scam" message
3. Show the real-time response from honeypot
4. Show the GUVI callback log in Render console
5. Show Supabase data being stored

**Key Points to Mention:**
- "Multi-channel capability - works on WhatsApp, SMS, API"
- "Real-time intelligence extraction"
- "Automatic reporting to law enforcement APIs"
- "1000 free conversations/month - cost effective"

---

## ✅ Quick Checklist

- [ ] Meta Developer account created
- [ ] Meta App created
- [ ] WhatsApp product added
- [ ] Phone Number ID copied
- [ ] Access Token generated
- [ ] `.env` updated with WhatsApp vars
- [ ] Code deployed to Render
- [ ] Render env vars updated
- [ ] Webhook URL configured in Meta
- [ ] Webhook verified successfully
- [ ] Test message sent and received
- [ ] Response verified in WhatsApp

---

## 📞 Support

If stuck, check:
- Meta Developer Docs: https://developers.facebook.com/docs/whatsapp
- Render Logs: Check for errors during deployment
- Your health endpoint: `https://your-app.onrender.com/health`
