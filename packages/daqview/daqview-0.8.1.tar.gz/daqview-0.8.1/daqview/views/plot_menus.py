import logging
import os.path
import numpy as np
from types import MethodType
from PySide6.QtWidgets import (QWidgetAction, QWidget, QLineEdit,
                               QLabel, QVBoxLayout, QHBoxLayout, QRadioButton,
                               QCheckBox, QComboBox, QInputDialog, QFileDialog,
                               QMenu, QApplication, QColorDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class PlotContextXAxis(QWidget):
    """
    Custom QWidget for the plot x-axis context menu.
    """
    def __init__(self, parent):
        """
        `parent`: the parent PlotContextMenu
        """
        super().__init__(parent)
        self.vb = parent.vb
        self.pw = parent.pw
        self.init_ui()
        self.update_window_list()
        self.update_ui_state()

        self.mode_last_n.toggled.connect(self.mode_changed)
        self.last_n.editingFinished.connect(self.last_n_edited)
        self.mode_all.toggled.connect(self.mode_changed)
        self.mode_link.toggled.connect(self.mode_changed)
        self.link_to.currentIndexChanged[int].connect(self.link_to_changed)
        self.mode_manual.toggled.connect(self.mode_changed)
        self.manual_from.editingFinished.connect(self.manual_edited)
        self.manual_to.editingFinished.connect(self.manual_edited)
        self.pw.parent.windows_changed.connect(self.update_window_list)
        self.mouse.stateChanged.connect(self.mouse_changed)
        self.grid.stateChanged.connect(self.grid_changed)
        self.vb.sigXRangeChanged.connect(self.range_changed)
        parent.aboutToShow.connect(self.update_ui_state)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.mode_last_n = QRadioButton("Last", self)
        self.last_n = QLineEdit(self)
        self.last_n.setMaxLength(6)
        self.last_n.setMaximumWidth(self.last_n.minimumSizeHint().width() * 2)
        self.mode_last_n.toggled.connect(self.last_n.setEnabled)
        self.last_n_lbl = QLabel("seconds", self)
        hbox = QHBoxLayout()
        hbox.addWidget(self.mode_last_n)
        hbox.addWidget(self.last_n)
        hbox.addWidget(self.last_n_lbl)
        hbox.addStretch()
        self.layout.addLayout(hbox)

        self.mode_all = QRadioButton("All Time", self)
        self.layout.addWidget(self.mode_all)

        hbox = QHBoxLayout()
        self.mode_link = QRadioButton("Link:", self)
        self.link_to = QComboBox()
        hbox.addWidget(self.mode_link)
        hbox.addWidget(self.link_to)
        hbox.addStretch()
        self.layout.addLayout(hbox)

        self.mode_manual = QRadioButton("Manual:", self)
        self.manual_from = QLineEdit(self)
        self.manual_from.setMaximumWidth(
            self.manual_from.minimumSizeHint().width() * 3)
        manual_to_lbl = QLabel("to", self)
        self.manual_to = QLineEdit(self)
        self.manual_to.setMaximumWidth(
            self.manual_to.minimumSizeHint().width() * 3)
        self.mode_manual.toggled.connect(self.manual_from.setEnabled)
        self.mode_manual.toggled.connect(self.manual_to.setEnabled)
        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignLeft)
        hbox.addWidget(self.mode_manual)
        hbox.addWidget(self.manual_from)
        hbox.addWidget(manual_to_lbl)
        hbox.addWidget(self.manual_to)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        QWidget.setTabOrder(self.manual_from, self.manual_to)

        self.mouse = QCheckBox("Enable Mouse (manual only)", self)
        self.layout.addWidget(self.mouse)

        self.grid = QCheckBox("Show Grid", self)
        self.layout.addWidget(self.grid)

    def update_ui_state(self):
        # Set link index before changing mode to avoid the mode change
        # triggering a callback which will wipe out the link index.
        if self.vb.get_x_link_idx() is not None:
            item_idx = self.link_to.findData(self.vb.get_x_link_idx())
            self.link_to.setCurrentIndex(item_idx)

        # Only enable "Last n seconds" when displaying live channels
        if self.pw.live_channels():
            self.mode_last_n.setEnabled(True)
        else:
            self.mode_last_n.setEnabled(False)

        self.mode_last_n.setChecked(self.vb.get_x_mode() == "last_n")
        self.last_n.setText(str(self.vb.get_x_last_n_secs()))
        self.mode_all.setChecked(self.vb.get_x_mode() == "all")
        self.mode_link.setChecked(self.vb.get_x_mode() == "link")
        self.link_to.setEnabled(self.vb.get_x_mode() == "link")
        self.mode_manual.setChecked(self.vb.get_x_mode() == "manual")
        if self.vb.get_x_mode() == "manual":
            self.manual_from.setText(str(self.vb.get_x_manual_from()))
            self.manual_to.setText(str(self.vb.get_x_manual_to()))
            self.manual_from.setCursorPosition(0)
            self.manual_to.setCursorPosition(0)
        self.manual_from.setEnabled(self.vb.get_x_mode() == "manual")
        self.manual_to.setEnabled(self.vb.get_x_mode() == "manual")
        self.mouse.setEnabled(self.vb.get_x_mode() == "manual")
        self.mouse.setChecked(self.vb.get_x_mouse())
        self.grid.setChecked(self.vb.get_x_grid())

    def mode_changed(self, _checked):
        if self.mode_last_n.isChecked():
            self.vb.set_x_mode("last_n")
        elif self.mode_all.isChecked():
            self.vb.set_x_mode("all")
        elif self.mode_link.isChecked():
            item_idx = self.link_to.currentIndex()
            link_idx = self.link_to.itemData(item_idx)
            self.vb.set_x_mode("link", link_idx)
        else:
            self.vb.set_x_mode("manual")
            self.vb.set_x_mouse(True)
            self.mouse.setChecked(True)
            self.manual_edited()
        self.update_ui_state()

    def last_n_edited(self):
        try:
            last_n = float(self.last_n.text())
        except ValueError:
            last_n = 60.0
            self.last_n.setText("60")
        else:
            self.pw.set_vbs_x_last_n_secs(last_n)

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

    def link_to_changed(self, item_idx):
        link_idx = self.link_to.itemData(item_idx)
        if self.vb.get_x_mode() != "link" or link_idx == -1:
            self.vb.set_x_link_idx(None)
        else:
            self.vb.set_x_link_idx(link_idx)

    def range_changed(self, _vb, viewrange):
        xmin, xmax = viewrange
        self.manual_from.setText(str(xmin))
        self.manual_to.setText(str(xmax))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)

    def update_window_list(self):
        self.link_to.clear()
        for idx, window in enumerate(self.pw.parent.windows):
            if hasattr(window, "vb") and window != self.pw:
                self.link_to.addItem(window.name, idx)


