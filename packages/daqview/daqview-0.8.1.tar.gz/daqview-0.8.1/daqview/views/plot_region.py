import math
import logging
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QMenu,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QWidget,
    QWidgetAction,
    QCheckBox,
    QApplication,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal
from .plot_hover_box import PlotHoverBox
from .plot_legend import LegendItem
from ..models.measurements import MEASUREMENTS, MeasurementResult

logger = logging.getLogger(__name__)


class PlotRegion(pg.LinearRegionItem):
    """
    A region on a chart which can be resized and repositioned, and provides
    analysis of all channel data inside the region.
    """

    measurements_changed = Signal()

    def __init__(self, values, label_pos, pw):
        super().__init__(values=values, movable=True)
        logger.info("Creating PlotRegion at times %s", values)
        self.pw = pw
        self.measurements_enabled = {k: False for k in [m.KEY for m in MEASUREMENTS]}
        for m in ("left", "right", "delta", "gradient", "mean"):
            self.measurements_enabled[m] = True
        self.label = PlotRegionLabel(self, label_pos)
        self.menu = PlotRegionMenu(self)
        self.measurements_changed.emit()

    def active_measurements(self):
        return [m for m in MEASUREMENTS if self.measurements_enabled.get(m.KEY, False)]

    def set_measurement_enabled(self, key, state):
        if key in self.measurements_enabled:
            if self.measurements_enabled[key] != state:
                logger.info("Setting measurement %s enabled to %s", key, state)
                self.measurements_enabled[key] = state
                self.measurements_changed.emit()
        else:
            logger.warning("Unknown measurement %s", key)


