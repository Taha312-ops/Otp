import sys
import os
import json
from http.server import BaseHTTPRequestHandler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import app, TOKEN
import telegram

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        if not post_data:
            self.send_response(400)
            self.end_headers()
            return
        try:
            update_data = json.loads(post_data.decode('utf-8'))
            update = telegram.Update.de_json(update_data, app.bot)
            app.process_update(update)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook is active.")
