import logging
from PySide6.QtWidgets import (QMenu, QInputDialog, QLineEdit,
                               QFileDialog, QApplication)
from PySide6.QtGui import QAction

logger = logging.getLogger(__name__)


class ChannelContextMenu(QMenu):
    """
    Context menu for an individual channel.
    """
    def __init__(self, channel, parent):
        """
        channel: the ReadoutChannel that corresponds to this context menu
        parent: the QMenu to which this menu belongs
        """
        super().__init__(channel.get_name(), parent)
        self.channel = channel
        self.init_ui()

    def init_ui(self):
        highlight = QAction("Highlight", self)
        highlight.setCheckable(True)
        highlight.toggled.connect(self.highlight_toggled)
        self.addAction(highlight)

        remove = QAction("Remove", self)
        remove.triggered.connect(self.remove_triggered)
        self.addAction(remove)

    def remove_triggered(self):
        self.channel.remove()

    def highlight_toggled(self, checked=False):
        self.channel.set_highlight(checked)


class ReadoutContextMenu(QMenu):
    """
    Right-click context menu on a ReadoutWindow.
    """
    def __init__(self, rw):
        super().__init__()
        self.rw = rw

        self.channel_menus = []
        self.init_ui()

    def init_ui(self):
        self.channelsmenu = QMenu("Channels", self)
        self.rw.channels_changed.connect(self.channels_changed)
        self.addMenu(self.channelsmenu)

        rename = QAction("Rename...", self)
        rename.triggered.connect(self.rename_triggered)
        self.addAction(rename)

        export_img = QAction("Export Image...", self)
        export_img.triggered.connect(self.export_triggered)
        self.addAction(export_img)

    def channels_changed(self):
        # Clear all current menus
        for menu in self.channel_menus:
            self.channelsmenu.removeAction(menu.menuAction())
            menu.close()
        self.channelsmenu.clear()
        self.channel_menus = []

        # Menu for each current channel
        for channel in self.rw.channels:
            menu = ChannelContextMenu(channel, self.channelsmenu)
            self.channelsmenu.addMenu(menu)
            self.channel_menus.append(menu)

        # "Add New Channel" menu
        self.channelsmenu.addSeparator()
        self.addchannelmenu = QMenu("Add New Channel", self.channelsmenu)
        self.rw.set_add_channel_menu(self.addchannelmenu)
        self.channelsmenu.addMenu(self.addchannelmenu)

    def rename_triggered(self, _checked=False):
        name, ok = QInputDialog.getText(
            self, 'Rename', 'New Name:', QLineEdit.Normal, self.rw.name)
        if ok:
            self.rw.rename(name)

    def export_triggered(self):
        with QApplication.instance().server.pdates_paused():
            pixmap = self.rw.widget.grab()
            fname = QFileDialog.getSaveFileName(
                self, "Export as...", "", "Images (*.png, *.jpg, *.bmp)", "")
            logger.info("Saving image to '%s'", fname[0])
            pixmap.save(fname[0])
