#!/bin/bash

# Comprehensive interview monitor - shows everything happening

if [ -z "$1" ]; then
    echo "Usage: ./monitor_interview.sh <room_id>"
    echo ""
    echo "Or run without args to see available rooms:"
    docker-compose exec redis redis-cli KEYS "interview:*:stage" 2>/dev/null | sed 's/interview://' | sed 's/:stage//' | head -10
    exit 1
fi

# Clean up room ID (remove any "Room ID: " prefix)
ROOM_ID=$(echo "$1" | sed 's/^Room ID: //' | sed 's/^room_id: //' | xargs)

echo "============================================================"
echo "🎬 MOCK INTERVIEW MONITOR - Room: $ROOM_ID"
echo "============================================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "============================================================"
    echo "🎬 MOCK INTERVIEW MONITOR - Room: $ROOM_ID"
    echo "   Last updated: $(date '+%H:%M:%S')"
    echo "============================================================"
    echo ""
    
    # 1. Interview Status
    echo "📊 INTERVIEW STATUS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    STATUS=$(curl -s http://localhost:8081/interview/$ROOM_ID/status 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$STATUS" ]; then
        STAGE=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stage', 'unknown'))" 2>/dev/null)
        DURATION=$(echo "$STATUS" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin).get('stage_duration', 0):.1f}\")" 2>/dev/null)
        STATUS_TEXT=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
        START_TIME=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stage_start_time', 'N/A'))" 2>/dev/null)
        
        echo "   Stage:        $STAGE"
        echo "   Duration:     ${DURATION}s"
        echo "   Status:       $STATUS_TEXT"
        echo "   Started:      $START_TIME"
    else
        echo "   ❌ Interview not found or API error"
    fi
    echo ""
    
    # 2. Conversation Transcript
    echo "💬 CONVERSATION TRANSCRIPT:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    TRANSCRIPT=$(curl -s http://localhost:8081/interview/$ROOM_ID/transcript 2>/dev/null)
    MESSAGE_COUNT=$(echo "$TRANSCRIPT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message_count', 0))" 2>/dev/null)
    
    if [ "$MESSAGE_COUNT" = "0" ] || [ -z "$MESSAGE_COUNT" ]; then
        echo "   ⏳ Waiting for conversation to start..."
        echo ""
        echo "   💡 The agent will join when a LiveKit client connects"
        echo "   💡 Connect a client to room: $ROOM_ID"
        echo "   💡 LiveKit URL: wss://test-hll5bwms.livekit.cloud"
    else
        echo "   📝 Total Messages: $MESSAGE_COUNT"
        echo ""
        echo "$TRANSCRIPT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    messages = data.get('messages', [])
    for i, msg in enumerate(messages[-10:], 1):  # Show last 10 messages
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', '')
        
        # Truncate long messages
        if len(content) > 80:
            content = content[:77] + '...'
        
        if role == 'assistant':
            print(f'   🤖 AGENT: {content}')
        elif role == 'user':
            print(f'   👤 USER:  {content}')
        else:
            print(f'   ❓ {role.upper()}: {content}')
        
        if timestamp:
            time_only = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp
            print(f'      ⏰ {time_only}')
        print()
except Exception as e:
    print(f'   Error: {e}')
" 2>/dev/null
    fi
    echo ""
    
    # 3. Agent Status
    echo "🤖 AGENT STATUS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    AGENT_STATUS=$(docker-compose ps agent 2>/dev/null | tail -1)
    if echo "$AGENT_STATUS" | grep -q "Up"; then
        echo "   ✅ Agent container: Running"
    else
        echo "   ❌ Agent container: Not running"
    fi
    
    # Check if agent is registered
    AGENT_LOGS=$(docker-compose logs agent --tail 3 2>/dev/null | grep -i "registered\|worker" | tail -1)
    if [ ! -z "$AGENT_LOGS" ]; then
        echo "   ✅ Agent: Registered with LiveKit"
    else
        echo "   ⏳ Agent: Checking..."
    fi
    echo ""
    
    # 4. System Health
    echo "💚 SYSTEM HEALTH:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    HEALTH=$(curl -s http://localhost:8081/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        REDIS_STATUS=$(echo "$HEALTH" | python3 -c "import sys, json; print('✅' if json.load(sys.stdin).get('redis_connected') else '❌')" 2>/dev/null)
        ACTIVE_SESSIONS=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('active_sessions', 0))" 2>/dev/null)
        echo "   Redis:          $REDIS_STATUS"
        echo "   Active Sessions: $ACTIVE_SESSIONS"
        echo "   API:            ✅ Running"
    else
        echo "   ❌ API not responding"
    fi
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Refreshing every 2 seconds... (Ctrl+C to stop)"
    echo ""
    echo "💡 To connect a client:"
    echo "   Room ID: $ROOM_ID"
    echo "   URL: wss://test-hll5bwms.livekit.cloud"
    
    sleep 2
done

