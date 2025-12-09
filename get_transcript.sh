#!/bin/bash

# Get and display interview transcript (one-time)

if [ -z "$1" ]; then
    echo "Usage: ./get_transcript.sh <room_id>"
    echo ""
    echo "Available rooms:"
    docker-compose exec redis redis-cli KEYS "interview:*:stage" 2>/dev/null | sed 's/interview://' | sed 's/:stage//' | head -10
    exit 1
fi

ROOM_ID=$1

echo "============================================================"
echo "📝 Interview Transcript - Room: $ROOM_ID"
echo "============================================================"
echo ""

TRANSCRIPT=$(curl -s http://localhost:8081/interview/$ROOM_ID/transcript)

MESSAGE_COUNT=$(echo "$TRANSCRIPT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message_count', 0))" 2>/dev/null)

if [ "$MESSAGE_COUNT" = "0" ] || [ -z "$MESSAGE_COUNT" ]; then
    echo "❌ No transcript found for room: $ROOM_ID"
    echo ""
    echo "💡 Make sure the interview session exists and has messages."
else
    echo "📊 Total Messages: $MESSAGE_COUNT"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Display messages in a readable format
    echo "$TRANSCRIPT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
messages = data.get('messages', [])

for i, msg in enumerate(messages, 1):
    role = msg.get('role', 'unknown')
    content = msg.get('content', '')
    timestamp = msg.get('timestamp', '')
    
    if role == 'assistant':
        print(f'🤖 AGENT [{i}]: {content}')
    elif role == 'user':
        print(f'👤 USER [{i}]:  {content}')
    else:
        print(f'❓ {role.upper()} [{i}]: {content}')
    
    if timestamp:
        print(f'   ⏰ {timestamp}')
    print()
" 2>/dev/null || echo "$TRANSCRIPT" | python3 -m json.tool
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

