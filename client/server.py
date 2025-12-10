#!/usr/bin/env python3
"""
Simple HTTP server to serve the auto-connect client
Run: python client/server.py
Then open: http://localhost:8082/auto-connect.html
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8083  # Changed from 8082 to avoid conflicts
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Client server running at http://localhost:{PORT}/")
        print(f"📄 Open: http://localhost:{PORT}/auto-connect.html")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Server stopped")
