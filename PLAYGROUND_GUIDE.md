# LiveKit Playground - Agent Connection Guide

## Understanding the "Agent name: None" Field

The **"Agent name: None"** field in LiveKit Playground is for **REQUESTING** an agent, not displaying the connected one.

### Your Agent Status
- ✅ Agent is registered: `interview-agent`
- ✅ Agent name is set correctly: `lk.agent_name: interview-agent` (visible in Attributes)
- ✅ Agent auto-dispatches when you connect

## How to Connect

### Option 1: Leave Agent Name as None (Recommended)
1. **Server URL**: `wss://test-hll5bwms.livekit.cloud`
2. **Room Name**: `demo-interview-1765256487`
3. **Token**: Get fresh token:
   ```bash
   curl -X POST http://localhost:8081/token \
     -H "Content-Type: application/json" \
     -d '{"room": "demo-interview-1765256487"}' | python3 -m json.tool
   ```
4. **Agent name**: Leave as `None` (agent will auto-join)
5. Click **"Connect"**

The agent will automatically join because:
- It's registered with `agent_name: "interview-agent"`
- The `/token` endpoint dispatches the agent automatically
- LiveKit will match the agent when you connect

### Option 2: Set Agent Name Explicitly
If the field is editable:
1. Type: `interview-agent`
2. Then connect as above

### Option 3: Manual Dispatch (Before Connecting)
```bash
# Dispatch agent first
curl -X POST http://localhost:8081/dispatch/demo-interview-1765256487

# Then connect in Playground (leave agent name as None)
```

## What You Should See

After connecting:
- ✅ **Status**: Connected
- ✅ **Agent Identity**: `agent-AJ_...` (auto-generated)
- ✅ **Attributes**: `lk.agent_name: interview-agent`
- ✅ **Agent State**: `listening` or `speaking`

## Troubleshooting

### If agent doesn't join:
1. Check agent logs:
   ```bash
   docker-compose logs agent --tail 50
   ```
2. Look for: `"agent_name": "interview-agent"` in registration logs
3. Look for: `🎯 Job received!` when you connect

### If you see errors:
- Check that agent is running: `docker-compose ps agent`
- Check agent registration: Look for `registered worker` in logs
- Verify agent_name matches: Should be `"interview-agent"`

## Quick Test

```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8081/token \
  -H "Content-Type: application/json" \
  -d '{"room": "demo-interview-1765256487"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# 2. Dispatch agent
curl -X POST http://localhost:8081/dispatch/demo-interview-1765256487

# 3. Use token in Playground
echo "Token: $TOKEN"
```

Then paste the token into Playground and connect!

