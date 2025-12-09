# 📝 View Interview Transcript

## How to See the Full Conversation

### 1. View Transcript in Real-Time (Live Updates)

```bash
./view_interview.sh <room_id>
```

This shows:
- 🤖 **Agent questions** - Everything the agent asks
- 👤 **User responses** - Everything the user says
- ⏰ **Timestamps** - When each message was sent
- 🔄 **Auto-refresh** - Updates every 2 seconds

**Example:**
```bash
./view_interview.sh test-room-123
```

### 2. Get Transcript Once (Static View)

```bash
./get_transcript.sh <room_id>
```

Shows the full conversation history formatted nicely.

**Example:**
```bash
./get_transcript.sh test-room-123
```

### 3. Via API (JSON Format)

```bash
curl http://localhost:8081/interview/<room_id>/transcript | python3 -m json.tool
```

Returns JSON with all messages:
```json
{
  "room_id": "test-room-123",
  "message_count": 10,
  "messages": [
    {
      "role": "assistant",
      "content": "Hello! I'm conducting your interview today...",
      "timestamp": "2025-12-09T04:52:18.993999"
    },
    {
      "role": "user",
      "content": "Hi, I'm John and I'm a software engineer...",
      "timestamp": "2025-12-09T04:52:25.123456"
    }
  ]
}
```

## Find Available Rooms

```bash
docker-compose exec redis redis-cli KEYS "interview:*:stage" | sed 's/interview://' | sed 's/:stage//'
```

## Example Output

When you run `./view_interview.sh test-room-123`, you'll see:

```
============================================================
📝 Interview Transcript - Room: test-room-123
   Last updated: 04:55:30
============================================================

📊 Total Messages: 6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 AGENT: Hello! I'm conducting your interview today. To start, 
         could you tell me a bit about yourself - your background, 
         what you're passionate about, and what brings you here today?
   ⏰ 2025-12-09T04:52:18.993999

👤 USER:  Hi, I'm John. I'm a software engineer with 5 years of 
         experience in full-stack development. I'm passionate about 
         building scalable applications.
   ⏰ 2025-12-09T04:52:25.123456

🤖 AGENT: That's great! Can you tell me more about a specific 
         project you worked on?
   ⏰ 2025-12-09T04:52:30.456789

👤 USER:  Sure! I worked on a microservices architecture for an 
         e-commerce platform...
   ⏰ 2025-12-09T04:52:35.789012

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Refreshing every 2 seconds... (Ctrl+C to stop)
```

## What Gets Captured

✅ **Agent Questions** - All prompts and follow-ups
✅ **User Responses** - All transcribed speech
✅ **Timestamps** - Exact time of each message
✅ **Stage Transitions** - When the interview moves to next stage

## Notes

- Transcripts are stored in Redis
- They persist for 24 hours
- Real-time updates as conversation happens
- Works for any active interview session

