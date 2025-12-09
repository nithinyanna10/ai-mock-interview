#!/bin/bash

# Watch agent output in real-time (not logs, but actual status)

echo "🔍 Watching Agent Status (Real-time)"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "============================================================"
    echo "🤖 Agent Status - $(date '+%H:%M:%S')"
    echo "============================================================"
    echo ""
    
    # Health
    echo "📊 API Health:"
    curl -s http://localhost:8081/health | python3 -m json.tool 2>/dev/null || echo "❌ API not responding"
    echo ""
    
    # Active sessions
    echo "📋 Active Interview Sessions:"
    echo "(Check individual room status with: curl http://localhost:8081/interview/{room_id}/status)"
    echo ""
    
    # Agent container status
    echo "🐳 Agent Container:"
    docker-compose ps agent 2>/dev/null | tail -1
    echo ""
    
    echo "============================================================"
    echo "Refreshing every 2 seconds... (Ctrl+C to stop)"
    
    sleep 2
done

