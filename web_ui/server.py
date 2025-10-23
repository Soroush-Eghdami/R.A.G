#!/usr/bin/env python3
"""
Simple HTTP server for the Smart RAG Web UI
Serves the HTML, CSS, and JavaScript files locally
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files with proper MIME types"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for API requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def start_server(port=8080, open_browser=True):
    """Start the local web server"""
    
    # Change to the web_ui directory
    web_ui_dir = Path(__file__).parent
    os.chdir(web_ui_dir)
    
    # Create the server
    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Smart RAG Web UI Server")
        print(f"📁 Serving from: {web_ui_dir}")
        print(f"🌐 Local URL: http://localhost:{port}")
        print(f"🔗 Public URL: http://127.0.0.1:{port}")
        print("\n📋 Instructions:")
        print("1. Make sure your RAG API is running: python -m app.api")
        print("2. Open your browser to the URL above")
        print("3. Start asking legal questions!")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Open browser automatically
        if open_browser:
            try:
                webbrowser.open(f'http://localhost:{port}')
                print("🌐 Browser opened automatically")
            except:
                print("⚠️  Could not open browser automatically")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")
            sys.exit(0)

def main():
    """Main function to start the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start Smart RAG Web UI Server')
    parser.add_argument('--port', '-p', type=int, default=8080, 
                       help='Port to run the server on (default: 8080)')
    parser.add_argument('--no-browser', action='store_true', 
                       help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    # Check if port is available
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', args.port))
    sock.close()
    
    if result == 0:
        print(f"❌ Port {args.port} is already in use!")
        print(f"💡 Try a different port: python server.py --port 8081")
        sys.exit(1)
    
    start_server(port=args.port, open_browser=not args.no_browser)

if __name__ == "__main__":
    main()
