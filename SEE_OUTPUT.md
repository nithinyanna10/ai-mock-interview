# 📺 See Agent Output (Not Logs)

## Quick Commands to See Output

### 1. Test Interview Flow
```bash
./test_agent.sh
```
Shows:
- ✅ API health status
- ✅ Interview session creation
- ✅ Real-time stage monitoring (updates every 2 seconds)
- ✅ Stage transitions and duration

### 2. Watch Agent Status (Live Dashboard)
```bash
./watch_agent.sh
```
Shows a live updating dashboard with:
- API health
- Active sessions
- Container status
- Refreshes every 2 seconds

### 3. Check Specific Room Status
```bash
# Replace ROOM_ID with your room ID
curl http://localhost:8081/interview/ROOM_ID/status | python3 -m json.tool
```

### 4. See Agent Capabilities
```bash
docker-compose exec agent python -c "
from livekit import agents
print('🤖 Agent Status')
print('✅ SDK Version:', agents.__version__)
print('✅ Ready to handle interviews')
"
```

## Example Output

When you run `./test_agent.sh`, you'll see:

```
============================================================
🧪 Testing AI Mock Interview Agent
============================================================

1️⃣  Checking API health...
{
    "status": "healthy",
    "redis_connected": true,
    "active_sessions": 2
}

2️⃣  Starting interview session...
   Room ID: test-room-1765255970

{
    "room_id": "test-room-1765255970",
    "stage": "self_intro",
    "message": "Interview started",
    "status": "active"
}

3️⃣  Monitoring interview status...
   [ 1] Stage: self_intro      | Duration:    0.0s | Status: active
   [ 2] Stage: self_intro      | Duration:    2.1s | Status: active
   [ 3] Stage: self_intro      | Duration:    4.2s | Status: active
   ...
```

## To See Agent Actually Speaking

The agent will speak when a LiveKit client connects to the room. To test:

1. **Start an interview:**
   ```bash
   curl -X POST http://localhost:8081/interview/start \
     -H "Content-Type: application/json" \
     -d '{"room_id": "my-room", "candidate_name": "Test"}'
   ```

2. **Connect a LiveKit client** (browser, mobile app, etc.) to:
   - Room: `my-room`
   - URL: `wss://test-hll5bwms.livekit.cloud`
   - Token: Generate via LiveKit dashboard or API

3. **Agent will automatically join** and start speaking!

## All Available Commands

```bash
# Health check
curl http://localhost:8081/health

# Start interview
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d '{"room_id": "test-123"}'

# Check status
curl http://localhost:8081/interview/test-123/status

# Manual stage transition
curl -X POST http://localhost:8081/interview/test-123/transition?target_stage=experience

# Stop interview
curl -X POST http://localhost:8081/interview/test-123/stop
```