class PlotContextYAxis(QWidget):
    """
    Custom QWidget for the plot y-axis context menu.
    """
    def __init__(self, parent):
        """
        `parent`: the parent PlotContextMenu
        """
        super().__init__(parent)
        self.vb = parent.vb
        self.pw = parent.pw
        self.init_ui()
        self.update_ui_state()

        self.mode_auto_vis.toggled.connect(self.mode_changed)
        self.mode_auto_all.toggled.connect(self.mode_changed)
        self.mode_manual.toggled.connect(self.mode_changed)
        self.manual_from.editingFinished.connect(self.manual_edited)
        self.manual_to.editingFinished.connect(self.manual_edited)
        self.mouse.stateChanged.connect(self.mouse_changed)
        self.grid.stateChanged.connect(self.grid_changed)
        self.autosi.stateChanged.connect(self.autosi_changed)
        self.vb.sigYRangeChanged.connect(self.range_changed)
        self.units_box.editingFinished.connect(self.units_edited)
        self.scale_box.editingFinished.connect(self.scale_edited)
        self.offset_box.editingFinished.connect(self.offset_edited)
        parent.aboutToShow.connect(self.update_ui_state)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.mode_auto_vis = QRadioButton("Autorange Visible Data", self)
        self.layout.addWidget(self.mode_auto_vis)

        self.mode_auto_all = QRadioButton("Autorange All Data", self)
        self.layout.addWidget(self.mode_auto_all)

        self.mode_manual = QRadioButton("Manual:", self)
        self.manual_from = QLineEdit(self)
        self.manual_from.setMaximumWidth(
            self.manual_from.minimumSizeHint().width() * 3)
        self.manual_to = QLineEdit(self)
        self.manual_to.setMaximumWidth(
            self.manual_to.minimumSizeHint().width() * 3)
        manual_to_lbl = QLabel("to", self)
        self.mode_manual.toggled.connect(self.manual_to.setEnabled)
        self.mode_manual.toggled.connect(self.manual_from.setEnabled)
        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignLeft)
        hbox.addWidget(self.mode_manual)
        hbox.addWidget(self.manual_from)
        hbox.addWidget(manual_to_lbl)
        hbox.addWidget(self.manual_to)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        QWidget.setTabOrder(self.manual_from, self.manual_to)

        self.mouse = QCheckBox("Enable Mouse (manual only)", self)
        self.layout.addWidget(self.mouse)

        self.grid = QCheckBox("Show Grid", self)
        self.layout.addWidget(self.grid)

        self.autosi = QCheckBox("Automatic SI prefix", self)
        self.layout.addWidget(self.autosi)

        self.units_box = QLineEdit(self)
        units_lbl = QLabel("Units:", self)
        hbox = QHBoxLayout()
        hbox.addWidget(units_lbl)
        hbox.addWidget(self.units_box)
        hbox.addStretch()
        self.layout.addLayout(hbox)

        self.scale_box = QLineEdit(self)
        scale_lbl = QLabel("Scale:", self)
        self.offset_box = QLineEdit(self)
        offset_lbl = QLabel("Offset:", self)
        hbox = QHBoxLayout()
        hbox.addWidget(scale_lbl)
        hbox.addWidget(self.scale_box)
        hbox.addWidget(offset_lbl)
        hbox.addWidget(self.offset_box)
        hbox.addStretch()
        self.layout.addLayout(hbox)

    def update_ui_state(self):
        self.mode_auto_vis.setChecked(self.vb.get_y_mode() == "auto_vis")
        self.mode_auto_all.setChecked(self.vb.get_y_mode() == "auto_all")
        self.mode_manual.setChecked(self.vb.get_y_mode() == "manual")
        if self.vb.get_y_mode() == "manual":
            self.manual_from.setText(str(self.vb.get_y_manual_from()))
            self.manual_to.setText(str(self.vb.get_y_manual_to()))
            self.manual_from.setCursorPosition(0)
            self.manual_to.setCursorPosition(0)
        self.manual_from.setEnabled(self.vb.get_y_mode() == "manual")
        self.manual_to.setEnabled(self.vb.get_y_mode() == "manual")
        self.mouse.setEnabled(self.vb.get_y_mode() == "manual")
        self.mouse.setChecked(self.vb.get_y_mouse())
        self.grid.setChecked(self.vb.get_y_grid())
        self.autosi.setChecked(self.vb.get_y_autosi())
        self.units_box.setText(self.vb.get_y_units())
        self.scale_box.setText(str(self.vb.get_y_scale()))
        self.offset_box.setText(str(self.vb.get_y_offset()))

    def mode_changed(self, _checked):
        if self.mode_auto_vis.isChecked():
            self.vb.set_y_mode("auto_vis")
        elif self.mode_auto_all.isChecked():
            self.vb.set_y_mode("auto_all")
        else:
            self.vb.set_y_mode("manual")
            self.vb.set_y_mouse(True)
            self.mouse.setChecked(True)
            self.manual_edited()
        self.update_ui_state()

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

    def autosi_changed(self, state):
        self.vb.set_y_autosi(bool(state))

    def range_changed(self, _vb, viewrange):
        ymin, ymax = viewrange
        self.manual_from.setText(str(ymin))
        self.manual_to.setText(str(ymax))
        self.manual_from.setCursorPosition(0)
        self.manual_to.setCursorPosition(0)
        self.vb.update_manual_y_range(float(ymin), float(ymax))

    def units_edited(self):
        self.vb.set_y_units(self.units_box.text())

    def scale_edited(self):
        try:
            scale = float(self.scale_box.text())
        except ValueError:
            pass
        else:
            self.vb.set_y_scale(scale)

    def offset_edited(self):
        try:
            offset = float(self.offset_box.text())
        except ValueError:
            pass
        else:
            self.vb.set_y_offset(offset)


