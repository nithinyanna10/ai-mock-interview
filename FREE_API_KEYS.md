# Free API Keys for STT/TTS

## 🎯 Quick Recommendation: OpenAI (Easiest)

**Why:** Already integrated in your code, just need a new API key.

### Steps:
1. **Create new OpenAI account:**
   - Go to: https://platform.openai.com/signup
   - Use a different email (or phone number)
   - Verify your account

2. **Get API key:**
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-...`)

3. **Update .env file:**
   ```bash
   OPENAI_API_KEY=sk-your-new-key-here
   ```

4. **Restart agent:**
   ```bash
   docker-compose restart agent
   ```

**Free Credits:** $5 free credits (enough for ~50-100 minutes of STT/TTS)

---

## 🆓 Alternative Options

### Option 2: Deepgram (Most Generous)

**Free Tier:** 12,000 minutes/month (200 hours!)

**Steps:**
1. Sign up: https://console.deepgram.com/signup
2. Get API key from dashboard
3. **Note:** Requires code changes to integrate Deepgram STT

**Pros:** Very generous free tier
**Cons:** Need to modify code to use Deepgram instead of OpenAI

---

### Option 3: Google Cloud Speech

**Free Tier:** 
- 60 minutes STT/month
- 1 million characters TTS/month

**Steps:**
1. Sign up: https://cloud.google.com (free trial)
2. Enable Speech-to-Text API
3. Enable Text-to-Speech API
4. Create API key
5. **Note:** Requires code changes to integrate Google APIs

**Pros:** Good free tier, reliable
**Cons:** Need to modify code, requires credit card (but won't charge)

---

### Option 4: ElevenLabs (TTS Only)

**Free Tier:** 10,000 characters/month

**Steps:**
1. Sign up: https://elevenlabs.io
2. Get API key
3. **Note:** Only TTS, need STT from elsewhere

**Pros:** High-quality voices
**Cons:** Only TTS, need separate STT service

---

## 💡 Quick Fix Right Now

**Fastest solution:** Create a new OpenAI account and get $5 free credits.

1. Go to: https://platform.openai.com/signup
2. Create account (use different email/phone)
3. Get API key: https://platform.openai.com/api-keys
4. Update `.env` file with new key
5. Restart: `docker-compose restart agent`

**That's it!** Your code already supports OpenAI, so no code changes needed.

---

## 📊 Cost Comparison

| Service | Free Tier | Best For |
|---------|-----------|----------|
| OpenAI | $5 credits | Quick setup, already integrated |
| Deepgram | 12,000 min/month | High volume usage |
| Google Cloud | 60 min + 1M chars | Balanced free tier |
| ElevenLabs | 10K chars/month | TTS only |

---

## ⚠️ Important Notes

- **OpenAI:** New accounts get $5 free, but you need a valid payment method (won't charge unless you exceed free credits)
- **Google Cloud:** Requires credit card but won't charge on free tier
- **Deepgram:** No credit card needed for free tier
- **All services:** Have usage limits on free tiers

---

## 🚀 After Getting API Key

1. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-new-key-here
   ```

2. Restart agent:
   ```bash
   docker-compose restart agent
   ```

3. Test in Playground - agent should now hear and speak!

