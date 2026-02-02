import importlib.metadata
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About DAQView")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("<h1>DAQview</h1>")
        layout.addWidget(title)
        copyright = QLabel("Copyright 2018-2023 Airborne Engineering Ltd")
        layout.addWidget(copyright)
        version = importlib.metadata.version('daqview')
        version = QLabel("Version {}".format(version))
        layout.addWidget(version)
        bottom_buttons = QHBoxLayout()
        close = QPushButton("Close", self)
        close.clicked.connect(self.close)
        close.setDefault(True)
        bottom_buttons.addStretch()
        bottom_buttons.addWidget(close)
        layout.addLayout(bottom_buttons)
