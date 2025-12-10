#!/usr/bin/env python3
"""
Generate LiveKit access token for interview room
"""

import sys
import time
import jwt

def generate_token(room_id, identity=None):
    api_key = "API4xeZWnJCKVyg"
    api_secret = "yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN"
    
    if not identity:
        identity = f"user-{int(time.time())}"
    
    token = jwt.encode({
        "iss": api_key,
        "sub": identity,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour
        "video": {
            "room": room_id,
            "roomJoin": True
        },
        "audio": {
            "room": room_id,
            "roomJoin": True
        }
    }, api_secret, algorithm="HS256")
    
    return token

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_token.py <room_id> [identity]")
        print("\nExample:")
        print("  python3 generate_token.py demo-interview-1765256487")
        sys.exit(1)
    
    room_id = sys.argv[1]
    identity = sys.argv[2] if len(sys.argv) > 2 else None
    
    token = generate_token(room_id, identity)
    
    print("=" * 60)
    print("🔑 LiveKit Access Token Generated")
    print("=" * 60)
    print()
    print("Room ID:", room_id)
    print("Identity:", identity or f"user-{int(time.time())}")
    print()
    print("Token:")
    print(token)
    print()
    print("=" * 60)
    print("📋 Use in LiveKit Playground:")
    print("=" * 60)
    print()
    print("1. Visit: https://agents-playground.livekit.io")
    print()
    print("2. Enter these values:")
    print("   Server URL: wss://test-hll5bwms.livekit.cloud")
    print(f"   Room Name: {room_id}")
    print(f"   Token: {token}")
    print()
    print("3. Click 'Connect'")
    print()
    print("=" * 60)

