#!/bin/bash

# Start the web client on port 8082

PORT=8082

echo "🌐 Starting Interview Client Web Server..."
echo "   Port: $PORT"
echo ""

cd "$(dirname "$0")/client"

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port $PORT is already in use. Trying port 8083..."
    PORT=8083
fi

echo "✅ Server starting on http://localhost:$PORT"
echo ""
echo "📋 Open in your browser:"
echo "   http://localhost:$PORT/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m http.server $PORT 2>/dev/null || python -m http.server $PORT