class ChannelContextMenu(QMenu):
    """
    Context menu for an individual channel.
    """
    def __init__(self, channel, parent):
        """
        channel: the PlotChannel that corresponds to this context menu
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

        separate_y_axis = QAction("Separate Y Axis", self)
        separate_y_axis.triggered.connect(self.separate_y_axis_triggered)
        separate_y_axis.setEnabled(False)
        self.addAction(separate_y_axis)
        self.separate_y_axis = separate_y_axis

        zero_offset = QAction("Zero Offset...", self)
        zero_offset.triggered.connect(self.zero_offset_triggered)
        self.addAction(zero_offset)

        remove = QAction("Remove", self)
        remove.triggered.connect(self.remove_triggered)
        self.addAction(remove)

        self.addSeparator()

        if self.channel.live:
            self.show_minmax = QAction("Show Min/Max", self)
            self.show_minmax.setCheckable(True)
            self.show_minmax.toggled.connect(self.show_minmax_toggled)
            self.addAction(self.show_minmax)

            self.show_limits = QAction("Show Limit Lines", self)
            self.show_limits.setCheckable(True)
            self.show_limits.toggled.connect(self.show_limits_toggled)
            self.addAction(self.show_limits)

        self.about_to_show()

    def about_to_show(self):
        self.show_channel.setChecked(self.channel.show_channel)
        self.highlight.setChecked(self.channel.highlight)
        if self.channel.live:
            self.show_limits.setChecked(self.channel.show_limits)
            self.show_limits.setEnabled(self.channel.has_limits)
            self.show_minmax.setChecked(self.channel.show_minmax)
            self.show_minmax.setEnabled(self.channel.has_minmax)
        self.separate_y_axis.setDisabled(self.channel.units_unique())

    def show_channel_toggled(self, checked=False):
        if checked:
            self.channel.show()
        else:
            self.channel.hide()

    def highlight_channel_toggled(self, checked=False):
        self.channel.set_highlight(checked)

    def show_minmax_toggled(self, checked=False):
        self.channel.set_minmax(checked)

    def show_limits_toggled(self, checked=False):
        self.channel.set_limits(checked)

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

    def separate_y_axis_triggered(self):
        self.channel.separate_y_axis()

    def zero_offset_triggered(self):
        # Get the default value for zero-offset:
        # If one is already set, use that, otherwise, if there's a region
        # visible use the channel mean in the region, otherwise use the
        # first value in the channel.
        if self.channel.zero_offset is not None:
            v0 = self.channel.zero_offset
        elif self.channel.pw.region is not None:
            t0, t1 = self.channel.pw.region.getRegion()
            _, v = self.channel.values_for_times(t0, t1)
            v0 = np.mean(v)
        else:
            v0 = self.channel.first_value()
        z, ok = QInputDialog.getDouble(
            self, 'Zero Offset', 'Offset (0 to remove):', value=v0, decimals=3)
        if ok:
            self.channel.set_zero_offset(z)
        else:
            logger.info("Zero offset cancelled by user")

    def remove_triggered(self):
        self.channel.remove()


class PlotContextMenu(QMenu):
    """
    The right-click context menu on PlotWindows.
    """
    def __init__(self, vb):
        super().__init__()

        # Store refs to both the parent ViewBox and its parent PlotWindow
        self.vb = vb
        self.pw = vb.pw

        # Store child channel menus
        self.channel_menus = []

        self.init_ui()

    def init_ui(self):
        self.channelsmenu = QMenu("Channels", self)
        self.pw.channels_changed.connect(self.channels_changed)
        self.pw.channel_list_changed.connect(self.channels_changed)
        self.addMenu(self.channelsmenu)

        self.xmenu = QMenu("X Axis", self)
        self.xmenu_widget = PlotContextXAxis(self)
        self.xmenu_action = QWidgetAction(self.xmenu)
        self.xmenu_action.setDefaultWidget(self.xmenu_widget)
        self.xmenu.addAction(self.xmenu_action)
        self.addMenu(self.xmenu)

        self.xmenu.focusNextPrevChild = MethodType(
            QWidget.focusNextPrevChild, self.xmenu)

        self.ymenu = QMenu("Y Axis", self)
        self.ymenu_widget = PlotContextYAxis(self)
        self.ymenu_action = QWidgetAction(self.ymenu)
        self.ymenu_action.setDefaultWidget(self.ymenu_widget)
        self.ymenu.addAction(self.ymenu_action)
        self.addMenu(self.ymenu)

        self.ymenu.focusNextPrevChild = MethodType(
            QWidget.focusNextPrevChild, self.ymenu)

        self.show_legend = QAction("Legend", self)
        self.show_legend.setCheckable(True)
        self.show_legend.toggled.connect(self.show_legend_toggled)
        self.pw.legend_changed.connect(self.legend_changed)
        self.addAction(self.show_legend)

        self.numeric_in_legend = QAction("Readout In Legend", self)
        self.numeric_in_legend.setVisible(False)
        self.numeric_in_legend.setCheckable(True)
        self.numeric_in_legend.setEnabled(False)
        self.numeric_in_legend.setChecked(self.pw.numeric_in_legend)
        self.show_legend.toggled.connect(self.numeric_in_legend.setEnabled)
        self.numeric_in_legend.toggled.connect(self.numeric_in_legend_toggled)
        self.addAction(self.numeric_in_legend)

        self.show_cursor = QAction("Cursor", self)
        self.show_cursor.setCheckable(True)
        self.show_cursor.toggled.connect(self.show_cursor_toggled)
        self.pw.cursor_changed.connect(self.cursor_changed)
        self.addAction(self.show_cursor)

        self.show_region = QAction("Analysis Region", self)
        self.show_region.setCheckable(True)
        self.show_region.toggled.connect(self.show_region_toggled)
        self.pw.region_changed.connect(self.region_changed)
        self.addAction(self.show_region)

        rename = QAction("Rename...", self)
        rename.triggered.connect(self.rename_triggered)
        self.addAction(rename)

        export_img = QAction("Export Image...", self)
        export_img.triggered.connect(self.export_triggered)
        self.addAction(export_img)

    def show_legend_toggled(self, checked=False):
        if checked:
            self.pw.show_legend()
        else:
            self.pw.hide_legend()

    def numeric_in_legend_toggled(self, checked=False):
        self.pw.set_numeric_in_legend(checked)

    def legend_changed(self, state):
        self.show_legend.setChecked(state)
        self.numeric_in_legend.setChecked(self.pw.numeric_in_legend)

    def show_cursor_toggled(self, checked=False):
        if checked:
            self.pw.show_cursor()
        else:
            self.pw.hide_cursor()

    def cursor_changed(self, state):
        self.show_cursor.setChecked(state)

    def show_region_toggled(self, checked=False):
        if checked:
            self.pw.show_region()
        else:
            self.pw.hide_region()

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
        for channel in self.pw.channels:
            menu = ChannelContextMenu(channel, self.channelsmenu)
            self.channelsmenu.addMenu(menu)
            self.channel_menus.append(menu)

        self.channelsmenu.addSeparator()

        # "Show All Channels" action
        show_all = QAction("Show All Channels", self.channelsmenu)
        show_all.triggered.connect(self.show_all_triggered)
        self.channelsmenu.addAction(show_all)

        # "Add New Channel" menu
        self.addchannelmenu = QMenu("Add New Channel", self.channelsmenu)
        self.pw.set_add_channel_menu(self.addchannelmenu)
        self.channelsmenu.addMenu(self.addchannelmenu)

        # Enable 'Show Readout In Legend' if any channels are live
        if self.pw.live_channels():
            self.numeric_in_legend.setVisible(True)
        else:
            self.numeric_in_legend.setVisible(False)

    def rename_triggered(self, _checked=False):
        name, ok = QInputDialog.getText(
            self, 'Rename', 'New Name:', QLineEdit.Normal, self.pw.name)
        if ok:
            self.pw.rename(name)

    def export_triggered(self):
        with QApplication.instance().server.updates_paused():
            pixmap = self.pw.glw.grab()
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
        logger.info("Showing all channels for PlotWindow %s", self.pw.name)
        for channel in self.pw.channels:
            channel.show()