class MeasurementLabel(pg.LabelItem):
    """Custom LabelItem with hover events."""

    def __init__(self, *args, channel, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel
        self.result = MeasurementResult("")
        self.items = []
        self.line_pen = pg.mkPen(width=3, color=(255, 255, 0), style=Qt.DotLine)
        self.tgt_pen = pg.mkPen(width=3, color=(255, 255, 0))

    def set_result(self, result):
        self.result = result
        self.setText(result.value)

    def hoverEvent(self, ev):
        if ev.exit:
            self.setText(self.result.value)
            for item in self.items:
                self.channel.pw.pi.removeItem(item)
            self.items.clear()
        else:
            self.setText(f"<b>{self.result.value}</b>")
            for vline in self.result.vlines:
                if not math.isfinite(vline):
                    continue
                line = pg.InfiniteLine(vline, angle=90, pen=self.line_pen)
                self.channel.pw.pi.addItem(line)
                self.items.append(line)
            for hline in self.result.hlines:
                if not math.isfinite(hline):
                    continue
                line = pg.InfiniteLine(hline, angle=0, pen=self.line_pen)
                self.channel.pw.pi.addItem(line)
                self.items.append(line)
            for target in self.result.targets:
                if not math.isfinite(target):
                    continue
                target = pg.TargetItem(target, size=20, pen=self.tgt_pen, movable=False)
                self.channel.pw.pi.addItem(target)
                self.items.append(target)


class PlotRegionLabel(PlotHoverBox):
    """
    A box that displays readouts from a region selection.
    Based on LegendItem but with additional values and a header.
    """

    def __init__(self, parent, offset):
        super().__init__(size=None, offset=offset)
        self.pr = parent
        parent.pw.channels_changed.connect(self.channels_changed)
        parent.sigRegionChanged.connect(self.update_values)
        parent.measurements_changed.connect(self.measurements_changed)
        self.setParentItem(self.pr.pw.pi.vb)
        self.layout.setHorizontalSpacing(20)
        self.header_lbls = []
        self.channel_lbls = []
        self.time_channel = _TimeChannel()
        self.set_header()
        self.add_channels()
        self.update_values()

    def channels_changed(self):
        self.add_channels()
        self.update_values()

    def measurements_changed(self):
        logger.info("Selected measurements changed, redrawing label")
        self.set_header()
        self.add_channels()
        self.update_values()

    def set_header(self):
        row = 0
        for lbl in self.header_lbls:
            lbl.close()
            self.layout.removeItem(lbl)
        self.header_lbls.clear()
        self.header_lbls.append(pg.LabelItem("<b>Channel</b>"))
        for m in self.pr.active_measurements():
            label = pg.LabelItem(f"<b>{m.LABEL}</b>")
            label.mouseDoubleClickEvent = lambda e, m=m: self.header_clicked(m)
            self.header_lbls.append(label)
        for col, lbl in enumerate(self.header_lbls):
            self.layout.addItem(lbl, row, col)
        self.updateSize()

    def header_clicked(self, measurement):
        t0, t1 = self.pr.getRegion()
        times = [t0, t1]
        results = []
        if getattr(measurement, "TIME", False):
            r = measurement.measure(self.time_channel, times, times)
            results.append(r)
        for channel in self.pr.pw.channels:
            times, values = channel.values_for_times(t0, t1)
            r = measurement.measure(channel, times, values)
            results.append(r)
        app = QApplication.instance()
        app.clipboard().clear()
        app.clipboard().setText(",".join(f"{r.raw_value:.06g}" for r in results))
        logger.info("Copying analysis results to clipboard")

    def add_channels(self):
        # Remove all existing labels
        for lbls in self.channel_lbls:
            for lbl in lbls:
                lbl.close()
                self.layout.removeItem(lbl)
        self.channel_lbls.clear()

        # Add labels for virtual 'time' channel
        lbls = []
        lbls.append(pg.LabelItem("Time"))
        for m in self.pr.active_measurements():
            lbls.append(MeasurementLabel(channel=self.time_channel))
        self.channel_lbls.append(lbls)
        for col, lbl in enumerate(lbls):
            self.layout.addItem(lbl, 1, col)

        # Add labels for all the real channels
        for row, channel in enumerate(self.pr.pw.channels):
            lbls = []
            lbls.append(LegendItem(channel.get_name(), channel=channel))
            for m in self.pr.active_measurements():
                lbls.append(MeasurementLabel(channel=channel))
            self.channel_lbls.append(lbls)
            for col, lbl in enumerate(lbls):
                self.layout.addItem(lbl, row + 2, col)

    def update_values(self):
        t0, t1 = self.pr.getRegion()

        # Process time measurements, typically just left/right
        time_lbls = self.channel_lbls[0]
        times = [t0, t1]
        for col, m in enumerate(self.pr.active_measurements()):
            if getattr(m, "TIME", False):
                r = m.measure(self.time_channel, times, times)
                time_lbls[col + 1].set_result(r)

        # Process real channel measurements
        for row, channel in enumerate(self.pr.pw.channels):
            times, values = channel.values_for_times(t0, t1)
            lbls = self.channel_lbls[row + 1]
            for col, m in enumerate(self.pr.active_measurements()):
                r = m.measure(channel, times, values)
                lbls[col + 1].set_result(r)

    def mouseDragEvent(self, ev):
        # Set new position in parent for later saving to layout file.
        super().mouseDragEvent(ev)
        self.pr.pw.region_label_pos = self.pos()

    def mouseClickEvent(self, ev):
        # Open context menu when clicked, and prevent event propagating to
        # underlying objects that might also want to open a context menu.
        if ev.button() == Qt.MouseButton.RightButton:
            ev.accept()
            self.pr.menu.popup(ev.screenPos().toPoint())


class PlotRegionMenu(QMenu):
    """
    Custom QWidget for the analysis region context menu.
    """

    def __init__(self, region):
        super().__init__()

        self.pr = region
        self.channel_menus = []

        self.init_ui()
        self.channels_changed()

    def init_ui(self):
        self.measurements_menu = PlotRegionMeasurementsMenu(self.pr, self)
        self.addMenu(self.measurements_menu)

        self.channels_menu = QMenu("Channels", self)
        self.pr.pw.channels_changed.connect(self.channels_changed)
        self.addMenu(self.channels_menu)

    def channels_changed(self):
        for menu in self.channel_menus:
            self.channels_menu.removeAction(menu.menuAction())
            menu.close()
        self.channels_menu.clear()
        self.channel_menus.clear()

        for channel in self.pr.pw.channels:
            menu = PlotRegionChannelMenu(channel, self.pr, self)
            self.channels_menu.addMenu(menu)
            self.channel_menus.append(menu)


class PlotRegionMeasurementsMenu(QMenu):
    def __init__(self, region, parent):
        super().__init__("Measurements", parent)
        self.aboutToShow.connect(self.about_to_show)
        self.pr = region
        self.init_ui()

    def init_ui(self):
        self.toggles = {}
        for m in MEASUREMENTS:
            action = QAction(m.NAME, self)
            action.setCheckable(True)
            action.triggered.connect(self.measurement_toggled(m.KEY))
            self.addAction(action)
            self.toggles[m.KEY] = action

    def about_to_show(self):
        for m in MEASUREMENTS:
            self.toggles[m.KEY].setChecked(self.pr.measurements_enabled[m.KEY])

    def measurement_toggled(self, key):
        def toggled(checked=False):
            self.pr.set_measurement_enabled(key, checked)

        return toggled


class PlotRegionChannelMenu(QMenu):
    def __init__(self, channel, region, parent):
        super().__init__(channel.name, parent)
        self.aboutToShow.connect(self.about_to_show)
        self.channel = channel
        self.pr = region
        self.init_ui()

    def init_ui(self):
        self.curve_fit_menu = QMenu("Curve Fit", self)
        self.curve_fit_widget = CurveFitMenu(self.channel, self.pr, self)
        self.curve_fit_action = QWidgetAction(self.curve_fit_menu)
        self.curve_fit_action.setDefaultWidget(self.curve_fit_widget)
        self.curve_fit_menu.addAction(self.curve_fit_action)
        self.addMenu(self.curve_fit_menu)

        self.show_fft = QAction("FFT", self)
        self.show_fft.setCheckable(True)
        self.show_fft.triggered.connect(self.fft_toggled)
        self.addAction(self.show_fft)

    def fft_toggled(self, checked=False):
        fft_window = self.pr.pw.parent.get_fft_window()
        if checked:
            fft_window.add_channel(
                self.channel.dataset, self.channel.channel_id, self.pr
            )
        else:
            fft_window.remove_channel_id(self.channel.channel_id)

    def about_to_show(self):
        present = self.pr.pw.parent.fft_channel_present(self.channel.channel_id)
        self.show_fft.setChecked(present)


class CurveFitMenu(QWidget):
    """
    Custom QWidget for the curve fit context menu.
    """

    def __init__(self, channel, region, parent):
        super().__init__(parent)
        self.channel = channel
        self.pr = region
        self.pw = region.pw
        self.init_ui()
        parent.aboutToShow.connect(self.update_ui)
        region.sigRegionChanged.connect(self.region_changed)
        region.pw.region_changed.connect(self.region_visibility_changed)

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.mode_none = QRadioButton("None", self)
        self.mode_none.setChecked(True)
        self.mode_none.clicked.connect(self.none_clicked)
        layout.addWidget(self.mode_none)

        self.mode_linear = QRadioButton("Linear", self)
        self.mode_linear.clicked.connect(self.linear_clicked)
        layout.addWidget(self.mode_linear)
        self.linear_label = QLabel("    y=Ax + B")
        layout.addWidget(self.linear_label)

        self.mode_sinusoidal = QRadioButton("Sinusoidal", self)
        self.mode_sinusoidal.clicked.connect(self.sinusoidal_clicked)
        layout.addWidget(self.mode_sinusoidal)
        self.sinusoidal_label = QLabel("    y=Asin(2πBx + C) + D")
        layout.addWidget(self.sinusoidal_label)

        """
        self.mode_sinusoidal_linear = QRadioButton("Sinusoidal Linear", self)
        layout.addWidget(self.mode_sinusoidal_linear)
        self.sinusoidal_linear_label = QLabel("    y=(A + Bx)sin(2πCx + D) + E")
        layout.addWidget(self.sinusoidal_linear_label)
        """

        self.mode_exponential = QRadioButton("Exponential", self)
        self.mode_exponential.clicked.connect(self.exponential_clicked)
        layout.addWidget(self.mode_exponential)
        self.exponential_label = QLabel("    y=Aexp(Bx + C) + D")
        layout.addWidget(self.exponential_label)

        self.autofit = QCheckBox("Auto fit", self)
        self.autofit.setChecked(True)
        self.autofit.stateChanged.connect(self.autofit_changed)
        layout.addWidget(self.autofit)

        self.param_edits = {}
        self.param_labels = {}
        for param in "abcde":
            edit = QLineEdit(self)
            label = QLabel(f"{param.upper()}:", self)
            label.setEnabled(False)
            self.param_edits[param] = edit
            self.param_labels[param] = label
            edit.setMaxLength(10)
            edit.setMaximumWidth(edit.minimumSizeHint().width() * 5)
            edit.setEnabled(False)
            edit.editingFinished.connect(self.params_updated)
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(edit)
            hbox.addStretch()
            layout.addLayout(hbox)

    def none_clicked(self, checked=False):
        self.channel.set_fit_none()
        self.update_ui()

    def linear_clicked(self, checked=False):
        self.channel.set_fit_linear(*self.pr.getRegion())
        self.update_ui()

    def sinusoidal_clicked(self, checked=False):
        self.channel.set_fit_sinusoidal(*self.pr.getRegion())
        self.update_ui()

    def exponential_clicked(self, checked=False):
        self.channel.set_fit_exponential(*self.pr.getRegion())
        self.update_ui()

    def autofit_changed(self, checked=False):
        self.channel.set_fit_autofit(checked)
        self.update_ui()

    def region_changed(self):
        self.channel.fit_region_changed(*self.pr.getRegion())

    def region_visibility_changed(self, visible):
        if not visible:
            self.channel.set_fit_none()

    def params_updated(self):
        params = {}
        for param in "abcde":
            v = self.param_edits[param].text()
            if v != "":
                params[param] = float(self.param_edits[param].text())
            else:
                params[param] = 0.0
        self.channel.set_fit_params(params)

    def update_ui(self):
        params = self.channel.get_fit_params()
        autofit = self.channel.get_fit_autofit()
        for param in self.param_edits:
            if param in params:
                self.param_edits[param].setText(str(params[param]))
                self.param_edits[param].setEnabled(not autofit)
                self.param_labels[param].setEnabled(True)
            else:
                self.param_edits[param].setText("")
                self.param_edits[param].setEnabled(False)
                self.param_labels[param].setEnabled(False)


class _TimeChannel:
    """
    Mock Channel object used for the virtual time channel in measurements,
    which just provides a suitable formatted_value method.
    """

    def formatted_value(self, value):
        return f"{value:.03f}"
