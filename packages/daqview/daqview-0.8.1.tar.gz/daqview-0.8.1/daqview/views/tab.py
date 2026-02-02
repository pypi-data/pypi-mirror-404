import logging
from collections import defaultdict
from PySide6.QtWidgets import (QWidget, QGridLayout, QApplication, QMenu,
                               QMessageBox)
from PySide6.QtGui import QAction

from .tab_dock import TabDock
from ..models.units import quantity_for_unit

logger = logging.getLogger(__name__)


class Tab(QWidget):
    """
    Abstract tab in the main user interface.

    May be either a LiveTab for viewing live-updating data,
    or a FileTab for viewing historic data.
    """
    def __init__(self, dataset):
        """
        dataset: the Dataset that this tab primarily represents.
        """
        super().__init__()
        self.dataset = dataset
        self.name = self.dataset.name()
        self.app = QApplication.instance()
        self.init_ui()

    def init_ui(self, is_live_tab=False):
        grid = QGridLayout(self)
        self.setLayout(grid)

        # Create TabDock for main display
        self.dock = TabDock(is_live_tab)
        grid.addWidget(self.dock.dock_area, 0, 0)

    def set_channel_chart_menus(self, add_menu):
        """
        Adds a QMenu for each group of channels in the dataset to the
        given menu, with actions bound appropriately to add a new
        chart for the selected channel.
        """
        self._set_channel_menus(
            add_menu, self.add_channel_chart, self.add_group_chart)

    def set_channel_readout_menus(self, add_menu):
        """
        Adds a QMenu for each group of channels in the dataset to the
        given menu, with actions bound appropriately to add a new
        readout for the selected channel.
        """
        self._set_channel_menus(
            add_menu, self.add_channel_readout, self.add_group_readout)

    def _set_channel_menus(self, add_menu, channel_slot, group_slot):
        # Shortcut if we don't have any channels
        if not self.dataset.channels:
            action = QAction("No channels available", add_menu)
            action.setEnabled(False)
            add_menu.addAction(action)
            return

        # Gather all the channels into a dict of groups
        groups = self.dataset.channels_by_group()

        # Make a menu for each group
        final_groups = ['ungrouped']
        if 'derived' in groups:
            final_groups.insert(0, 'derived')
        group_list = sorted(list(set(groups.keys()) - set(final_groups)))
        for group_id in (group_list + final_groups):
            group_name = self.dataset.get_group_name(group_id)
            menu = QMenu(group_name, add_menu)

            # Add 'Add Entire Group' action
            action = QAction("Add Entire Group", menu)

            def wrapper(*args, g=group_id):
                return group_slot(g)

            action.triggered.connect(wrapper)
            menu.addAction(action)
            menu.addSeparator()

            # Add action for each channel
            for channel in sorted(groups[group_id], key=lambda x: x['name']):
                action = QAction(
                    "{} ({})".format(channel['name'], channel['units']), menu)

                def wrapper(*args, c=channel):
                    return channel_slot(c['id'])

                action.triggered.connect(wrapper)
                menu.addAction(action)

            if group_id == final_groups[0]:
                add_menu.addSeparator()

            add_menu.addMenu(menu)

    def add_channel_chart(self, channel_id):
        """
        Slot which is called by the "Add Channel" actions
        when adding charts.
        """
        channel_cfg = self.dataset.get_channel_config(channel_id)
        window = self.dock.new_plot_window(channel_cfg['name'])
        window.add_channel(self.dataset, channel_id)

    def add_group_chart(self, group_id):
        """
        Slot which is called by the "Add Entire Group" action
        when adding charts.
        """
        channels = self.dataset.channels_by_group()[group_id]
        group_name = self.dataset.get_group_name(group_id)

        if len(channels) > 15:
            confirm = QMessageBox.question(
                self, "Confirm Add Entire Group",
                "This group contains {} channels.<br/>"
                "Are you sure you want to add them all?".format(len(channels)),
                QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.No:
                return

        # For 'Ungrouped' we don't want to try and collect together channels
        if group_id == "ungrouped":
            for channel in channels:
                window = self.dock.new_plot_window(channel['name'])
                window.add_channel(self.dataset, channel['id'])
            return

        # Collect channels which have the same units
        units = defaultdict(list)
        for channel in channels:
            units[channel['units']].append(channel)

        # Add one new window for each unique unit
        for unit in units:
            if len(units) == 1:
                name = group_name
            else:
                qty = quantity_for_unit(unit)
                name = "{} {}s".format(group_name, qty)

            window = self.dock.new_plot_window(name)

            for channel in units[unit]:
                window.add_channel(
                    self.dataset, channel['id'], emit_changed=False)

            window.channels_changed.emit()

    def add_channel_readout(self, channel_id):
        """
        Slot which is called by the "Add Channel" actions
        when adding readouts.
        """
        channel_cfg = self.dataset.get_channel_config(channel_id)
        window = self.dock.new_readout_window(channel_cfg['name'])
        window.add_channel(self.dataset, channel_id)

    def add_group_readout(self, group_id):
        """
        Slot which is called by the "Add Entire Group" action
        when adding readouts.
        """
        channels = self.dataset.channels_by_group()[group_id]
        group_name = self.dataset.get_group_name(group_id)
        window = self.dock.new_readout_window(group_name)
        for channel in channels:
            window.add_channel(self.dataset, channel['id'], emit_changed=False)
        window.channels_changed.emit()

    def serialise(self):
        """
        Serialise this Tab's state and all its children (windows, channels,
        etc) to a dict that can be persisted to disk and restored from.
        """
        logger.info("Serialising Tab '%s'", self.name)
        return {
            "dataset": self.dataset.serialise(),
            "dock": self.dock.serialise(),
        }

    def deserialise(self, layout):
        """
        Restore this Tab's state from a given layout.
        """
        logger.info("Deserialising Tab '%s'", self.name)
        self.dock.deserialise(layout['dock'])

    def dock_channels_changed(self):
        """
        Implemented on LiveTabs.
        """
        pass


class LiveTab(Tab):
    """
    A Tab that views live data being streamed from a server.

    Maintains a reference to a LiveDataset in a Server and handles
    updating the channels being live streamed.
    """
    def __init__(self):
        self.app = QApplication.instance()
        super().__init__(self.app.server.live_data)
        self.dock.channels_changed.connect(self.dock_channels_changed)

    def init_ui(self):
        super().init_ui(is_live_tab=True)

    def add_group_chart(self, group_id):
        # Overridden from base class to disconnect the dock.channels_changed
        # signal before adding channels then re-connect afterwards, to avoid
        # triggering it multiple times causing server.set_live_channels
        # to dis/reconnect the websocket for each channel in the group.
        self.dock.channels_changed.disconnect(self.dock_channels_changed)

        super().add_group_chart(group_id)

        self.dock_channels_changed()
        self.dock.channels_changed.connect(self.dock_channels_changed)

    def add_group_readout(self, group_id):
        # See add_group_chart
        self.dock.channels_changed.disconnect(self.dock_channels_changed)

        super().add_group_readout(group_id)

        self.dock_channels_changed()
        self.dock.channels_changed.connect(self.dock_channels_changed)

    def dock_channels_changed(self):
        logger.info("Dock channels changed, updating live channels")
        live_channels = self.dock.live_channels()
        self.app.server.set_live_channels(live_channels)

    def deserialise(self, layout):
        if not layout['dataset']['live']:
            logger.error("Cannot restore non-live dataset to live tab.")
            return
        logger.info("Deserialising Tab '%s'", self.name)
        hostname = layout['dataset']['filename']
        if not self.app.server.connected or self.app.server.host != hostname:
            logger.info("Connecting to server %s from layout file", hostname)
            self.app.server.disconnect_from_host()
            self.app.server.connect_to_host(hostname)
        self.dock.channels_changed.disconnect(self.dock_channels_changed)
        self.dock.deserialise(layout['dock'])
        self.dock_channels_changed()
        self.dock.channels_changed.connect(self.dock_channels_changed)


class FileTab(Tab):
    """
    A Tab that views historic data loaded from a file.

    Maintains its own FileDataset.
    """
    def closeEvent(self, ev):
        self.dataset.close()
        ev.accept()
