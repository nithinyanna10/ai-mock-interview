#!/usr/bin/env python3
"""
Test script to see agent output in real-time
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8081"

async def test_interview():
    """Test the interview flow and show output"""
    
    print("=" * 60)
    print("🧪 Testing AI Mock Interview Agent")
    print("=" * 60)
    print()
    
    # 1. Health check
    print("1️⃣  Checking API health...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        health = response.json()
        print(f"   Status: {health['status']}")
        print(f"   Redis: {'✅ Connected' if health['redis_connected'] else '❌ Disconnected'}")
        print(f"   Active Sessions: {health['active_sessions']}")
    print()
    
    # 2. Start interview
    room_id = f"test-room-{int(datetime.now().timestamp())}"
    print(f"2️⃣  Starting interview session...")
    print(f"   Room ID: {room_id}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/interview/start",
            json={"room_id": room_id, "candidate_name": "Test Candidate"}
        )
        result = response.json()
        print(f"   ✅ Interview started!")
        print(f"   Stage: {result['stage']}")
        print(f"   Status: {result['status']}")
    print()
    
    # 3. Monitor status
    print("3️⃣  Monitoring interview status...")
    print("   (Press Ctrl+C to stop)")
    print()
    
    try:
        async with httpx.AsyncClient() as client:
            for i in range(10):
                response = await client.get(f"{API_BASE}/interview/{room_id}/status")
                status = response.json()
                
                stage = status['stage']
                duration = status['stage_duration']
                status_text = status['status']
                
                print(f"   [{i+1}] Stage: {stage:15} | Duration: {duration:6.1f}s | Status: {status_text}")
                
                if status_text == "completed":
                    print()
                    print("   ✅ Interview completed!")
                    break
                
                await asyncio.sleep(2)
    except KeyboardInterrupt:
        print()
        print("   ⏹️  Monitoring stopped")
    
    print()
    print("=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
    print()
    print("💡 To see the agent in action:")
    print("   1. Connect a LiveKit client to the room")
    print("   2. The agent will automatically join")
    print("   3. You'll hear the agent speak and can interact")
    print()
    print(f"   Room ID: {room_id}")
    print(f"   LiveKit URL: wss://test-hll5bwms.livekit.cloud")

if __name__ == "__main__":
    asyncio.run(test_interview())

