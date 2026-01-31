import json
import socket
from typing import Any, Dict, Optional

from .server import PROTOCOL_VERSION


def send(host: str, port: int, payload: Dict[str, Any], token: Optional[str] = None, timeout: float = 5.0) -> Dict[str, Any]:
    """Send a JSON payload and receive a JSON response over the SocketBridge protocol."""
    message = dict(payload)
    if token:
        message.setdefault("auth_token", token)
    message.setdefault("protocol_version", PROTOCOL_VERSION)
    data = json.dumps(message).encode("utf-8")
    frame = len(data).to_bytes(4, "big") + data
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(frame)
        len_bytes = sock.recv(4)
        if not len_bytes:
            raise ConnectionError("No response length received")
        resp_len = int.from_bytes(len_bytes, "big")
        resp_bytes = b""
        while len(resp_bytes) < resp_len:
            chunk = sock.recv(resp_len - len(resp_bytes))
            if not chunk:
                raise ConnectionError("Connection closed before full response")
            resp_bytes += chunk
    return json.loads(resp_bytes.decode("utf-8"))
