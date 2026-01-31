import json
import socket
import time
from socketbridge.server import SocketServer, PROTOCOL_VERSION
from socketbridge.client import send


def test_roundtrip_with_auth():
    received = []

    def handler(msg):
        received.append(msg)

    server = SocketServer("127.0.0.1", 0, handler=handler, auth_token="token123")
    server.start()
    host, port = server.sock.getsockname()
    resp = send(host, port, {"type": "ping"}, token="token123")
    server.stop()

    assert resp["status"] == "ok"
    assert received and received[0]["type"] == "ping"
    assert received[0]["auth_token"] == "token123"
    assert received[0]["protocol_version"] == PROTOCOL_VERSION


def test_reject_wrong_token():
    server = SocketServer("127.0.0.1", 0, auth_token="secret")
    server.start()
    host, port = server.sock.getsockname()
    resp = send(host, port, {"type": "ping"}, token="wrong")
    server.stop()
    assert resp["status"] == "error"
    assert "unauthorized" in resp["message"]


def test_max_bytes_rejected():
    server = SocketServer("127.0.0.1", 0, max_bytes=8)
    server.start()
    host, port = server.sock.getsockname()
    big_payload = {"data": "x" * 100}
    message = json.dumps(big_payload).encode("utf-8")
    frame = len(message).to_bytes(4, "big") + message
    with socket.create_connection((host, port), timeout=5.0) as sock:
        sock.sendall(frame)
        resp_len = int.from_bytes(sock.recv(4), "big")
        resp = json.loads(sock.recv(resp_len).decode("utf-8"))
    server.stop()
    assert resp["status"] == "error"
    assert "payload too large" in resp["message"]
