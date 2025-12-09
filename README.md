# AI Mock Interview - Multi-Agent System

A production-ready AI mock interview system using LiveKit Agents SDK, featuring multi-stage orchestration, time-based fallbacks, and smooth agent transitions.

## 🏗️ Architecture

```
                        ┌────────────────────────────┐
                        │        User Audio          │
                        └──────────────┬─────────────┘
                                       │
                        ┌──────────────▼─────────────┐
                        │    LiveKit Room (RTC)       │
                        └──────────────┬─────────────┘
                                       │
                        ┌──────────────▼─────────────┐
                        │   Interview Agent          │
                        │   (Unified Voice Agent)    │
                        └──────────────┬─────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────┐
        │                              │                          │
┌──────▼───────┐                ┌──────▼─────────┐        ┌──────▼───────────┐
│ Self-Intro    │                │ Experience      │        │ Stage Manager     │
│ Stage Logic   │                │ Stage Logic     │        │ (FSM + Redis)     │
└──────────────┘                └─────────────────┘        └───────────────────┘
```

## ✨ Features

- **Multi-Stage Interview**: Self-introduction and Past Experience stages
- **Smooth Transitions**: Automatic stage switching with time-based fallbacks
- **Ollama Integration**: Uses ChatGPT 120B OSS model via Ollama
- **Redis State Management**: Centralized state store for multi-agent coordination
- **FastAPI REST API**: Enterprise-grade endpoints for session management
- **LiveKit Real-time Audio**: Professional audio pipeline with VAD, ASR, and TTS
- **Docker Support**: Easy deployment with docker-compose

## 📋 Prerequisites

- Python 3.10+
- Docker and Docker Compose
- LiveKit Server (Cloud or Self-hosted)
- Redis (included in docker-compose)
- Ollama with ChatGPT 120B OSS model

## 🚀 Quick Start

### 1. Install Ollama and Pull Model

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the ChatGPT 120B OSS model
ollama pull chatgpt-120b-oss
```

### 2. Set Up Environment Variables

```bash
cd ai-mock-interview
cp .env.example .env
```

Edit `.env` with your LiveKit credentials:

```env
LIVEKIT_URL=https://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
LIVEKIT_WS_URL=wss://your-livekit-server.com
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Redis (port 6379)
- FastAPI server (port 8081, mapped from container port 8080)
- Interview agent (connects to LiveKit)

### 4. Or Run Locally

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (if not using Docker)
redis-server

# Start FastAPI server
python server/run.py

# In another terminal, start the agent
python -m livekit.agents.cli dev agents/interview_agent.py
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Start Interview
```bash
POST /interview/start
Content-Type: application/json

{
  "room_id": "room-123",
  "candidate_name": "John Doe"
}
```

### Get Interview Status
```bash
GET /interview/{room_id}/status
```

Response:
```json
{
  "room_id": "room-123",
  "stage": "self_intro",
  "stage_start_time": "2024-01-01T12:00:00",
  "stage_duration": 15.5,
  "status": "active"
}
```

### Manual Stage Transition
```bash
POST /interview/{room_id}/transition?target_stage=experience
```

### Stop Interview
```bash
POST /interview/{room_id}/stop
```

### Get Transcript
```bash
GET /interview/{room_id}/transcript
```

## 🎯 Interview Stages

### Stage 1: Self-Introduction
- **Duration**: Up to 45 seconds
- **Purpose**: Get to know the candidate
- **Follow-ups**: Maximum 2 questions
- **Transition**: Automatic after follow-ups or timeout

### Stage 2: Past Experience
- **Duration**: Up to 5 minutes
- **Purpose**: Deep dive into projects and technical skills
- **Follow-ups**: Maximum 5 questions
- **Method**: STAR (Situation, Task, Action, Result)
- **Transition**: Automatic after sufficient depth or timeout

## ⚙️ Configuration

Edit `config/settings.yaml` to customize:

- Stage durations and timeouts
- Agent behavior (temperature, max tokens)
- LLM provider settings
- Audio pipeline settings

## 🔧 Development

### Project Structure

```
ai-mock-interview/
├── agents/
│   ├── __init__.py
│   ├── stage_manager.py      # FSM for stage orchestration
│   ├── llm_client.py         # Ollama/LLM integration
│   ├── base_agent.py         # Base agent class
│   └── interview_agent.py    # Main unified agent
├── config/
│   ├── settings.yaml         # Configuration
│   └── prompts/
│       ├── self_intro.txt    # Self-intro prompt
│       └── experience.txt    # Experience prompt
├── server/
│   ├── api.py                # FastAPI endpoints
│   ├── orchestrator.py      # Multi-agent orchestrator
│   └── run.py                # Server entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🐛 Troubleshooting

### Ollama Connection Issues

1. Verify Ollama is running:
   ```bash
   ollama list
   ```

2. Test the model:
   ```bash
   ollama run chatgpt-120b-oss "Hello"
   ```

3. Check the base URL in `config/settings.yaml`

### Redis Connection Issues

1. Verify Redis is running:
   ```bash
   redis-cli ping
   ```

2. Check Redis configuration in `config/settings.yaml`

### LiveKit Connection Issues

1. Verify your LiveKit credentials in `.env`
2. Test LiveKit server connectivity
3. Check agent logs for connection errors

### Stage Transitions Not Working

1. Check Redis is accessible and storing state
2. Verify stage manager is initialized correctly
3. Check agent logs for transition events

## 📊 Monitoring

### Check Agent Status

```bash
# View agent logs
docker-compose logs -f agent

# View API logs
docker-compose logs -f api

# Check Redis state
redis-cli
> KEYS interview:*
> GET interview:room-123:stage
```

### Health Endpoint

```bash
curl http://localhost:8081/health
```

## 🚢 Production Deployment

### Using LiveKit Cloud

1. Sign up at [livekit.io](https://livekit.io)
2. Get your API key and secret
3. Update `.env` with cloud credentials
4. Deploy with docker-compose

### Self-Hosted LiveKit

1. Follow [LiveKit deployment guide](https://docs.livekit.io/deployment/)
2. Set up TLS certificates
3. Update `.env` with your server URL
4. Deploy agents and API

### Scaling

- Run multiple agent instances (LiveKit handles load balancing)
- Use Redis Cluster for high availability
- Deploy API behind a load balancer

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ using LiveKit Agents SDK**

