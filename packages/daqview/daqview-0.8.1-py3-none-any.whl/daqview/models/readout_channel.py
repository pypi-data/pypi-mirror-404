import logging
from PySide6.QtWidgets import QLabel

from .channel import Channel

logger = logging.getLogger(__name__)


class ReadoutChannel(Channel):
    """
    Represents one channel inside a ReadoutWindow.
    """
    def __init__(self, dataset, channel_id, readout_window):
        super().__init__(dataset, channel_id, readout_window)
        self.rw = readout_window
        self.name_lbl = QLabel(self.name)
        self.unit_lbl = QLabel(self.units)
        self.value_lbl = QLabel(self.formatted_value())
        self.removed = False
        self.highlight = False

    def add_to_layout(self, layout, row):
        layout.addWidget(self.name_lbl, row, 0)
        layout.addWidget(self.value_lbl, row, 1)
        layout.addWidget(self.unit_lbl, row, 2)

    def update_data(self):
        _, data = self.dataset.get_channel_data(self.channel_id)
        if data.size:
            self.current_value = data[-1]
            if not self.removed:
                self.value_lbl.setText(self.formatted_value())

    def remove(self):
        super().remove()
        self.name_lbl.deleteLater()
        self.value_lbl.deleteLater()
        self.unit_lbl.deleteLater()
        self.removed = True

    def set_highlight(self, highlight):
        self.highlight = highlight
        for lbl in (self.name_lbl, self.unit_lbl, self.value_lbl):
            if highlight:
                lbl.setStyleSheet("QLabel { background-color: yellow; }")
            else:
                lbl.setStyleSheet("QLabel { }")

    def serialise(self):
        logger.info("Serialising channel %s", self.name)
        ser = super().serialise()
        ser.update({
            "highlight": self.highlight,
        })
        return ser

    def deserialise(self, layout):
        logger.info("Deserialising channel %s", self.name)
        super().deserialise(layout)
        self.set_highlight(layout['highlight'])
