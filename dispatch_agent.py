#!/usr/bin/env python3
"""
Manually dispatch agent to a room
"""

import sys
import requests
import os

def dispatch_agent(room_name):
    """Dispatch agent to a room using LiveKit API"""
    
    livekit_url = os.getenv("LIVEKIT_URL", "https://test-hll5bwms.livekit.cloud")
    api_key = os.getenv("LIVEKIT_API_KEY", "API4xeZWnJCKVyg")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN")
    
    # Create room if needed and dispatch agent
    url = f"{livekit_url}/twirp/livekit.RoomService/CreateRoom"
    
    headers = {
        "Authorization": f"Bearer {api_key}:{api_secret}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": room_name,
        "empty_timeout": 300,
        "max_participants": 10
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"✅ Room created/verified: {room_name}")
        else:
            print(f"⚠️  Room creation response: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Room creation: {e}")
    
    # Note: Agent should auto-join when client connects
    # If not, check agent logs for dispatch errors
    print(f"\n💡 Agent should auto-join when client connects to room: {room_name}")
    print("   If agent doesn't join, check:")
    print("   1. Agent is registered: docker-compose logs agent | grep registered")
    print("   2. Client is connected to the correct room")
    print("   3. Agent worker is running: docker-compose ps agent")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dispatch_agent.py <room_id>")
        sys.exit(1)
    
    dispatch_agent(sys.argv[1])

