# 🎬 Start & Monitor Mock Interview

## Quick Start

### 1. Start a New Interview

```bash
# This creates a new interview session
ROOM_ID="interview-$(date +%s)"
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d "{\"room_id\": \"$ROOM_ID\", \"candidate_name\": \"Test Candidate\"}"

echo "Room ID: $ROOM_ID"
```

### 2. Monitor Everything (Real-Time)

```bash
./monitor_interview.sh <room_id>
```

This shows:
- 📊 **Interview Status** - Current stage, duration, status
- 💬 **Full Transcript** - Every question and answer (live updates)
- 🤖 **Agent Status** - Is agent running and connected
- 💚 **System Health** - Redis, API, active sessions

### 3. View Just the Transcript

```bash
# Live view (updates every 2 seconds)
./view_interview.sh <room_id>

# One-time view
./get_transcript.sh <room_id>
```

## What You'll See

The monitor shows:

```
🎬 MOCK INTERVIEW MONITOR - Room: interview-1234567890
   Last updated: 05:00:30

📊 INTERVIEW STATUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Stage:        self_intro
   Duration:     15.3s
   Status:       active
   Started:      2025-12-09T05:00:15.123456

💬 CONVERSATION TRANSCRIPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📝 Total Messages: 4

   🤖 AGENT: Hello! I'm conducting your interview today. To start...
      ⏰ 05:00:15

   👤 USER:  Hi, I'm John. I'm a software engineer...
      ⏰ 05:00:20

   🤖 AGENT: That's great! Can you tell me more about...
      ⏰ 05:00:25

🤖 AGENT STATUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅ Agent container: Running
   ✅ Agent: Registered with LiveKit

💚 SYSTEM HEALTH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Redis:          ✅
   Active Sessions: 1
   API:            ✅ Running
```

## To Actually Run the Interview

1. **Start the interview** (creates the session)
2. **Connect a LiveKit client** to the room:
   - Room ID: (from step 1)
   - URL: `wss://test-hll5bwms.livekit.cloud`
   - Generate token via LiveKit dashboard or API
3. **Watch the monitor** - You'll see:
   - Agent joining
   - Agent asking questions
   - User responses (when they speak)
   - Stage transitions

## All-in-One Command

```bash
# Start interview and monitor
ROOM_ID="demo-$(date +%s)" && \
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d "{\"room_id\": \"$ROOM_ID\"}" && \
echo "" && \
echo "🎬 Monitoring interview: $ROOM_ID" && \
./monitor_interview.sh $ROOM_ID
```

