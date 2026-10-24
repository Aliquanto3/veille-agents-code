"""Récepteur OTLP/HTTP minimal (bibliothèque standard) : écrit chaque corps reçu en JSONL.

Usage : uv run --no-project python otlp_recepteur.py <port> <fichier.jsonl>
Chaque ligne : {"path": "/v1/metrics", "body": {...}}. Arrêt : Ctrl+C ou kill.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT, OUT = int(sys.argv[1]), sys.argv[2]


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            body = json.loads(body)
        except ValueError:
            body = {"raw": body.decode("utf-8", "replace")}
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"path": self.path, "body": body}) + "\n")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", PORT), H).serve_forever()
