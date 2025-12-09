# 🚀 Quick Connect Guide

## Method 1: LiveKit Playground (Easiest)

### Step 1: Generate Token

```bash
python3 generate_token.py demo-interview-1765256487
```

This will show you:
- The token to copy
- Exact values to enter in playground

### Step 2: Open Playground

Visit: **https://agents-playground.livekit.io**

### Step 3: Fill the Form

**IMPORTANT:** You'll see a form. Fill it like this:

```
Server URL:  wss://test-hll5bwms.livekit.cloud
Room Name:   demo-interview-1765256487
Token:       [paste token from step 1]
```

**Note:** If you see "test" as a placeholder, replace it with your actual values!

### Step 4: Connect

Click "Connect" and allow microphone access.

## Method 2: Local Web Client (Port 8082)

```bash
./start_client.sh
```

Then open: **http://localhost:8082/index.html**

Enter:
- Room ID: `demo-interview-1765256487`
- URL: `wss://test-hll5bwms.livekit.cloud`
- Token: (from `python3 generate_token.py`)

## What Happens Next

1. ✅ You connect to the room
2. ✅ Agent automatically joins (wait 2-3 seconds)
3. ✅ Agent starts asking questions
4. ✅ You can speak and respond
5. ✅ Watch the transcript: `./monitor_interview.sh demo-interview-1765256487`

## Troubleshooting "test" in Playground

If you see "test" in the playground fields:
- **Server URL field:** Replace with `wss://test-hll5bwms.livekit.cloud`
- **Room Name field:** Replace with your room ID (e.g., `demo-interview-1765256487`)
- **Token field:** Paste the full token from `generate_token.py`

These are just placeholders - you need to replace them with your actual values!

