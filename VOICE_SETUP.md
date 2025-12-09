# Voice Interaction Setup Guide

## Problem: Agent Not Responding to Speech

If you're talking but the agent isn't responding, it's because **STT (Speech-to-Text) and TTS (Text-to-Speech) are missing**.

### Current Status

✅ **Working:**
- VAD (Voice Activity Detection) - detects when you speak
- LLM (Ollama) - generates text responses
- Agent registration and dispatch

❌ **Missing (causes no response):**
- STT (Speech-to-Text) - needed to transcribe your speech
- TTS (Text-to-Speech) - needed to speak responses back

## Solution: Add OpenAI API Key

The agent needs STT and TTS to have voice conversations. The easiest solution is to use OpenAI's APIs.

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-...`)

### Step 2: Add to .env File

Add this line to your `.env` file:

```bash
OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Restart Agent

```bash
docker-compose restart agent
```

### Step 4: Test

1. Connect in LiveKit Playground
2. Speak into your microphone
3. Agent should now:
   - ✅ Hear your speech (STT transcribes it)
   - ✅ Respond with voice (TTS speaks back)

## Alternative Solutions

If you don't want to use OpenAI, you can use other providers:

### Option 1: Deepgram (STT)
- Sign up at https://deepgram.com
- Get API key
- Modify code to use Deepgram STT

### Option 2: Azure Speech Services
- Use Azure Cognitive Services
- Requires Azure account

### Option 3: ElevenLabs (TTS)
- Sign up at https://elevenlabs.io
- Get API key
- Modify code to use ElevenLabs TTS

## Cost Considerations

- **OpenAI STT**: ~$0.006 per minute
- **OpenAI TTS**: ~$0.015 per 1000 characters
- **Typical interview (10 min)**: ~$0.10-0.20

## Verification

After adding OPENAI_API_KEY, check logs:

```bash
docker-compose logs agent | grep -E "STT|TTS|OPENAI"
```

You should see:
```
✅ Using OpenAI STT and TTS
```

If you see warnings, the API key might not be set correctly.

## Troubleshooting

### Still not responding?

1. **Check API key is set:**
   ```bash
   docker-compose exec agent env | grep OPENAI_API_KEY
   ```

2. **Check agent logs for errors:**
   ```bash
   docker-compose logs agent --tail 50 | grep -E "Error|error|Exception"
   ```

3. **Verify STT/TTS are initialized:**
   ```bash
   docker-compose logs agent | grep -E "STT|TTS"
   ```

4. **Test OpenAI API key:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

## Current Code Status

The code now:
- ✅ Checks for OPENAI_API_KEY
- ✅ Uses OpenAI STT/TTS if key is present
- ✅ Falls back to VAD-only if key is missing
- ✅ Logs warnings when STT/TTS are unavailable

