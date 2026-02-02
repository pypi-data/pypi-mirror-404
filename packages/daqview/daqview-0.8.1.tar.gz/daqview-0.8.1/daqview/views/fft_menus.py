import logging
import os.path
from types import MethodType
from PySide6.QtWidgets import (QWidgetAction, QWidget, QLineEdit,
                               QLabel, QVBoxLayout, QHBoxLayout, QCheckBox,
                               QInputDialog, QFileDialog, QMenu, QApplication,
                               QColorDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class FftContextXAxis(QWidget):
    """
    Custom QWidget for the FFT x-axis context menu.
    """
    def __init__(self, parent):
        """
        `parent`: the parent FftContextMenu
        """
        super().__init__(parent)
        self.vb = parent.vb
        self.fw = parent.fw
        self.init_ui()
        self.update_ui_state()

        self.manual_from.editingFinished.connect(self.manual_edited)
        self.manual_to.editingFinished.connect(self.manual_edited)
        self.mouse.stateChanged.connect(self.mouse_changed)
        self.grid.stateChanged.connect(self.grid_changed)
        self.vb.sigXRangeChanged.connect(self.range_changed)
        parent.aboutToShow.connect(self.update_ui_state)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.manual_from = QLineEdit(self)
        self.manual_from.setMaximumWidth(
            self.manual_from.minimumSizeHint().width() * 3)
        manual_to_lbl = QLabel("to", self)
        self.manual_to = QLineEdit(self)
        self.manual_to.setMaximumWidth(
            self.manual_to.minimumSizeHint().width() * 3)
        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignLeft)
        hbox.addWidget(self.manual_from)
        hbox.addWidget(manual_to_lbl)
        hbox.addWidget(self.manual_to)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        QWidget.setTabOrder(self.manual_from, self.manual_to)

        self.mouse = QCheckBox("Enable Mouse", self)
        self.layout.addWidget(self.mouse)

        self.grid = QCheckBox("Show Grid", self)
        self.layout.addWidget(self.grid)

        self.logscale = QCheckBox("Log Scale", self)
        self.layout.addWidget(self.logscale)
        self.logscale.stateChanged.connect(self.logscale_changed)

    def update_ui_state(self):
        self.manual_from.setText(str(self.vb.get_x_manual_from()))
        self.manual_to.setText(str(self.vb.get_x_manual_to()))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)
        self.mouse.setChecked(self.vb.get_x_mouse())
        self.grid.setChecked(self.vb.get_x_grid())
        self.logscale.setChecked(self.vb.get_x_logscale())

    def manual_edited(self):
        try:
            manual_from = float(self.manual_from.text())
            manual_to = float(self.manual_to.text())
        except ValueError:
            pass
        else:
            self.vb.set_manual_x_range(manual_from, manual_to)

    def mouse_changed(self, state):
        self.vb.set_x_mouse(bool(state))

    def grid_changed(self, state):
        self.vb.set_x_grid(bool(state))

    def logscale_changed(self, state):
        self.vb.set_x_logscale(bool(state))

    def range_changed(self, _vb, viewrange):
        xmin, xmax = viewrange
        self.manual_from.setText(str(xmin))
        self.manual_to.setText(str(xmax))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)


