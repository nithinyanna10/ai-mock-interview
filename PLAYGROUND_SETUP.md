# 🎮 LiveKit Playground Setup Guide

## Step-by-Step Instructions

### Step 1: Generate a Token

```bash
./generate_token.sh demo-interview-1765256487
```

Copy the token that's displayed.

### Step 2: Open LiveKit Playground

Visit: **https://agents-playground.livekit.io**

### Step 3: Fill in the Form

You'll see a form with these fields. Fill them like this:

**Server URL:**
```
wss://test-hll5bwms.livekit.cloud
```

**Room Name:**
```
demo-interview-1765256487
```
(Or any room ID you created)

**Token:**
```
[paste the token from step 1]
```

**Agent Name (optional):**
```
interview-agent
```
(Leave empty or use any name)

### Step 4: Connect

1. Click the **"Connect"** button
2. Allow microphone access when prompted
3. The agent will automatically join and start the interview!

## What You Should See

After connecting:
- ✅ Connection status: "Connected"
- ✅ You'll see participants (you and the agent)
- ✅ Agent will start speaking
- ✅ You can speak and the agent will respond

## Troubleshooting

**"Invalid token"**
- Make sure you copied the entire token
- Token should start with `eyJ...`
- Regenerate if needed: `./generate_token.sh <room_id>`

**"Connection failed"**
- Check the Server URL is exactly: `wss://test-hll5bwms.livekit.cloud`
- Make sure room ID matches an active interview
- Check your internet connection

**"Agent not joining"**
- Wait a few seconds (agent joins automatically)
- Check agent is running: `docker-compose ps agent`
- Check agent logs: `docker-compose logs agent --tail 20`

**Only seeing "test"**
- This might be a placeholder in the playground
- Make sure you're entering the correct values:
  - Server URL: `wss://test-hll5bwms.livekit.cloud`
  - Room: Your actual room ID (e.g., `demo-interview-1765256487`)
  - Token: The full token from generate_token.sh

## Quick Test

```bash
# 1. Start a new interview
ROOM_ID="test-$(date +%s)"
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d "{\"room_id\": \"$ROOM_ID\"}"

# 2. Generate token
./generate_token.sh $ROOM_ID

# 3. Use that token in playground with room: $ROOM_ID
```

## Alternative: Use the Local Web Client

If playground doesn't work:

```bash
./start_client.sh
```

Then open: http://localhost:8082/index.html

