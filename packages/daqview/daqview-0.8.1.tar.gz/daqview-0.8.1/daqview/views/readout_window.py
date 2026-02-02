import logging
from PySide6.QtWidgets import QWidget, QGridLayout

from .window import Window
from ..models.readout_channel import ReadoutChannel
from .readout_menus import ReadoutContextMenu

logger = logging.getLogger(__name__)


class ReadoutWidget(QWidget):
    def __init__(self, context_menu):
        super().__init__()
        self.menu = context_menu

    def contextMenuEvent(self, ev):
        self.menu.exec_(self.mapToGlobal(ev.pos()))


class ReadoutWindow(Window):
    """
    Manages a Dock and ReadoutWidget.

    Signals:
    closed: emitted when the managed Dock closes, with argument self.
    name_changed: emitted when the window is renamed
    channels_changed: emitted when the displayed channels change
    """

    def __init__(self, name, parent):
        """
        name: string name to show in label
        parent: the TabDock to which this ReadoutWindow belongs
        """
        super().__init__(name, parent)
        self.context_menu = ReadoutContextMenu(self)
        self.widget = ReadoutWidget(self.context_menu)
        self.widget.layout = QGridLayout(self.widget)
        self.dock.addWidget(self.widget)
        self.rows = []
        self.row_idx = 0

    def add_channel(self, dataset, channel_id, emit_changed=True):
        channel = ReadoutChannel(dataset, channel_id, self)
        self.channels.append(channel)
        if emit_changed:
            self.channels_changed.emit()
        channel.add_to_layout(self.widget.layout, self.row_idx)
        self.row_idx += 1
        return channel

    def serialise(self):
        logger.info("Serialising ReadoutWindow %s", self.name)
        return {
            "name": self.name,
            "type": "readout",
            "channels": [c.serialise() for c in self.channels]
        }

    def deserialise(self, layout):
        self.rename(layout['name'], force=True)
        logger.info("Deserialising ReadoutWindow %s", self.name)

        for channel in layout['channels']:
            if channel['dataset'] not in self.app.datasets:
                logger.warning("Dataset '%s' not found", channel['dataset'])
                continue
            dataset = self.app.datasets[channel['dataset']]
            if channel['channel_id'] not in dataset.channels_by_id():
                logger.warning("Channel '%s' not found in dataset '%s'",
                               channel['channel_id'], channel['dataset'])
                continue
            rc = self.add_channel(dataset, channel['channel_id'])
            rc.deserialise(channel)
