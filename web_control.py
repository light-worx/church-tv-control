#!/usr/bin/env python3

from pathlib import Path
from urllib.parse import urlparse
import http.server
import json
import socketserver
import threading

from remote import SSHRemoteBackend
from openlp import OpenLPBackend


HOST = "127.0.0.1"
PORT = 8765

WEB_DIR = Path(__file__).parent / "web"

tv_backend = SSHRemoteBackend()
openlp_backend = OpenLPBackend()

preview_lock = threading.Lock()


class ChurchTVRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP server for the Church TV Control web interface."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(WEB_DIR),
            **kwargs,
        )

    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/status":
            self.handle_status()
            return

        if path == "/api/preview":
            self.handle_preview()
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/start":
            self.handle_start()
            return

        if self.path == "/api/shutdown":
            self.handle_shutdown()
            return

        if self.path == "/api/fix-openlp":
            self.handle_fix_openlp()
            return

        self.send_json(
            {
                "success": False,
                "message": "Unknown API endpoint.",
            },
            status=404,
        )

    def handle_status(self):
        """
        Return status.

        If the TV computer is online and OpenLP is reachable but the
        Church TV display is not running, automatically restart the
        display. This keeps the technical recovery out of the UI.
        """

        try:
            status = tv_backend.get_status()

            if (
                status.tv_online
                and status.openlp_reachable
                and not status.church_tv_running
            ):
                try:
                    tv_backend.restart_display()
                    status = tv_backend.get_status()
                except Exception as exc:
                    status.message = (
                        "Church TV display needs attention: "
                        + str(exc)
                    )

            self.send_json(
                {
                    "success": True,
                    "tv_online": status.tv_online,
                    "church_tv_running": status.church_tv_running,
                    "openlp_reachable": status.openlp_reachable,
                    "message": status.message,
                }
            )

        except Exception as exc:
            self.send_json(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=500,
            )

    def handle_preview(self):
        """Return a current PNG screenshot of the TV PC."""

        if not preview_lock.acquire(blocking=False):
            self.send_json(
                {
                    "success": False,
                    "message": "Preview capture already in progress.",
                },
                status=429,
            )
            return

        try:
            data = tv_backend.get_screenshot()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "image/png",
            )
            self.send_header(
                "Content-Length",
                str(len(data)),
            )
            self.send_header(
                "Cache-Control",
                "no-store, no-cache, must-revalidate",
            )
            self.send_header(
                "Pragma",
                "no-cache",
            )
            self.end_headers()

            self.wfile.write(data)

        except Exception as exc:
            self.send_json(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=503,
            )

        finally:
            preview_lock.release()

    def handle_start(self):
        try:
            message = tv_backend.start()

            self.send_json(
                {
                    "success": True,
                    "message": message,
                }
            )

        except Exception as exc:
            self.send_json(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=500,
            )

    def handle_shutdown(self):
        try:
            message = tv_backend.shutdown()

            self.send_json(
                {
                    "success": True,
                    "message": (
                        message
                        or "TV computer is shutting down."
                    ),
                }
            )

        except Exception as exc:
            self.send_json(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=500,
            )

    def handle_fix_openlp(self):
        try:
            message = openlp_backend.fix_service_problem()

            self.send_json(
                {
                    "success": True,
                    "message": message,
                }
            )

        except Exception as exc:
            self.send_json(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=500,
            )


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def main():
    if not WEB_DIR.exists():
        raise RuntimeError(
            f"Web directory does not exist: {WEB_DIR}"
        )

    server = ReusableTCPServer(
        (HOST, PORT),
        ChurchTVRequestHandler,
    )

    print(
        "Church TV Control web interface running at:"
    )
    print(f"http://{HOST}:{PORT}")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping web server...")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
