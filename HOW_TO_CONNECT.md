# 🔌 How to Connect a Client to the Interview

## Option 1: Simple Web Client (Easiest)

### Step 1: Generate a Token

You need a LiveKit access token. Use one of these methods:

**Method A: LiveKit CLI (Recommended)**
```bash
# Install LiveKit CLI
npm install -g livekit-cli

# Generate token
livekit-cli token create \
  --api-key API4xeZWnJCKVyg \
  --api-secret yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN \
  --room demo-interview-1765256487 \
  --identity user-123 \
  --join
```

**Method B: Use LiveKit Dashboard**
1. Go to https://cloud.livekit.io
2. Login with your credentials
3. Go to "Tokens" section
4. Generate a token for your room

### Step 2: Open the Web Client

```bash
# Open the HTML file in your browser
open client/index.html
# Or
python3 -m http.server 3000
# Then visit http://localhost:3000/client/index.html
```

### Step 3: Connect

1. Enter your Room ID (e.g., `demo-interview-1765256487`)
2. Enter the LiveKit URL: `wss://test-hll5bwms.livekit.cloud`
3. Paste the token you generated
4. Click "Connect to Interview"
5. Allow microphone access

## Option 2: LiveKit Playground (Easiest for Testing)

1. Go to: https://agents-playground.livekit.io
2. Enter your room details:
   - URL: `wss://test-hll5bwms.livekit.cloud`
   - Room: `demo-interview-1765256487`
   - Token: (generate via dashboard or CLI)
3. Click "Connect"
4. The agent will join automatically!

## Option 3: Python Client (For Testing)

```python
import asyncio
from livekit import rtc

async def main():
    # Connect to room
    room = rtc.Room()
    await room.connect(
        "wss://test-hll5bwms.livekit.cloud",
        "YOUR_TOKEN_HERE"
    )
    
    print("Connected! Waiting for agent...")
    
    # Wait for agent to join
    @room.on("participant_connected")
    def on_participant(participant):
        print(f"Participant joined: {participant.identity}")
    
    # Keep running
    await asyncio.sleep(3600)

asyncio.run(main())
```

## Option 4: JavaScript/Node.js Client

```javascript
const { Room, createLocalAudioTrack } = require('livekit-client');

async function connect() {
    const room = new Room();
    
    await room.connect(
        'wss://test-hll5bwms.livekit.cloud',
        'YOUR_TOKEN_HERE'
    );
    
    // Publish audio
    const track = await createLocalAudioTrack();
    await room.localParticipant.publishTrack(track);
    
    console.log('Connected! Agent will join shortly...');
}

connect();
```

## Quick Token Generation Script

Create a simple token server:

```bash
# Save this as generate_token.sh
#!/bin/bash
ROOM=$1
IDENTITY=${2:-user-$(date +%s)}

livekit-cli token create \
  --api-key API4xeZWnJCKVyg \
  --api-secret yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN \
  --room $ROOM \
  --identity $IDENTITY \
  --join
```

Usage:
```bash
chmod +x generate_token.sh
./generate_token.sh demo-interview-1765256487
```

## What Happens When You Connect

1. ✅ Your client connects to the LiveKit room
2. ✅ The agent automatically detects the connection
3. ✅ Agent joins the room
4. ✅ Agent starts asking questions
5. ✅ Your responses are transcribed
6. ✅ Full transcript appears in the monitor

## Troubleshooting

**"Token invalid"**
- Make sure token is generated with correct API key/secret
- Token must have `join` permission
- Token must be for the correct room

**"Connection failed"**
- Check LiveKit URL is correct
- Verify network connectivity
- Check if room exists

**"Agent not joining"**
- Make sure agent container is running: `docker-compose ps agent`
- Check agent logs: `docker-compose logs agent`
- Verify agent is registered with LiveKit

## Recommended: Use LiveKit Playground

The easiest way is to use the official LiveKit Playground:
1. Visit: https://agents-playground.livekit.io
2. Enter your room details
3. Connect and start the interview!

