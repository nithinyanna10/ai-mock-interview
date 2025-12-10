# 🚀 Quick Start - Auto Connect Client

## Option 1: Simple Web Client (No Manual Token Copying!)

### Start the client server:
```bash
python client/server.py
```

### Open in browser:
```
http://localhost:8082/auto-connect.html
```

### That's it! Just click "Connect to Interview" and it will:
- ✅ Automatically generate a token
- ✅ Connect to LiveKit
- ✅ Dispatch the agent
- ✅ Start the interview

---

## Option 2: Use LiveKit Playground (Manual)

1. Get token:
```bash
curl -X POST http://localhost:8081/token \
  -H "Content-Type: application/json" \
  -d '{"room": "demo-interview-123"}' | python3 -m json.tool
```

2. Go to: https://agents-playground.livekit.io/
3. Click "Manual"
4. Paste Server, Room, and Token
5. Click "Connect"

---

## Option 3: One-Line Token Generator

Create an alias in your shell:
```bash
alias get-token='curl -s -X POST http://localhost:8081/token -H "Content-Type: application/json" -d "{\"room\": \"demo-interview-$(date +%s)\"}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Room: {d[\"room\"]}\nToken: {d[\"token\"]}\")"'
```

Then just run: `get-token`

---

## Recommended: Use Option 1 (Auto Connect Client)

It's the easiest - no copying/pasting needed!
