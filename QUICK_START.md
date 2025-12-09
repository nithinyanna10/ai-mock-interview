# 🚀 Quick Start - View Interview Transcripts

## See the Full Conversation

### Step 1: Start an Interview
```bash
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d '{"room_id": "my-interview", "candidate_name": "John Doe"}'
```

### Step 2: View the Transcript (Real-Time)

**Option A: Live View (Updates Every 2 Seconds)**
```bash
./view_interview.sh my-interview
```

**Option B: One-Time View**
```bash
./get_transcript.sh my-interview
```

**Option C: JSON API**
```bash
curl http://localhost:8081/interview/my-interview/transcript | python3 -m json.tool
```

## What You'll See

```
🤖 AGENT: Hello! I'm conducting your interview today. To start, 
         could you tell me a bit about yourself...
   ⏰ 2025-12-09T04:52:18.993999

👤 USER:  Hi, I'm John. I'm a software engineer with 5 years 
         of experience...
   ⏰ 2025-12-09T04:52:25.123456

🤖 AGENT: That's great! Can you tell me more about a specific 
         project you worked on?
   ⏰ 2025-12-09T04:52:30.456789
```

## Find Your Room ID

```bash
docker-compose exec redis redis-cli KEYS "interview:*:stage" | sed 's/interview://' | sed 's/:stage//'
```

## Full Documentation

See `VIEW_TRANSCRIPT.md` for complete details.

