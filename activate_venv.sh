#!/bin/bash

# Activate the virtual environment

cd "$(dirname "$0")"
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "You can now run:"
echo "  - python3 generate_token.py <room_id>"
echo "  - python3 dispatch_agent.py <room_id>"
echo "  - python3 test_agent.py"
echo ""
echo "To deactivate: deactivate"

