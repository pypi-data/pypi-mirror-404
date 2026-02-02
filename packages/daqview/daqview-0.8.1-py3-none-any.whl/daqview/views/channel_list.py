from PySide6.QtWidgets import (QDialog, QVBoxLayout, QApplication, QTableView,
                               QPushButton, QHBoxLayout, QAbstractItemView)
from PySide6.QtCore import Qt


class ChannelListDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.setWindowTitle("DAQview Server Channel List")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        table = QTableView(self)
        table.setModel(self.app.server.channels_table)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        layout.addWidget(table)
        bottom_buttons = QHBoxLayout()
        close = QPushButton("Close", self)
        close.clicked.connect(self.close)
        bottom_buttons.addStretch()
        bottom_buttons.addWidget(close)
        layout.addLayout(bottom_buttons)
        width = table.horizontalHeader().length() + 24
        height = table.verticalHeader().length() + 24
        self.resize(width, height)
