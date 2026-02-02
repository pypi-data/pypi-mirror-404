import logging

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QProgressBar, QTextEdit,
                               QApplication)


logger = logging.getLogger(__name__)


class SequenceLoadDialog(QDialog):
    def __init__(self, rendered, parent=None):
        super().__init__(parent)
        self.rendered = rendered
        self.setWindowTitle("Loading Sequences")
        self.app = QApplication.instance()
        self.init_ui()
        self.cancelled = False
        self.errors = []
        QTimer.singleShot(50, self.run)

    def run(self):
        self.store_json()
        self.load_daus()
        if not self.cancelled and not self.errors:
            self.add_log("Finished.")
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
        if self.errors:
            self.log.setFontWeight(700)
            self.log.setTextColor(QColor.fromRgb(255, 0, 0))
            self.add_log("\n\nEncountered the following errors loading boxes:")
            self.log.setFontWeight(500)
            for error in self.errors:
                self.add_log(error)
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)

    def cancel_clicked(self):
        self.cancelled = True
        self.add_log("Cancelled.")
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def add_log(self, message):
        logger.info(message)
        self.log.append(message)
        self.app.processEvents()

    def add_error(self, message):
        logger.info(message)
        normal_colour = self.log.textColor()
        self.log.setTextColor(QColor.fromRgb(255, 0, 0))
        self.log.append(message)
        self.log.setTextColor(normal_colour)
        self.errors.append(message)
        self.app.processEvents()

    def increment_progress(self):
        self.progress.setValue(self.progress.value() + 1)
        self.app.processEvents()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.progress = QProgressBar(self)
        n_items = 1 + len(self.rendered.daus)
        self.progress.setRange(0, n_items)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log = QTextEdit(self)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        btns_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.cancel_clicked)
        self.cancel_btn = cancel_btn
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        close_btn.setEnabled(False)
        self.close_btn = close_btn
        btns_layout.addStretch()
        btns_layout.addWidget(cancel_btn)
        btns_layout.addWidget(close_btn)
        layout.addLayout(btns_layout)

        self.resize(512, 320)

    def store_json(self):
        data_path = self.app.prefs.get_daqng_data_path()
        self.add_log(f"Using data directory {data_path}")
        self.add_log("Writing JSON metdata file...")
        self.rendered.write_json_metadata(data_path)
        self.increment_progress()

    def load_daus(self):
        daus = list(self.rendered.daus.keys())
        daus.sort(key=lambda x: len(self.rendered.daus[x].sequences))
        for dau_id in daus:
            dau = self.rendered.daus[dau_id]
            if self.cancelled:
                return
            if len(dau.sequences) == 0:
                self.add_log(f"Loading empty profile to {dau.dau_id}...")
            else:
                self.add_log(f"Loading sequences to {dau.dau_id}...")
            try:
                dau.load()
            except (OSError, AssertionError, RuntimeError) as e:
                self.add_error(f"Error: Could not load {dau.dau_id} at {dau.addr}: {e}")
            self.increment_progress()
