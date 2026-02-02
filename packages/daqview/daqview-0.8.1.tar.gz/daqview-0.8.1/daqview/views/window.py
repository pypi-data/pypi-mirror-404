from types import MethodType
import logging
from pyqtgraph.dockarea import Dock
from PySide6.QtWidgets import QApplication, QMenu, QErrorMessage
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


# Patch DockLabel to prevent crash on right-click drag
def patch_docklabel(docklabel):
    original_mouseMoveEvent = docklabel.mouseMoveEvent

    def patched_mouseMoveEvent(self, ev):
        if not hasattr(self, 'pressPos'):
            self.pressPos = ev.pos()
        original_mouseMoveEvent(ev)

    docklabel.mouseMoveEvent = MethodType(patched_mouseMoveEvent, docklabel)


class Window(QObject):
    """
    Base class for PlotWindow and ReadoutWindow.

    Manages one Dock and {Plot,Readout}Widget, and many channels.

    Signals:
    closed: emitted when the managed Dock closes, with argument self.
    name_changed: emitted when the window is renamed
    channels_changed: emitted when the displayed channels change
    """
    closed = Signal(object)
    name_changed = Signal()
    channels_changed = Signal()

    def __init__(self, name, parent):
        """
        name: string name to show in label
        parent: the TabDock to which this ReadoutWindow belongs
        """
        super().__init__()
        self.app = QApplication.instance()
        self.name = name
        self.parent = parent
        self.channels = []
        self.datasets = []

        self.dock = Dock(name, closable=True, autoOrientation=False)
        patch_docklabel(self.dock.label)
        self.dock.sigClosed.connect(self._dock_closed)

        # Increase label font size
        font = self.dock.label.font()
        font.setPointSize(14)
        self.dock.label.setFont(font)

    def new_group(self, dataset, group_id):
        """
        Convenience function to add a whole group worth of new channels.
        """
        for channel in dataset.channels_by_group()[group_id]:
            if channel['id'] not in [c.channel_id for c in self.channels]:
                self.add_channel(dataset, channel['id'], emit_changed=False)
        self.channels_changed.emit()

    def remove_channel(self, channel):
        self.channels.remove(channel)
        self.channels_changed.emit()

    def rename(self, new_name, force=False):
        """
        Updates the name for this PlotWindow and its Dock and PlotItem.
        """
        if self.parent.allow_rename(new_name) or force:
            self.name = new_name
            self.dock._name = new_name
            self.dock.setTitle(new_name)
            self.name_changed.emit()
        else:
            error = QErrorMessage(self.dock)
            error.setModal(True)
            error.showMessage("Name already in use")

    def live_channels(self):
        """
        Returns a list of all channel_ids displayed in this PlotWindow which
        belong to a LiveDataset.
        """
        return sum((c.streaming_channel_ids() for c in self.channels), [])

    def set_add_channel_menu(self, menu):
        """
        Populates `menu` with submenus for each group of channels in the same
        dataset as the current channel, with actions bound to add those
        channels to this PlotWindow.

        Disables channels which are already present in this PlotWindow.

        See also Tab.set_channel_chart_menus

        In the future, update this to show submenus for each open tab/dataset,
        so that channels from other datasets can be added for comparison.
        """
        if not self.channels:
            action = QAction("No channels available", menu)
            action.setEnabled(False)
            menu.addAction(action)
            return

        dataset = self.channels[0].dataset

        # Quit early if we don't have any channels available
        if not dataset.channels:
            action = QAction("No channels available", menu)
            action.setEnabled(False)
            menu.addAction(action)
            return

        # Make a menu for each group, with Ungrouped stuck at the end
        groups = dataset.channels_by_group()
        final_groups = ['ungrouped']
        if 'derived' in groups:
            final_groups.insert(0, 'derived')
        group_list = sorted(list(set(groups.keys()) - set(final_groups)))
        for group_id in group_list + final_groups:
            group_name = dataset.get_group_name(group_id)
            group_menu = QMenu(group_name, menu)
            action = QAction("Add Entire Group", group_menu)

            def wrapper(*args, d=dataset, g=group_id):
                return self.new_group(d, g)

            action.triggered.connect(wrapper)
            group_menu.addAction(action)
            group_menu.addSeparator()

            for channel in sorted(groups[group_id], key=lambda x: x['name']):
                channel_id = channel['id']
                action = QAction(
                    "{} ({})".format(channel.get('name'), channel.get('units')),
                    group_menu)
                if channel_id in [c.channel_id for c in self.channels]:
                    action.setEnabled(False)

                def wrapper(*args, d=dataset, c=channel_id):
                    return self.add_channel(d, c)

                action.triggered.connect(wrapper)
                group_menu.addAction(action)

            if group_id == final_groups[0]:
                menu.addSeparator()

            menu.addMenu(group_menu)

    def close(self):
        self.dock.close()

    def serialise(self):
        raise NotImplementedError()

    def deserialise(self, layout):
        raise NotImplementedError()

    def _dock_closed(self, _dock):
        self.closed.emit(self)
        self.channels = []
