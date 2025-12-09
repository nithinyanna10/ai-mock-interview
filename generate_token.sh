#!/bin/bash

# Generate LiveKit access token for interview room

if [ -z "$1" ]; then
    echo "Usage: ./generate_token.sh <room_id> [identity]"
    echo ""
    echo "Example:"
    echo "  ./generate_token.sh demo-interview-1765256487"
    echo "  ./generate_token.sh demo-interview-1765256487 user-123"
    exit 1
fi

ROOM=$1
IDENTITY=${2:-user-$(date +%s)}

echo "🔑 Generating LiveKit token..."
echo "   Room: $ROOM"
echo "   Identity: $IDENTITY"
echo ""

# Try Python method first (more reliable)
if command -v python3 &> /dev/null; then
    python3 "$(dirname "$0")/generate_token.py" "$ROOM" "$IDENTITY"
else
    # Fallback to livekit-cli
    if ! command -v livekit-cli &> /dev/null; then
        echo "❌ Need Python3 or livekit-cli"
        echo "   Install livekit-cli: npm install -g livekit-cli"
        echo "   Or use: python3 generate_token.py $ROOM"
        exit 1
    fi
    
    livekit-cli token create \
      --api-key API4xeZWnJCKVyg \
      --api-secret yheogye7QX27H6sD83tajnckfRW5c6h9eQvpePTAjeaN \
      --room "$ROOM" \
      --identity "$IDENTITY" \
      --join
fi

