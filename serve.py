#!/usr/bin/env python3
"""Run AeroWatch locally with live traffic and METARs.

Browsers won't let a web page call the OpenSky or aviationweather.gov APIs
directly (no CORS headers), so this serves the app on localhost and makes those
requests from Python instead. Standard library only.

    python3 serve.py          # http://localhost:8000
    python3 serve.py 8080     # pick a different port
"""

import http.server
import os
import sys
import urllib.error
import urllib.request

OPENSKY = "https://opensky-network.org/api/"
AWC = "https://aviationweather.gov/api/data/"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Only forward the two endpoints the app uses, so this isn't an open proxy.
        if self.path.startswith("/opensky/states/all"):
            self.forward(OPENSKY + self.path[len("/opensky/"):])
        elif self.path.startswith("/awc/metar?"):
            self.forward(AWC + self.path[len("/awc/"):])
        else:
            super().do_GET()

    def forward(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "AeroWatch local server"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status, body = resp.status, resp.read()
                ctype = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as err:
            status, body = err.code, err.read()
            ctype = err.headers.get("Content-Type", "text/plain")
        except Exception as err:  # network down, DNS, timeout...
            status, body, ctype = 502, str(err).encode(), "text/plain"

        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_request(self, code="-", size="-"):
        # keep the terminal quiet unless something goes wrong
        if str(code).startswith(("4", "5")):
            super().log_request(code, size)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AeroWatch is running at http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
