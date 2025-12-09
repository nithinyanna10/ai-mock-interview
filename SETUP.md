# Setup Guide - AI Mock Interview

## ✅ Current Status

- ✅ Docker containers running (Redis, API)
- ✅ Ollama running with models available
- ✅ LiveKit Agents repo forked to: https://github.com/nithinyanna10/agents

## 🔧 Next Steps

### 1. Create .env File

```bash
cd /Users/nithinyanna/Downloads/ai-mock-interview
cp env.example .env
```

### 2. Configure LiveKit

You need to set up LiveKit. You have two options:

#### Option A: Use LiveKit Cloud (Easiest)
1. Sign up at https://livekit.io/cloud
2. Create a project
3. Get your credentials:
   - LIVEKIT_URL
   - LIVEKIT_API_KEY
   - LIVEKIT_API_SECRET
   - LIVEKIT_WS_URL

#### Option B: Self-Host LiveKit
1. Follow: https://docs.livekit.io/deployment/
2. Set up with Docker or Kubernetes
3. Get your server URL and credentials

### 3. Update .env File

Edit `.env` with your LiveKit credentials:

```env
LIVEKIT_URL=https://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
LIVEKIT_WS_URL=wss://your-livekit-server.com

# Redis (already configured in docker-compose)
REDIS_HOST=redis
REDIS_PORT=6379

# Ollama (using your local instance)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=gpt-oss:120b-cloud
```

**Note**: For Ollama in Docker, use `host.docker.internal:11434` to access your host's Ollama.

### 4. Verify Ollama Model

Check if you have the model:
```bash
ollama list | grep -i "120b\|gpt-oss"
```

If not, pull it:
```bash
ollama pull gpt-oss:120b-cloud
```

### 5. Restart Services

```bash
docker-compose down
docker-compose up -d
```

### 6. Test API

```bash
# Health check
curl http://localhost:8081/health

# Start an interview
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d '{"room_id": "test-room-123", "candidate_name": "Test User"}'

# Check status
curl http://localhost:8081/interview/test-room-123/status
```

### 7. Run the Agent

The agent needs to connect to LiveKit. You can run it:

**Option A: In Docker (recommended)**
```bash
# Make sure .env is set up
docker-compose up agent
```

**Option B: Locally (for development)**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LIVEKIT_URL=...
export LIVEKIT_API_KEY=...
export LIVEKIT_API_SECRET=...
export LIVEKIT_WS_URL=...

# Run agent
python -m livekit.agents.cli dev agents/interview_agent.py
```

### 8. Connect a Client

Use any LiveKit client SDK to connect:
- **JavaScript/TypeScript**: https://github.com/livekit/client-sdk-js
- **React**: https://github.com/livekit/components-js
- **Python**: https://github.com/livekit/python-sdks
- **Playground**: https://github.com/livekit/agent-playground

## 🐛 Troubleshooting

### API Not Starting
- Check logs: `docker-compose logs api`
- Verify Redis is healthy: `docker-compose ps`

### Agent Not Connecting
- Verify LiveKit credentials in `.env`
- Check agent logs: `docker-compose logs agent`
- Test LiveKit connection manually

### Ollama Not Accessible from Docker
- Use `host.docker.internal:11434` instead of `localhost:11434`
- Or run Ollama in Docker too

### Port Conflicts
- API is on port 8081 (changed from 8080)
- Redis is on port 6379

## 📚 Resources

- LiveKit Agents Docs: https://docs.livekit.io/agents/
- Your Forked Repo: https://github.com/nithinyanna10/agents
- LiveKit Cloud: https://livekit.io/cloud
- Ollama: https://ollama.ai

## 🎯 Quick Test

Once everything is set up:

1. Start interview via API:
```bash
curl -X POST http://localhost:8081/interview/start \
  -H "Content-Type: application/json" \
  -d '{"room_id": "demo-123"}'
```

2. Connect a LiveKit client to the room
3. The agent should join and start the interview!

