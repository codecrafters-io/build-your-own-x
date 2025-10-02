#!/usr/bin/env python3
"""
Simple HTTP server for Build Your Own X Explorer
"""
import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[Server] {self.address_string()} - {format % args}")

def run_server():
    os.chdir('/workspace')
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print("🚀 Build Your Own X Explorer Server")
        print("=" * 60)
        print(f"📡 Server running at: http://localhost:{PORT}")
        print(f"📂 Serving files from: {os.getcwd()}")
        print("\n🎯 Open your browser and navigate to the URL above")
        print("\n⌨️  Keyboard Shortcuts:")
        print("   • Ctrl+K  - Focus search")
        print("   • Ctrl+R  - Random tutorial (Surprise Me!)")
        print("   • Escape  - Close modal")
        print("\n💡 Press Ctrl+C to stop the server")
        print("=" * 60)
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()
