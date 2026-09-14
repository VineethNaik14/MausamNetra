"""Tiny local HTTP endpoint for genuine citizen submissions.

This uses only the Python standard library. A real browser/mobile frontend can POST
JSON to /reports. Uploaded media should be stored by the backend and referenced by URL.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from ingestion.citizen_reports.ingestion import ingest_citizen_report

class CitizenHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/reports":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length))
            report = ingest_citizen_report(payload)
            body = json.dumps(report, indent=2, ensure_ascii=False).encode()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode()
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def run(host="127.0.0.1", port=8081):
    print(f"Citizen report API listening on http://{host}:{port}/reports")
    HTTPServer((host, port), CitizenHandler).serve_forever()

if __name__ == "__main__":
    run()
