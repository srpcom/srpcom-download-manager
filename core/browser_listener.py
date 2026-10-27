import http.server
import socketserver
import threading
import urllib.parse
from typing import Callable, Optional

PORT = 9876

class BrowserRequestHandler(http.server.BaseHTTPRequestHandler):
    on_download_received: Callable[[str, str], None] = None
    on_video_download_received: Optional[Callable[[str, str, str], None]] = None

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_OPTIONS(self):
        # Handle CORS
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _handle_request(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/add":
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            filename = params.get("filename", [""])[0]

            if url and BrowserRequestHandler.on_download_received:
                BrowserRequestHandler.on_download_received(url, filename)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"Download added to SRPCOM"}')
        elif parsed.path == "/download_video":
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            quality = params.get("quality", ["best"])[0]
            title = params.get("title", [""])[0]

            if url and BrowserRequestHandler.on_video_download_received:
                BrowserRequestHandler.on_video_download_received(url, quality, title)
            elif url and BrowserRequestHandler.on_download_received:
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
        # Silence standard HTTP access logging in terminal
        pass

def start_browser_listener(
    on_download_received: Callable[[str, str], None],
    on_video_download_received: Optional[Callable[[str, str, str], None]] = None
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
