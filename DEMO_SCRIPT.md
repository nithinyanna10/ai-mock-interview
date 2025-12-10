# 🎬 Loom Video Demo Script - AI Mock Interview

## 📋 PRE-RECORDING SETUP

### 1. Start Services
```bash
cd /Users/nithinyanna/Downloads/ai-mock-interview
docker-compose up -d
# Wait 10-15 seconds for services to start
docker-compose ps  # Verify all services are up
```

### 2. Open These Tabs/Windows:
- **Terminal** - For API calls
- **LiveKit Playground** - https://agents-playground.livekit.io/
- **GitHub Repo** - https://github.com/nithinyanna10/ai-mock-interview
- **Code Editor** (optional) - Show key files

---

## 🎥 RECORDING SCRIPT (5-10 minutes)

### PART 1: Introduction & Architecture (1 min)
**Say:** "I built an AI-powered mock interview system using LiveKit Agents SDK, OpenAI, and FastAPI."

**Show:**
- GitHub repo overview
- Project structure (agents/, server/, config/)
- Key technologies:
  - LiveKit Agents SDK (Python)
  - OpenAI GPT-4o-mini (LLM)
  - OpenAI STT/TTS (Voice)
  - FastAPI (REST API)
  - Redis (State management)
  - Docker (Containerization)

---

### PART 2: API Endpoints Demo (2-3 min)

**Open Terminal and demonstrate:**

#### 2.1 Health Check
```bash
curl http://localhost:8081/health | python3 -m json.tool
```
**Say:** "First, let's check if the API is running. This shows Redis connection and LiveKit API status."

#### 2.2 Generate Token
```bash
curl -X POST http://localhost:8081/token \
  -H "Content-Type: application/json" \
  -d '{"room": "demo-interview-123"}' | python3 -m json.tool
```
**Say:** "This endpoint generates a LiveKit access token and automatically dispatches the agent to the room."

**Show the response:**
- `token` - JWT token for authentication
- `room` - Room name
- `identity` - User identity

#### 2.3 Interview Status
```bash
curl http://localhost:8081/interview/demo-interview-123/status | python3 -m json.tool
```
**Say:** "Check the current interview stage and status."

#### 2.4 Transcript
```bash
curl http://localhost:8081/interview/demo-interview-123/transcript | python3 -m json.tool
```
**Say:** "Get the full conversation transcript stored in Redis."

#### 2.5 Manual Agent Dispatch (Optional)
```bash
curl -X POST http://localhost:8081/dispatch/demo-interview-123
```
**Say:** "Manually dispatch agent if needed."

---

### PART 3: Live Demo - Agent Interaction (3-4 min)

**Switch to LiveKit Playground:**

#### 3.1 Connect to Room
**Say:** "Now let's connect to the interview room using the LiveKit Playground."

**Steps:**
1. Go to: https://agents-playground.livekit.io/
2. Click "Manual" (not LiveKit Cloud)
3. Enter:
   - **Server:** `wss://test-hll5bwms.livekit.cloud`
   - **Room:** (from token response)
   - **Token:** (from token response)
4. Click "Connect"

**Say:** "The agent automatically joins when we connect."

#### 3.2 Show Agent Joining
**Say:** "You can see the agent participant appears in the room. It's using OpenAI STT to hear us, GPT-4o-mini for responses, and OpenAI TTS to speak back."

**Wait 3-5 seconds for greeting:**
**Say:** "The agent automatically greets us and starts the interview."

#### 3.3 Interact with Agent
**Say:** "Let me introduce myself..." (speak naturally)

**Show:**
- Agent transcribing your speech (STT)
- Agent generating responses (LLM)
- Agent speaking back (TTS)
- Stage transitions happening automatically

#### 3.4 Show Transcript
**Switch back to terminal:**
```bash
curl http://localhost:8081/interview/demo-interview-123/transcript | python3 -m json.tool
```
**Say:** "All conversations are stored in Redis and can be retrieved via API."

---

### PART 4: Technical Deep Dive (2-3 min)

**Show code files:**

#### 4.1 Agent Architecture
**File:** `agents/interview_agent.py`
**Say:** "The agent uses LiveKit's AgentSession with OpenAI for STT, LLM, and TTS. It implements a stage manager for interview flow control."

**Highlight:**
- `AgentSession` initialization
- `session.say()` for proactive speech
- Stage management loop

#### 4.2 Stage Manager
**File:** `agents/stage_manager.py`
**Say:** "A finite state machine manages interview stages: START → SELF_INTRO → EXPERIENCE → END, with time-based fallbacks."

#### 4.3 API Server
**File:** `server/api.py`
**Say:** "FastAPI provides REST endpoints for token generation, status checking, and transcript retrieval."

**Highlight:**
- `/token` endpoint
- `/interview/{room_id}/status`
- `/interview/{room_id}/transcript`

#### 4.4 Configuration
**File:** `config/settings.yaml`
**Say:** "YAML configuration for interview stages, timeouts, and LLM settings."

#### 4.5 Docker Setup
**File:** `docker-compose.yml`
**Say:** "Docker Compose orchestrates Redis, API server, and the agent worker."

---

### PART 5: Key Features Summary (1 min)

**Say:** "Key features of this system:"

1. **Multi-stage Interview Flow**
   - Automatic stage transitions
   - Time-based fallbacks
   - State persistence in Redis

2. **Real-time Voice Interaction**
   - OpenAI STT for speech recognition
   - GPT-4o-mini for intelligent responses
   - OpenAI TTS for natural speech

3. **Production-Ready Architecture**
   - RESTful API for integration
   - Containerized deployment
   - State management with Redis
   - Error handling and logging

4. **Scalable Design**
   - Agent auto-dispatch
   - Room-based isolation
   - Transcript storage

---

### PART 6: Closing (30 sec)

**Say:** "This demonstrates a complete AI interview system using modern technologies. The code is open-source on GitHub."

**Show:**
- GitHub repo link
- Key files one more time
- Running system

**End with:** "Thanks for watching! Check out the repo for more details."

---

## 🔗 LINKS TO HAVE READY

1. **LiveKit Playground:** https://agents-playground.livekit.io/
2. **GitHub Repo:** https://github.com/nithinyanna10/ai-mock-interview
3. **API Base URL:** http://localhost:8081
4. **LiveKit Server:** wss://test-hll5bwms.livekit.cloud

---

## 📝 QUICK COMMAND REFERENCE

```bash
# Start system
docker-compose up -d

# Check status
docker-compose ps
curl http://localhost:8081/health

# Generate token
curl -X POST http://localhost:8081/token \
  -H "Content-Type: application/json" \
  -d '{"room": "demo-interview-123"}'

# Check interview status
curl http://localhost:8081/interview/demo-interview-123/status

# Get transcript
curl http://localhost:8081/interview/demo-interview-123/transcript

# View logs
docker-compose logs agent --tail 50
```

---

## ✅ CHECKLIST BEFORE RECORDING

- [ ] Docker containers are running
- [ ] API is accessible (test /health)
- [ ] OpenAI API key is set in .env
- [ ] LiveKit credentials are configured
- [ ] Terminal is ready with commands
- [ ] Browser tabs are open
- [ ] GitHub repo is accessible
- [ ] Code editor is ready (optional)
