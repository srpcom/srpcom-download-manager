import http.server
import json
import socketserver
import threading
import urllib.parse
from typing import Callable, Optional

PORT = 9876

class BrowserRequestHandler(http.server.BaseHTTPRequestHandler):
    on_download_received: Optional[Callable] = None
    on_video_download_received: Optional[Callable] = None

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _get_data(self):
        """Extract parameters from either JSON POST body or GET query parameters."""
        parsed = urllib.parse.urlparse(self.path)
        data = {}
        
        # 1. Query parameters
        if parsed.query:
            qs = urllib.parse.parse_qs(parsed.query)
            for k, v in qs.items():
                if v:
                    data[k] = v[0]

        # 2. POST body (JSON or Form)
        content_length = self.headers.get("Content-Length")
        if content_length and content_length.isdigit():
            length = int(content_length)
            body = self.rfile.read(length).decode("utf-8", errors="ignore")
            if body:
                try:
                    json_data = json.loads(body)
                    if isinstance(json_data, dict):
                        data.update(json_data)
                except Exception:
                    # Maybe form encoded
                    form_data = urllib.parse.parse_qs(body)
                    for k, v in form_data.items():
                        if v:
                            data[k] = v[0]

        return parsed.path, data

    def _handle_request(self):
        path, data = self._get_data()
        
        url = data.get("url", "").strip()
        filename = data.get("filename", "").strip()
        quality = data.get("quality", "best").strip()
        title = data.get("title", "").strip()
        cookies = data.get("cookies", "").strip()
        referer = data.get("referer", "").strip()
        user_agent = data.get("user_agent", "").strip()

        if path == "/add":
            if url and BrowserRequestHandler.on_download_received:
                try:
                    BrowserRequestHandler.on_download_received(
                        url, filename, cookies=cookies, referer=referer, user_agent=user_agent
                    )
                except TypeError:
                    BrowserRequestHandler.on_download_received(url, filename)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"Download added to SRPCOM"}')

        elif path == "/download_video":
            if url and BrowserRequestHandler.on_video_download_received:
                try:
                    BrowserRequestHandler.on_video_download_received(
                        url, quality, title, cookies=cookies, referer=referer, user_agent=user_agent
                    )
                except TypeError:
                    BrowserRequestHandler.on_video_download_received(url, quality, title)
            elif url and BrowserRequestHandler.on_download_received:
                try:
                    BrowserRequestHandler.on_download_received(
                        url, title, cookies=cookies, referer=referer, user_agent=user_agent
                    )
                except TypeError:
                    BrowserRequestHandler.on_download_received(url, title)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"Video download added to SRPCOM"}')

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence access logs in terminal
        pass

def start_browser_listener(
    on_download_received: Callable,
    on_video_download_received: Optional[Callable] = None
):
    BrowserRequestHandler.on_download_received = on_download_received
    BrowserRequestHandler.on_video_download_received = on_video_download_received
    try:
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer(("127.0.0.1", PORT), BrowserRequestHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"Browser integration listener started on port {PORT}")
        return server
    except Exception as e:
        print(f"Could not start browser listener on port {PORT}: {e}")
        return None
