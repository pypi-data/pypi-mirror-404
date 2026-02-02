import logging
import pyqtgraph as pg
from PySide6.QtCore import Signal

from .window import Window
from ..models.plot_channel import PlotChannel
from .plot_legend import PlotLegend
from .plot_region import PlotRegion
from .plot_cursor import PlotCursor
from .plot_viewbox import PlotViewBox

logger = logging.getLogger(__name__)


class PlotWindow(Window):
    """
    Manages a Dock, GraphicsLayoutWidget, and PlotItem,
    and contains many PlotChannels.

    Signals:
    closed: emitted when the managed Dock closes, with argument self.
    name_changed: emitted when the window is renamed
    channels_changed: emitted when the displayed channels change
    channel_list_changed: emitted when the available channels changes
    lenged_changed: emitted when the legend visibility changes, with argument
                    True if legend is visible and False if not
    cursor_changed: emitted when the cursor visibility changes, with argument
                    True if cursor is visible and False if not
    region_changed: emitted when the region visibility changes, with argument
                    True if region is visible and False if not
    """
    channel_list_changed = Signal()
    legend_changed = Signal(bool)
    cursor_changed = Signal(bool)
    region_changed = Signal(bool)

    def __init__(self, name, parent):
        """
        name: string name to show in label
        parent: the TabDock to which this PlotWindow belongs
        """
        super().__init__(name, parent)
        self.app.server.time_update.connect(self._server_time_update)

        self.legend = None
        self.legend_offset = (30, 30)
        self.numeric_in_legend = False

        self.cursor = None
        self.cursor_label_pos = None

        self.region = None
        self.region_label_pos = (30, 300)

        # Create the internal GraphicsWindow, PlotViewBox, and PlotItem
        # PlotItem gets a rowspan of 2 so that additional y-axes to the right
        # can be in row 0 while adding a dummy x-axis to row 1 to align them
        # correctly with the PlotItem's actual chart area.
        self.glw = pg.GraphicsLayoutWidget()
        self.vb = PlotViewBox(self)
        self.vbs = [self.vb]
        self.pi = pg.PlotItem(name=name, viewBox=self.vb)
        self.glw.addItem(self.pi, row=0, col=0, rowspan=2)
        self.dock.addWidget(self.glw)

        # Set up the plot item with some sensible defaults
        self.pi.setClipToView(False)
        self.pi.setDownsampling(auto=True)
        self.vb.x_axis = self.pi.getAxis('bottom')
        self.vb.y_axis = self.pi.getAxis('left')
        self.vb.set_x_units('s')
        self.vb.y_axis.enableAutoSIPrefix(False)
        self.vb.x_axis.enableAutoSIPrefix(False)
        self.vb.x_axis.setStyle(textFillLimits=[])
        self.pi.setMouseEnabled(x=False, y=False)
        self.pi.hideButtons()

        # Prevent overlapping x-axis labels in recent pyqtgraph
        self.pi.getAxis('bottom').setStyle(
            autoExpandTextSpace=True, hideOverlappingLabels=True,
            textFillLimits=[(0, 0.8)])

        # Keep a monotonic counter for adding more axes
        self.x_axis_next_row = 2
        self.y_axis_next_col = 1

        # We need to update all child PlotViewBox when the main one resizes
        self.vb.sigResized.connect(self._update_viewboxes)

    def add_channel(self, dataset, channel_id, emit_changed=True, vb_idx=None):
        """
        Start displaying a new PlotChannel inside this PlotWindow.
        dataset: dataset containing channel to add
        channel_id: ID of channel in given dataset
        emit_changed: whether to emit channels_changed when adding this
                      channel (if False, the caller should emit it instead
                      after adding a batch of channels).
        vb_idx: if not None, the index of an existing PlotViewBox to add this
                channel to (used for deserialisation).
        """
        cfg = dataset.get_channel_config(channel_id)
        units = cfg['units']

        if self.channels and dataset != self.channels[0].dataset:
            logger.warning("Not adding channel from different dataset")
            return

        if vb_idx is not None:
            # Handle deserialising channels to existing PlotViewBoxes
            vb = self.vbs[vb_idx]
        elif self.vb.y_units is None:
            # Handle first channel
            logger.info("Initialising first vb for units '%s'", units)
            self.vb.set_y_units(units)
            vb = self.vb
        else:
            for vb in self.vbs:
                # Handle channels with existing units
                if units == vb.y_units:
                    logger.info("Reusing existing vb for units '%s'", units)
                    break
            else:
                # Handle channels with new units
                logger.info("Creating new vb for units '%s'", units)
                vb = self._new_y_axis(units)

        channel = PlotChannel(dataset, channel_id, self, vb)
        channel.show()

        if channel.dataset not in self.datasets:
            self.datasets.append(channel.dataset)
            channel.dataset.channels_changed.connect(self.channel_list_changed)

        # Set defaults for file plots
        if not self.channels and not channel.live:
            # Manual with mouse for first window, otherwise link
            if (self not in self.parent.windows or
                    self.parent.windows.index(self) == 0):
                vb.set_x_mode("manual")
                vb.set_x_mouse(True)
            else:
                vb.set_x_mode("link", link_idx=0)

        self.channels.append(channel)
        if emit_changed:
            self.channels_changed.emit()

        # When adding a second channel, display a legend by default
        if len(self.channels) == 2:
            self.show_legend()

        return channel

    def remove_channel(self, channel):
        """
        Remove a channel from this PlotWindow.
        channel: PlotChannel instance to remove.
        """
        channel.clear_viewbox()
        idx = self.vbs.index(channel.vb)
        if self.channel_units_unique(channel) and idx != 0:
            self._remove_y_axis(idx)

        super().remove_channel(channel)

    def separate_channel_y_axis(self, channel):
        """
        Remove the given channel from its current y-axis and corresponding
        viewbox, create a new y-axis with the same units, and add the channel
        to that one instead.
        """
        logger.info("Separating y-axis for channel %s", channel.channel_id)
        if self.channel_units_unique(channel):
            logger.info("Not separating already unique channel")
            return
        vb = self._new_y_axis(channel.units)
        channel.update_viewbox(vb)

    def show_legend(self):
        if not self.legend:
            logger.info("Showing legend for %s", self.name)
            self.legend = PlotLegend(parent=self, offset=self.legend_offset,
                                     show_numeric=self.numeric_in_legend)
            self.legend_changed.emit(True)

    def hide_legend(self):
        if self.legend is not None:
            logger.info("Hiding legend for %s", self.name)
            self.legend.close()
            self.legend = None
            self.legend_changed.emit(False)
            self.legend_offset = (30, 30)

    def set_numeric_in_legend(self, enabled):
        self.numeric_in_legend = enabled
        self.hide_legend()
        self.show_legend()

    def show_cursor(self):
        if self.cursor is not None:
            logger.info("Not showing already visible cursor")
            return
        logger.info("Showing cursor for %s", self.name)
        # Place cursor in the middle of the currently displayed X range
        vb_xrange = self.vb.viewRange()[0]
        cursor_pos = (vb_xrange[0] + vb_xrange[1]) / 2 + 0.1
        self.cursor = PlotCursor(
            pos=cursor_pos, label_pos=self.cursor_label_pos, pw=self)
        self.pi.addItem(self.cursor)
        self.cursor_changed.emit(True)

    def hide_cursor(self):
        if self.cursor is None:
            logger.info("Not hiding already hidden cursor")
            return
        logger.info("Hiding cursor for %s", self.name)
        self.pi.removeItem(self.cursor)
        self.cursor = None
        self.cursor_changed.emit(False)

    def show_region(self, label_pos=None):
        if self.region is not None:
            logger.info("Not showing already visible region")
            return
        logger.info("Showing region for %s", self.name)
        xleft, xright = self.vb.viewRange()[0]
        centre = (xleft + xright) / 2
        span = xright - xleft
        left = centre - span/8
        right = centre + span/8
        if label_pos is None:
            height = self.pi.viewGeometry().height()
            self.region_label_pos = (30, height//2)
        else:
            self.region_label_pos = label_pos
        self.region = PlotRegion((left, right), self.region_label_pos, self)
        self.pi.addItem(self.region)
        self.region_changed.emit(True)

    def hide_region(self):
        if self.region is None:
            logger.info("Not hiding already hidden region")
            return
        logger.info("Hiding region for %s", self.name)
        self.pi.removeItem(self.region)
        self.region.label.close()
        del self.region.label
        self.region = None
        self.region_changed.emit(False)

    def channel_units_unique(self, channel):
        """
        Returns True if the channel is the only one on its viewbox
        with its units.
        """
        other_units = [c.units for c in self.channels
                       if c != channel and c.vb == channel.vb]
        return channel.units not in other_units

    def update_channel_data(self):
        """
        Triggers an update of the data for each live channel. Used when the
        x-mode changes to cause channels to update their available data.
        """
        update_time = False
        for channel in self.channels:
            if channel.live:
                channel.update_data()
                update_time = True
        if update_time:
            self._server_time_update(self.app.server.get_time())

    def set_vbs_x_last_n_secs(self, last_n):
        """
        Sets the x_last_n_secs for all viewboxes.
        """
        for vb in self.vbs:
            vb.set_x_last_n_secs(last_n)

    def viewbox_idx(self, vb):
        """
        Get the index in the viewbox list of the provided viewbox.

        Used by PlotChannels when serialising to determine the index of
        their own viewbox.
        """
        return self.vbs.index(vb)

    def serialise(self):
        """
        Serialise this PlotWindow to a format which can be used to reconstruct
        it and its child PlotChannels.
        """
        logger.info("Serialising PlotWindow %s", self.name)
        if self.region:
            region_measurements = self.region.measurements_enabled
        else:
            region_measurements = {}
        return {
            "name": self.name,
            "type": "plot",
            "legend": {
                "show": bool(self.legend),
                "offset": list(self.legend_offset),
                "show_numeric": self.numeric_in_legend,
            },
            "cursor": {
                "show": bool(self.cursor),
                "label_position": self.cursor_label_pos,
            },
            "region": {
                "show": bool(self.region),
                "label_position": list(self.region_label_pos),
                "measurements": region_measurements,
            },
            "channels": [c.serialise() for c in self.channels],
            "viewboxes": [vb.serialise() for vb in self.vbs],
        }

    def deserialise(self, layout):
        """
        Restore state from a saved layout.
        layout: an item from the `windows` list in a layout.
        """
        self.rename(layout['name'], force=True)
        logger.info("Deserialising PlotWindow %s", self.name)

        # Set legend offset before adding channels so that it is created in
        # the correct position when the second channel is added
        self.legend_offset = layout['legend']['offset']
        self.numeric_in_legend = layout['legend']['show_numeric']

        # Restore viewboxes
        for idx, viewbox in enumerate(layout['viewboxes']):
            if idx == 0:
                self.vb.deserialise(viewbox)
            else:
                vb = PlotViewBox(self)
                self.vbs.append(vb)
                self.glw.scene().addItem(vb)
                if viewbox['twinx']:
                    vb.twinx(self.vb, self.vb.y_units)
                elif viewbox['twiny']:
                    logger.error("Can't deserialise twiny viewboxes yet")
                vb.deserialise(viewbox)
        self._update_viewboxes()

        # Create all the required channels
        for channel in layout['channels']:
            if channel['dataset'] not in self.app.datasets:
                logger.warning("Dataset '%s' not found", channel['dataset'])
                continue
            dataset = self.app.datasets[channel['dataset']]
            if channel['channel_id'] not in dataset.channels_by_id():
                logger.warning("Channel '%s' not found in dataset '%s'",
                               channel['channel_id'], channel['dataset'])
                continue
            idx = channel['viewbox_idx']
            pc = self.add_channel(dataset, channel['channel_id'], vb_idx=idx,
                                  emit_changed=False)
            pc.deserialise(channel)

        # Update after potentially adding several new channels
        self.channels_changed.emit()

        # Restore legend state
        if layout['legend']['show']:
            self.show_legend()
        else:
            self.hide_legend()

        # Restore cursor state
        self.cursor_label_pos = layout['cursor']['label_position']
        if layout['cursor']['show']:
            self.show_cursor()
        else:
            self.hide_cursor()

        # Restore region state
        if layout['region']['show']:
            self.show_region(layout['region']['label_position'])
            for m, en in layout['region'].get('measurements', {}).items():
                self.region.set_measurement_enabled(m, en)
        else:
            self.hide_region()

    def _server_time_update(self, time):
        if self.vb.x_mode == "last_n":
            positions = self._save_cursor_region_positions()
            if self.app.server.live_data.t_offset is not None:
                time -= self.app.server.live_data.t_offset
            self.pi.setXRange(time - self.vb.x_last_n_secs, time, padding=0)
            self._restore_cursor_region_positions(positions)
        if self.legend is not None and self.numeric_in_legend:
            self.legend.update_current_values()

    def _save_cursor_region_positions(self):
        """
        Before the XRange is updated, call this method to get the current
        cursor or region positions in screen coordinates, so that after the
        update they can be restored to the correct position.
        Used when in last_n mode or linked to another chart which is
        in last_n mode.
        """
        cursor_x2 = region_x2 = None
        if self.cursor is not None or self.region is not None:
            mapping = self.vb.childTransform()
            if self.cursor is not None:
                cursor_x = self.cursor.getXPos()
                cursor_x2 = mapping.map(cursor_x, 0.0)[0]
            if self.region is not None:
                region_x = self.region.getRegion()
                region_x2 = (mapping.map(region_x[0], 0.0)[0],
                             mapping.map(region_x[1], 0.0)[0])
        return (cursor_x2, region_x2)

    def _restore_cursor_region_positions(self, saved):
        """
        Puts the cursor and region back at their old screen positions.
        `saved` the return value from `_save_cursor_region_positions`.
        """
        cursor_x2, region_x2 = saved
        if cursor_x2 is not None or region_x2 is not None:
            mapping = pg.functions.invertQTransform(self.vb.childTransform())
            if self.cursor is not None and cursor_x2 is not None:
                cursor_x = mapping.map(cursor_x2, 0.0)[0]
                self.cursor.setPos(cursor_x)
            if self.region is not None and region_x2 is not None:
                region_x = (mapping.map(region_x2[0], 0.0)[0],
                            mapping.map(region_x2[1], 0.0)[0])
                self.region.setRegion(region_x)

    def _update_viewboxes(self):
        rect = self.vb.sceneBoundingRect()
        for vb in self.vbs[1:]:
            vb.setGeometry(rect)

    def _new_y_axis(self, units):
        vb = PlotViewBox(self)
        self.vbs.append(vb)
        self.glw.scene().addItem(vb)
        vb.twinx(self.vb, units)
        self._update_viewboxes()
        return vb

    def _remove_y_axis(self, idx):
        """
        Remove the viewbox and y-axis corresponding to the given index.
        """
        if idx == 0:
            # Don't remove the main y-axis.
            return
        vb = self.vbs[idx]
        axis = vb.y_axis
        self.glw.scene().removeItem(vb)
        self.glw.removeItem(axis)
        del self.vbs[idx]
