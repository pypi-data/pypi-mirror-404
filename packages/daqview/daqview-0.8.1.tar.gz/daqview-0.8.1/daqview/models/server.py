import json
import struct
import logging
from contextlib import contextmanager

import numpy as np
from PySide6.QtCore import (QObject, QTimer, QAbstractTableModel, QModelIndex,
                            Qt, QEventLoop, Signal)
from PySide6.QtWidgets import QErrorMessage, QApplication
from PySide6.QtNetwork import QTcpSocket

from .live_dataset import LiveDataset


logger = logging.getLogger(__name__)


class ChannelsTableModel(QAbstractTableModel):
    """
    A TableModel that shows all the channels on the server.
    """
    def __init__(self, channels):
        super().__init__()
        self._data = [[c['id'], c['name'], c.get('colour'), c.get('units'),
                       ", ".join(c.get('groups', []))] for c in channels]

    def rowCount(self, _parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, _parent=QModelIndex()):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        else:
            return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ["ID", "Name", "Colour", "Units", "Groups"][section]
        else:
            return section + 1


class Server(QObject):
    """
    Handles connection to server.

    Receives configuration and status updates and streamed data.

    Signals:
    connected: emitted when connection state changes
    status_update: emitted when status updates are received
    config_update: emitted when config updates are received
    time_update: emitted when a new timestmap is received
    """
    connected = Signal(bool)
    status_update = Signal()
    config_update = Signal()
    time_update = Signal(float)

    _TAG_CONFIG_REQUEST = 1
    _TAG_CONFIG_RESPONSE = 2
    _TAG_STATUS_REQUEST = 3
    _TAG_STATUS_RESPONSE = 4
    _TAG_SUBSCRIBE_REQUEST = 5
    _TAG_DATA_INDICATION = 6
    _TAG_SUBSCRIBE_IDXS_REQUEST = 7

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.host = None
        self.last_host = self.app.prefs.get_last_server()
        self.last_time = None
        self.status = None
        self.config = None
        self._connected = False
        self._connecting = False
        self.paused = False
        self.stream_channels = []
        self.channels_Table = None
        self.live_data = LiveDataset([], [])
        self.socket = QTcpSocket()
        self.socket.readyRead.connect(self._socket_ready_read)
        self.socket.errorOccurred.connect(self._socket_error)
        self.pending = None
        self.data_queue = []
        self.unpack_hh = struct.Struct("<HH").unpack
        self.unpack_hd = struct.Struct("<Hd").unpack

    def connect_to_host(self, host):
        """
        Connect to a new host, which should be a 'hostname:port' string.
        """
        logger.info("Connecting to server %s", host)
        self.host = host
        self.last_host = host
        self.app.prefs.set_last_server(host)

        self._connecting = True
        if not self._connect_socket():
            error = QErrorMessage()
            error.setModal(True)
            error.showMessage(
                "Error connecting to server. Check host and try again.\n"
                " Error {}: {}"
                .format(self.socket.error(), self.socket.errorString()))
            error.exec_()
            self._connecting = False
            return
        self._connecting = False

        self._connected = True
        self.connected.emit(True)

    def disconnect_from_host(self):
        """Disconnect from a connected host."""
        logger.info("Disconnecting from server")
        self.socket.abort()
        self.config = None
        self.channels_table = None
        self.host = None
        self.status = None
        self.live_data.update_channels([], [])
        self._connected = False
        self.connected.emit(False)

    def reconnect(self):
        """Reconnect to the current host."""
        logger.info("Reconnecting to server")
        host = self.host
        self.disconnect_from_host()
        self.connect_to_host(host)

    def is_connected(self):
        """Return connection status."""
        return self._connected

    def set_live_channels(self, channels):
        """
        Change which channels are being live streamed.

        channels: a list of channel_id strings.
        """
        logger.info("Requesting channels from server: %s", ",".join(channels))
        self.stream_channels = channels
        if self._connected:
            channel_ids = [c["id"] for c in self.config['channels']]
            for channel in channels:
                assert channel in channel_ids
            self._subscribe()

    def ensure_live_channels(self, channels):
        """
        If any of `channels` are not currently being streamed, begin
        streaming them in addition to the current channels.
        """
        new_channels = set(channels) - set(self.stream_channels)
        if new_channels:
            self.set_live_channels(self.stream_channels + list(new_channels))

    @contextmanager
    def updates_paused(self):
        """Context manager which pauses updates in its block."""
        self.paused = True
        try:
            yield
        finally:
            self.paused = False

    def get_config(self):
        return self.config

    def get_channels(self):
        return self.config['channels']

    def get_status(self):
        return self.status

    def get_time(self):
        return self.last_time

    def _connect_socket(self):
        logger.info("Connecting socket")
        host, port = self.host.split(":")
        self.socket.connectToHost(host, int(port))
        if not self.socket.waitForConnected(500):
            return False
        self._request_status()
        self._request_config()
        wait_ticks = 0
        while self.config is None and wait_ticks < 50:
            loop = QEventLoop()
            QTimer.singleShot(10, loop.quit)
            loop.exec()
            self._socket_ready_read()
            wait_ticks += 1
        if wait_ticks == 50:
            logger.warning("Did not receive configuration from server")
        self._subscribe()
        return True

    def _send_request(self, tag):
        msg = struct.pack("<HH", tag, 0)
        self.socket.write(msg)

    def _request_config(self):
        self._send_request(self._TAG_CONFIG_REQUEST)

    def _request_status(self):
        self._send_request(self._TAG_STATUS_REQUEST)

    def _detect_old_daqd(self):
        """
        Guess we're talking to old daqd if the status exists and is all dummy,
        as it never implemented getting status from daqng.
        This requires we've already received a STATUS_RESPONSE though,
        so be careful not to _subscribe() until we should have received one.
        """
        return (
            self.status is not None
            and all(self.status.get(f) == "dummy"
                    for f in ("test_name", "config_file", "assets_file"))
        )

    def _stream_idxs(self):
        idxs = []
        for channel_id in self.stream_channels:
            for idx, channel in enumerate(self.config['channels']):
                if channel['id'] == channel_id:
                    idxs.append(idx)
                    break
            else:
                assert f"Could not find {channel_id} in channels"
        return idxs

    def _subscribe(self):
        if self._detect_old_daqd():
            data = ",".join(self.stream_channels).encode()
            length = len(data)
            msg = struct.pack("<HH", self._TAG_SUBSCRIBE_REQUEST, length)
            msg += data
        else:
            length = len(self.stream_channels) * 2
            msg = struct.pack("<HH", self._TAG_SUBSCRIBE_IDXS_REQUEST, length)
            for idx in self._stream_idxs():
                msg += struct.pack("<H", idx)
        self.socket.write(msg)

    def _socket_error(self, error):
        logger.error("Socket error: %s (%s)", error, self.socket.errorString())
        self.socket.abort()
        if self._connected:
            QTimer.singleShot(200, self._connect_socket)

    def _socket_ready_read(self):
        while self.socket.bytesAvailable() >= 4:
            if self.pending is None:
                data = bytes(self.socket.read(4))
                tag, length = self.unpack_hh(data)
            else:
                tag, length = self.pending
                self.pending = None
            avail = self.socket.bytesAvailable()
            if avail < length:
                self.pending = tag, length
                return
            data = bytes(self.socket.read(length))
            if tag == self._TAG_DATA_INDICATION:
                nch, ts = self.unpack_hd(data[:10])
                data = np.ndarray((nch,), buffer=data[10:])
                self.data_queue.append((ts, data))
                QTimer.singleShot(0, self._process_queue)
            elif tag == self._TAG_CONFIG_RESPONSE:
                self.config = json.loads(data)
                if self.stream_channels:
                    self._subscribe()
                channels = self.config['channels']
                self.channels_table = ChannelsTableModel(channels)
                self.live_data.update_channels(
                    self.config['channels'], self.config['groups'])
                self.config_update.emit()
            elif tag == self._TAG_STATUS_RESPONSE:
                self.status = json.loads(data)
                self.status_update.emit()

    def _process_queue(self):
        n = len(self.data_queue)
        if not n:
            return
        nch = self.data_queue[0][1].size
        if nch != len(self.stream_channels):
            self.data_queue.clear()
            return
        q_ts = np.empty(n)
        q_data = np.empty((nch, n))
        q_status = np.empty((nch, n), dtype=np.uint8)
        for idx, (ts, data) in enumerate(self.data_queue):
            if data.size != nch:
                self.data_queue.clear()
                return
            q_ts[idx] = ts
            q_data[:, idx] = data
            q_status[:, idx] = 0
        self.data_queue.clear()
        self.live_data.data_update(
            q_ts, self.stream_channels, q_data, q_data, q_data, q_status,
            not self.paused)
        self.last_time = ts
        if not self.paused:
            self.time_update.emit(ts)