class FftContextYAxis(QWidget):
    """
    Custom QWidget for the FFT y-axis context menu.
    """
    def __init__(self, parent):
        """
        `parent`: the parent FftContextMenu
        """
        super().__init__(parent)
        self.vb = parent.vb
        self.fw = parent.fw
        self.init_ui()
        self.update_ui_state()

        self.vb.sigYRangeChanged.connect(self.range_changed)
        parent.aboutToShow.connect(self.update_ui_state)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.manual_from = QLineEdit(self)
        self.manual_from.setMaximumWidth(
            self.manual_from.minimumSizeHint().width() * 3)
        self.manual_from.editingFinished.connect(self.manual_edited)
        self.manual_to = QLineEdit(self)
        self.manual_to.setMaximumWidth(
            self.manual_to.minimumSizeHint().width() * 3)
        self.manual_to.editingFinished.connect(self.manual_edited)
        manual_to_lbl = QLabel("to", self)
        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignLeft)
        hbox.addWidget(self.manual_from)
        hbox.addWidget(manual_to_lbl)
        hbox.addWidget(self.manual_to)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        QWidget.setTabOrder(self.manual_from, self.manual_to)

        self.mouse = QCheckBox("Enable Mouse", self)
        self.layout.addWidget(self.mouse)
        self.mouse.stateChanged.connect(self.mouse_changed)

        self.grid = QCheckBox("Show Grid", self)
        self.layout.addWidget(self.grid)
        self.grid.stateChanged.connect(self.grid_changed)

    def update_ui_state(self):
        self.manual_from.setText(str(self.vb.get_y_manual_from()))
        self.manual_to.setText(str(self.vb.get_y_manual_to()))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)
        self.mouse.setChecked(self.vb.get_y_mouse())
        self.grid.setChecked(self.vb.get_y_grid())

    def manual_edited(self):
        try:
            manual_from = float(self.manual_from.text())
            manual_to = float(self.manual_to.text())
        except ValueError:
            pass
        else:
            self.vb.set_manual_y_range(manual_from, manual_to)

    def mouse_changed(self, state):
        self.vb.set_y_mouse(bool(state))

    def grid_changed(self, state):
        self.vb.set_y_grid(bool(state))

    def range_changed(self, _vb, viewrange):
        ymin, ymax = viewrange
        self.manual_from.setText(str(ymin))
        self.manual_to.setText(str(ymax))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)
        self.vb.update_manual_y_range(float(ymin), float(ymax))


class ChannelContextMenu(QMenu):
    """
    Context menu for an individual channel.
    """
    def __init__(self, channel, parent):
        """
        channel: the FftChannel that corresponds to this context menu
        parent: the QMenu to which this menu belongs
        """
        super().__init__(channel.get_name(), parent)
        self.aboutToShow.connect(self.about_to_show)
        self.channel = channel
        self.init_ui()

    def init_ui(self):
        self.show_channel = QAction("Show Channel", self)
        self.show_channel.setCheckable(True)
        self.show_channel.toggled.connect(self.show_channel_toggled)
        self.addAction(self.show_channel)

        hide_others = QAction("Hide Others", self)
        hide_others.triggered.connect(self.hide_others_triggered)
        self.addAction(hide_others)

        self.highlight = QAction("Highlight", self)
        self.highlight.setCheckable(True)
        self.highlight.toggled.connect(self.highlight_channel_toggled)
        self.addAction(self.highlight)

        set_colour = QAction("Set Colour...", self)
        set_colour.triggered.connect(self.set_colour_triggered)
        self.addAction(set_colour)

        remove = QAction("Remove", self)
        remove.triggered.connect(self.remove_triggered)
        self.addAction(remove)

        self.about_to_show()

    def about_to_show(self):
        self.show_channel.setChecked(self.channel.show_channel)
        self.highlight.setChecked(self.channel.highlight)

    def show_channel_toggled(self, checked=False):
        if checked:
            self.channel.show()
        else:
            self.channel.hide()

    def highlight_channel_toggled(self, checked=False):
        self.channel.set_highlight(checked)

    def hide_others_triggered(self):
        self.channel.hide_others()

    def set_colour_triggered(self):
        current = self.channel.get_qcolor()
        new_colour = QColorDialog.getColor(
            current, self, "Choose Colour for " + self.channel.get_name(),
            QColorDialog.DontUseNativeDialog)
        if new_colour.isValid():
            self.channel.update_colour(new_colour.name())
        else:
            logger.info("User cancelled new colour")

    def remove_triggered(self):
        self.channel.remove()


