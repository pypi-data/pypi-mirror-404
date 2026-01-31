import os
import socket
import threading
import json
import logging
from typing import Dict, Any, Callable, Optional

PROTOCOL_VERSION = "1"
AUTH_TOKEN_ENV = "SOCKETBRIDGE_TOKEN"
ALLOWLIST_ENV = "SOCKETBRIDGE_ALLOWLIST"
MAX_BYTES_ENV = "SOCKETBRIDGE_MAX_BYTES"


def _parse_allowlist(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


class SocketServer:
    """Length-prefixed JSON socket server with optional auth/allowlist."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7002,
        handler: Optional[Callable[[Dict[str, Any]], None]] = None,
        auth_token: Optional[str] = None,
        allowlist: Optional[list[str]] = None,
        max_bytes: Optional[int] = None,
        verbose: bool = False,
    ):
        self.host = host
        self.port = port
        self.handler = handler
        self.auth_token = auth_token if auth_token is not None else os.getenv(AUTH_TOKEN_ENV, "")
        self.allowlist = allowlist if allowlist is not None else _parse_allowlist(os.getenv(ALLOWLIST_ENV, ""))
        env_max = os.getenv(MAX_BYTES_ENV)
        self.max_bytes = max_bytes if max_bytes is not None else int(env_max) if env_max else 1024 * 1024
        self.verbose = bool(verbose)
        self.logger = logging.getLogger("socketbridge")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_thread: Optional[threading.Thread] = None
        self._is_running = False

    def _log(self, msg: str, level: str = "info") -> None:
        if self.verbose:
            print(msg)
            return
        try:
            getattr(self.logger, level, self.logger.info)(msg)
        except Exception:
            pass

    def _handle_client(self, conn, addr):
        self._log(f"[SocketBridge] Accepted connection from {addr}")
        try:
            while self._is_running:
                len_bytes = conn.recv(4)
                if not len_bytes:
                    break
                msg_len = int.from_bytes(len_bytes, byteorder="big")
                if msg_len > self.max_bytes:
                    # drain payload
                    remaining = msg_len
                    while remaining > 0:
                        chunk = conn.recv(min(4096, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                    response = {"status": "error", "message": "payload too large", "protocol_version": PROTOCOL_VERSION}
                    resp_json = json.dumps(response).encode("utf-8")
                    conn.sendall(len(resp_json).to_bytes(4, "big") + resp_json)
                    continue

                msg_bytes = b""
                while len(msg_bytes) < msg_len:
                    chunk = conn.recv(msg_len - len(msg_bytes))
                    if not chunk:
                        raise ConnectionError("Client closed connection unexpectedly.")
                    msg_bytes += chunk

                try:
                    message: Dict[str, Any] = json.loads(msg_bytes.decode("utf-8"))
                    self._log(f"[SocketBridge] Received message: {message}")
                    if self.allowlist and addr[0] not in self.allowlist:
                        response = {"status": "error", "message": "unauthorized host", "protocol_version": PROTOCOL_VERSION, "request_id": message.get("request_id")}
                        resp_json = json.dumps(response).encode("utf-8")
                        conn.sendall(len(resp_json).to_bytes(4, "big") + resp_json)
                        continue
                    if self.auth_token and message.get("auth_token") != self.auth_token:
                        response = {"status": "error", "message": "unauthorized", "protocol_version": PROTOCOL_VERSION, "request_id": message.get("request_id")}
                        resp_json = json.dumps(response).encode("utf-8")
                        conn.sendall(len(resp_json).to_bytes(4, "big") + resp_json)
                        continue
                    if message.get("protocol_version") not in (None, PROTOCOL_VERSION):
                        response = {"status": "error", "message": "protocol mismatch", "protocol_version": PROTOCOL_VERSION, "request_id": message.get("request_id")}
                        resp_json = json.dumps(response).encode("utf-8")
                        conn.sendall(len(resp_json).to_bytes(4, "big") + resp_json)
                        continue
                    if self.handler:
                        self.handler(message)
                    response = {"status": "ok", "message": "received", "protocol_version": PROTOCOL_VERSION}
                except json.JSONDecodeError:
                    response = {"status": "error", "message": "invalid json", "protocol_version": PROTOCOL_VERSION}
                except Exception as e:
                    response = {"status": "error", "message": f"handler error: {e}", "protocol_version": PROTOCOL_VERSION}

                resp_json = json.dumps(response).encode("utf-8")
                conn.sendall(len(resp_json).to_bytes(4, "big") + resp_json)
        finally:
            self._log(f"[SocketBridge] Closing connection from {addr}")
            conn.close()

    def _run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self._log(f"[SocketBridge] Listening on {self.host}:{self.port}")
        self._is_running = True
        while self._is_running:
            try:
                conn, addr = self.sock.accept()
                client_handler = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                client_handler.start()
            except socket.error as e:
                if self._is_running:
                    self._log(f"[SocketBridge] Socket error: {e}", level="warning")
                break
        self._log("[SocketBridge] Server loop stopped.")

    def start(self):
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=self._run, daemon=True)
            self.server_thread.start()
            self._log("[SocketBridge] Server started.")

    def stop(self):
        if self._is_running:
            self._is_running = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.port))
            except Exception:
                pass
            self.sock.close()
            if self.server_thread:
                self.server_thread.join(timeout=2)
            self._log("[SocketBridge] Server stopped.")
