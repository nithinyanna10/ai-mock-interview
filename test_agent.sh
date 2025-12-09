#!/bin/bash

# Test script to see agent output in real-time

echo "============================================================"
echo "🧪 Testing AI Mock Interview Agent"
echo "============================================================"
echo ""

# 1. Health check
echo "1️⃣  Checking API health..."
curl -s http://localhost:8081/health | python3 -m json.tool
echo ""

# 2. Start interview
ROOM_ID="test-room-$(date +%s)"
echo "2️⃣  Starting interview session..."
echo "   Room ID: $ROOM_ID"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d "{\"room_id\": \"$ROOM_ID\", \"candidate_name\": \"Test Candidate\"}")

echo "$RESPONSE" | python3 -m json.tool
echo ""

# 3. Monitor status
echo "3️⃣  Monitoring interview status..."
echo "   (Press Ctrl+C to stop)"
echo ""

for i in {1..10}; do
    STATUS=$(curl -s http://localhost:8081/interview/$ROOM_ID/status)
    STAGE=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['stage'])" 2>/dev/null)
    DURATION=$(echo "$STATUS" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin)['stage_duration']:.1f}\")" 2>/dev/null)
    STATUS_TEXT=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    
    printf "   [%2d] Stage: %-15s | Duration: %6ss | Status: %s\n" "$i" "$STAGE" "$DURATION" "$STATUS_TEXT"
    
    if [ "$STATUS_TEXT" = "completed" ]; then
        echo ""
        echo "   ✅ Interview completed!"
        break
    fi
    
    sleep 2
done

echo ""
echo "============================================================"
echo "✅ Test complete!"
echo "============================================================"
echo ""
echo "💡 To see the agent in action:"
echo "   1. Connect a LiveKit client to the room"
echo "   2. The agent will automatically join"
echo "   3. You'll hear the agent speak and can interact"
echo ""
echo "   Room ID: $ROOM_ID"
echo "   LiveKit URL: wss://test-hll5bwms.livekit.cloud"
echo ""