class FftContextMenu(QMenu):
    """
    The right-click context menu on FftWindows.
    """
    def __init__(self, vb):
        super().__init__()

        # Store refs to both the parent ViewBox and its parent FftWindow
        self.vb = vb
        self.fw = vb.fw

        # Store child channel menus
        self.channel_menus = []

        self.init_ui()

    def init_ui(self):
        self.channelsmenu = QMenu("Channels", self)
        self.fw.channels_changed.connect(self.channels_changed)
        self.addMenu(self.channelsmenu)

        self.xmenu = QMenu("X Axis", self)
        self.xmenu_widget = FftContextXAxis(self)
        self.xmenu_action = QWidgetAction(self.xmenu)
        self.xmenu_action.setDefaultWidget(self.xmenu_widget)
        self.xmenu.addAction(self.xmenu_action)
        self.addMenu(self.xmenu)

        self.xmenu.focusNextPrevChild = MethodType(
            QWidget.focusNextPrevChild, self.xmenu)

        self.ymenu = QMenu("Y Axis", self)
        self.ymenu_widget = FftContextYAxis(self)
        self.ymenu_action = QWidgetAction(self.ymenu)
        self.ymenu_action.setDefaultWidget(self.ymenu_widget)
        self.ymenu.addAction(self.ymenu_action)
        self.addMenu(self.ymenu)

        self.ymenu.focusNextPrevChild = MethodType(
            QWidget.focusNextPrevChild, self.ymenu)

        self.show_legend = QAction("Legend", self)
        self.show_legend.setCheckable(True)
        self.show_legend.toggled.connect(self.show_legend_toggled)
        self.fw.legend_changed.connect(self.legend_changed)
        self.addAction(self.show_legend)

        self.show_cursor = QAction("Cursor", self)
        self.show_cursor.setCheckable(True)
        self.show_cursor.toggled.connect(self.show_cursor_toggled)
        self.fw.cursor_changed.connect(self.cursor_changed)
        self.addAction(self.show_cursor)

        rename = QAction("Rename...", self)
        rename.triggered.connect(self.rename_triggered)
        self.addAction(rename)

        export_img = QAction("Export Image...", self)
        export_img.triggered.connect(self.export_triggered)
        self.addAction(export_img)

    def show_legend_toggled(self, checked=False):
        if checked:
            self.fw.show_legend()
        else:
            self.fw.hide_legend()

    def legend_changed(self, state):
        self.show_legend.setChecked(state)

    def show_cursor_toggled(self, checked=False):
        if checked:
            self.fw.show_cursor()
        else:
            self.fw.hide_cursor()

    def cursor_changed(self, state):
        self.show_cursor.setChecked(state)

    def region_changed(self, state):
        self.show_region.setChecked(state)

    def channels_changed(self):
        # Clear all current menus
        for menu in self.channel_menus:
            self.channelsmenu.removeAction(menu.menuAction())
            menu.close()
        self.channelsmenu.clear()
        self.channel_menus = []

        # Menu for each current channel
        for channel in self.fw.channels:
            menu = ChannelContextMenu(channel, self.channelsmenu)
            self.channelsmenu.addMenu(menu)
            self.channel_menus.append(menu)

        self.channelsmenu.addSeparator()

        # "Show All Channels" action
        show_all = QAction("Show All Channels", self.channelsmenu)
        show_all.triggered.connect(self.show_all_triggered)
        self.channelsmenu.addAction(show_all)

    def rename_triggered(self, _checked=False):
        name, ok = QInputDialog.getText(
            self, 'Rename', 'New Name:', QLineEdit.Normal, self.fw.name)
        if ok:
            self.fw.rename(name)

    def export_triggered(self):
        with QApplication.instance().server.updates_paused():
            pixmap = self.fw.glw.grab()
            fname = QFileDialog.getSaveFileName(
                self, "Export as...", "", "Images (*.png *.jpg *.bmp)", "")
            if not fname:
                logger.info("No file provided, not saving image")
                return
            if os.path.splitext(fname)[1] == "":
                fname = fname + ".png"
            logger.info("Saving image to '%s'", fname[0])
            pixmap.save(fname[0])

    def show_all_triggered(self):
        logger.info("Showing all channels for FftWindow %s", self.fw.name)
        for channel in self.fw.channels:
            channel.show()
