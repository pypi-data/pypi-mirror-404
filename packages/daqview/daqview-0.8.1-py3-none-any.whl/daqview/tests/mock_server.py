# pylint: disable=missing-docstring

import time
import json
import struct
import socket
import socketserver
import threading
import numpy as np

from ..models.server import Server


SAMPLE_STATUS = {
    "test_name": "2018-02-12 001",
    "config": {
        "path": "/bla/bla/config.yaml",
        "revision": "1234567890abcdef"
    },
    "assets": {
        "path": "/bla/bla/assets.yaml",
        "revision": "acdef1234567890"
    },
    "connected": False,
    "recording": False,
    "daus": {
        "Box101": {
            "uri": "udp://192.168.2.103:1735",
            "status": "disconnected"
        }
    }
}

SAMPLE_CONFIG = {
    "channels": [
        {
            "id": "p_inj_ox",
            "name": "Oxidant Injector Feed",
            "colour": "g",
            "units": "bar(g)",
            "redline": 2.0,
            "format": "%8.2f",
            "groups": ["p", "inj", "ox"]
        }, {
            "id": "p_inj_fl",
            "name": "Fuel Injector Feed",
            "colour": "r",
            "units": "bar(g)",
            "redline": 2.0,
            "format": "%8.2f",
            "groups": ["p", "inj", "fl"]
        }, {
            "id": "t_inj_ox",
            "name": "Oxidant Injector Feed",
            "colour": "g",
            "units": "degC",
            "format": "%8.1f",
            "groups": ["t", "inj", "ox"]
        }, {
            "id": "t_inj_fl",
            "name": "Fuel Injector Feed",
            "colour": "r",
            "units": "degC",
            "format": "%8.1f",
            "groups": ["t", "inj", "fl"]
        }, {
            "id": "pc1",
            "name": "Chamber",
            "colour": "c",
            "format": "%8.2f",
            "redline": 3.0,
            "yellowline": 2.5,
            "units": "bar(g)",
            "groups": ["p"]
        }, {
            "id": "thrust",
            "name": "Thrust",
            "colour": "w",
            "format": "%8.2f",
            "units": "N",
            "groups": []
        }
    ],
    "groups": [
        {
            "id": "p",
            "name": "Pressures"
        }, {
            "id": "t",
            "name": "Temperatures"
        }, {
            "id": "inj",
            "name": "Injector"
        }, {
            "id": "fl",
            "name": "Fuel"
        }, {
            "id": "ox",
            "name": "Oxidant"
        }
    ]
}


def msg_generator(channels):
    n = len([x for x in channels.split(",") if x.strip() != ""])
    t = 0.0
    ch = np.zeros(n)
    mn = np.zeros(n)
    mx = np.zeros(n)
    st = np.zeros(n, dtype=np.uint8)
    while True:
        t += 0.1
        ch += (2 * np.random.randn(n) - 1.0) / 100.0 - ch/1000.0
        mn = ch - np.random.standard_exponential(n)
        mx = ch + np.random.standard_exponential(n)
        yield (1, [[n, t, ch.tolist(), mn.tolist(), mx.tolist(), st.tolist()]])


def get_port():
    """
    Opens a socket to find an unused port number then closes the socket and
    returns the port.
    This has an obvious race condition (if another program ends up being given
    that port number in the time between us closing our socket and us using
    the port), but there doesn't seem to be a better way to get Flask to
    bind to a random port which we can then retrieve.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class RequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.setblocking(False)
        nch = 0
        ts = 0.0
        while True:
            # Handle incoming data
            try:
                data = self.request.recv(4)
            except BlockingIOError:
                pass
            except (BrokenPipeError, ConnectionResetError):
                return
            else:
                if len(data) == 0:
                    return
                tag, length = struct.unpack("<HH", data)
                if tag == Server._TAG_CONFIG_REQUEST:
                    payload = json.dumps(SAMPLE_CONFIG).encode("utf-8")
                    msg = struct.pack(
                        "<HH", Server._TAG_CONFIG_RESPONSE, len(payload))
                    msg += payload
                    try:
                        self.request.sendall(msg)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                elif tag == Server._TAG_STATUS_REQUEST:
                    payload = json.dumps(SAMPLE_STATUS).encode("utf-8")
                    msg = struct.pack(
                        "<HH", Server._TAG_STATUS_RESPONSE, len(payload))
                    msg += payload
                    try:
                        self.request.sendall(msg)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                elif tag == Server._TAG_SUBSCRIBE_REQUEST:
                    if length == 0:
                        nch = 0
                    else:
                        self.request.setblocking(True)
                        data = self.request.recv(length)
                        self.request.setblocking(False)
                        nch = len(data.decode().split(","))
                elif tag == Server._TAG_SUBSCRIBE_IDXS_REQUEST:
                    if length == 0:
                        nch = 0
                    else:
                        self.request.setblocking(True)
                        data = self.request.recv(length)
                        self.request.setblocking(False)
                        nch = length // 2

            # Send outgoing data
            n = 2 + 8 + nch*8
            msg = struct.pack("<HHHd", Server._TAG_DATA_INDICATION, n, nch, ts)
            chdata = np.random.random(nch)
            msg += struct.pack("<{}d".format(nch), *chdata)
            try:
                self.request.sendall(msg)
            except (BrokenPipeError, ConnectionResetError):
                return

            # Wait before next piece of data
            ts += 0.05
            time.sleep(0.05)


def run():
    server = socketserver.ThreadingTCPServer(("localhost", 0), RequestHandler)
    ip, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return "{}:{}".format(ip, port)
