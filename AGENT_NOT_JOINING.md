# 🔧 Agent Not Joining Room - Troubleshooting

## Current Issue

You're connected to the room in the playground, but seeing:
- "Waiting for agent video track..."
- "Waiting for agent audio track..."
- Loading spinner

This means the agent hasn't joined the room yet.

## Why This Happens

LiveKit Agents work on a **job dispatch system**. When you connect:
1. ✅ Your client connects to the room
2. ⏳ LiveKit should dispatch the agent to join
3. ❌ Agent isn't being dispatched or is failing to join

## Fix Applied

✅ **Redis connection fixed** - Agent was crashing due to Redis config error
✅ **Agent restarted** - Should now work properly

## What to Do Now

### Step 1: Disconnect and Reconnect

In the playground:
1. **Disconnect** from the room
2. **Wait 2-3 seconds**
3. **Reconnect** with the same token

The agent should now join automatically!

### Step 2: Check Agent Logs

```bash
docker-compose logs agent --tail 20 --follow
```

You should see:
- "Starting interview agent for room: ..."
- "Agent connected and running"
- "Participant connected"

### Step 3: Verify Agent is Registered

```bash
docker-compose logs agent | grep "registered worker"
```

Should show: `registered worker` with worker ID

## If Still Not Working

### Check Agent Status
```bash
docker-compose ps agent
docker-compose logs agent --tail 50
```

### Manual Test
```bash
# Generate fresh token
source venv/bin/activate
python3 generate_token.py demo-interview-1765256487

# Use in playground and reconnect
```

### Verify Room Exists
```bash
curl http://localhost:8081/interview/demo-interview-1765256487/status
```

## Expected Behavior

Once working, you should see:
1. ✅ Client connects
2. ✅ Agent joins (2-3 seconds later)
3. ✅ Agent video/audio tracks appear
4. ✅ Agent starts speaking
5. ✅ Conversation begins

## Quick Fix Command

```bash
# Restart everything
docker-compose restart agent api
sleep 5

# Generate fresh token
source venv/bin/activate
python3 generate_token.py demo-interview-1765256487

# Reconnect in playground
```

