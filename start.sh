#!/bin/bash

# Start script for AI Mock Interview system

set -e

echo "🚀 Starting AI Mock Interview System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env with your LiveKit credentials"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama doesn't seem to be running on localhost:11434"
    echo "   Please start Ollama and pull the model:"
    echo "   ollama pull chatgpt-120b-oss"
fi

# Start with docker-compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo "✅ Services started!"
echo ""
echo "📊 Check status:"
echo "   docker-compose ps"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🌐 API available at: http://localhost:8081"
echo "📚 API docs at: http://localhost:8081/docs"

