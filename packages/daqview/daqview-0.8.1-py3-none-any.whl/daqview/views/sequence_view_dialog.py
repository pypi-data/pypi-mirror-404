import logging

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QApplication, QFileDialog)

from .tab_dock import TabDock
from ..models.profile_dataset import ProfileDataset


logger = logging.getLogger(__name__)


class SequenceViewDialog(QDialog):
    def __init__(self, rendered, parent=None):
        super().__init__(parent)
        self.rendered = rendered
        self.ds = ProfileDataset(rendered)
        self.setWindowTitle("Sequence View")
        self.app = QApplication.instance()
        self.init_ui()
        self.add_profile_channels()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.dock = TabDock(False)
        layout.addWidget(self.dock.dock_area)

        groups = self.ds.channels_by_group()
        if groups.get('run_profiles', []):
            self.run_prof_pw = self.dock.new_plot_window("Run Profiles")
            self.run_prof_pw.show_legend()
        if groups.get('stop_profiles', []):
            self.stop_prof_pw = self.dock.new_plot_window("Stop Profiles")
            self.stop_prof_pw.show_legend()
        if groups.get('run_seq', []):
            self.run_pw = self.dock.new_plot_window("Run Sequences")
            self.run_pw.show_legend()
            self.run_pw.vb.y_axis.setStyle(showValues=False)
        if groups.get('stop_seq', []):
            self.stop_pw = self.dock.new_plot_window("Stop Sequences")
            self.stop_pw.show_legend()
            self.stop_pw.vb.y_axis.setStyle(showValues=False)

        btns_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        export_btn = QPushButton("Export", self)
        export_btn.clicked.connect(self.export)
        accept_btn = QPushButton("Load Boxes", self)
        accept_btn.clicked.connect(self.accept)
        btns_layout.addStretch()
        btns_layout.addWidget(cancel_btn)
        btns_layout.addWidget(export_btn)
        btns_layout.addWidget(accept_btn)
        layout.addLayout(btns_layout)

    def add_profile_channels(self):
        groups = self.ds.channels_by_group()
        run_chs = groups.get('run_seq', [])
        stop_chs = groups.get('stop_seq', [])
        for ch in groups.get('run_profiles', []):
            self.run_prof_pw.add_channel(self.ds, ch['id'])
        for ch in sorted(run_chs, key=lambda ch: ch['id']):
            self.run_pw.add_channel(self.ds, ch['id'])
        for ch in groups.get('stop_profiles', []):
            self.stop_prof_pw.add_channel(self.ds, ch['id'])
        for ch in sorted(stop_chs, key=lambda ch: ch['id']):
            self.stop_pw.add_channel(self.ds, ch['id'])
        self.stop_pw.vb.y_axis.showLabel(False)
        self.run_pw.vb.y_axis.showLabel(False)

    def export(self):
        fname = QFileDialog.getSaveFileName(
            self,
            "Export sequence as...",
            "",
            "Dataset (*.h5)",
            ""
        )[0]
        if not fname:
            logger.info("No file provided, not exporting sequence")
            return
        if fname != "" and not fname.endswith(".h5"):
            fname = fname + ".h5"
        logger.info("Exporting sequence to '%s'", fname)
        self.ds.save_data(fname)
