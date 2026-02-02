import logging
import pyqtgraph as pg
from PySide6.QtCore import Signal

from .window import Window
from ..models.fft_channel import FftChannel
from .fft_viewbox import FftViewBox
from .plot_legend import PlotLegend
from .plot_cursor import PlotCursor

logger = logging.getLogger(__name__)


class FftWindow(Window):
    """
    Display FFTs of one or more channels.

    Manages a Dock, GraphicsLayoutWidget, PlotItem, FftViewBox, and contains
    many FftChannels.

    Signals:
    closed: emitted when the managed Dock closes, with argument self
    name_changed: emitted when the window is renamed
    channels_changed: emitted when the displayed channels change
    legend_changed: emitted when the legend visibility changes, with argument
                    True if legend is visible and False if not
    cursor_changed: emitted when the cursor visibility changes, with argument
                    True if cursor is visible and False if not
    """
    legend_changed = Signal(bool)
    cursor_changed = Signal(bool)

    def __init__(self, name, parent):
        """
        name: name to show in label
        parent: the TabDock to which this FftWindow belongs
        """
        super().__init__(name, parent)

        self.legend = None
        self.legend_offset = (30, 30)
        self.cursor = None
        self.cursor_label_pos = None

        self.glw = pg.GraphicsLayoutWidget()
        self.vb = FftViewBox(self)
        self.pi = pg.PlotItem(name=name, viewBox=self.vb)
        self.glw.addItem(self.pi, row=0, col=0)
        self.dock.addWidget(self.glw)

        # Set up the plot item with sensible defaults
        self.pi.setClipToView(False)
        self.pi.setDownsampling(auto=True)
        self.pi.setMouseEnabled(x=True, y=False)
        self.pi.hideButtons()
        self.vb.x_axis = self.pi.getAxis('bottom')
        self.vb.y_axis = self.pi.getAxis('left')
        self.vb.configure()

    def add_channel(self, dataset, channel_id, region, emit_changed=True):
        if self.channels and dataset != self.channels[0].dataset:
            logger.warning("Not adding channel from different dataset")
            return
        channel = FftChannel(dataset, channel_id, region, self)
        channel.show()
        self.channels.append(channel)
        if emit_changed:
            self.channels_changed.emit()
        channel.update_data()
        channel.update_range()

        # When adding the second channel, display a legend by default
        if len(self.channels) == 2:
            self.show_legend()

        return channel

    def remove_channel(self, channel):
        """
        Remove a channel from this FftWindow.
        channel: FftChannel instance to remove.
        """
        channel.clear_viewbox()
        super().remove_channel(channel)

    def remove_channel_id(self, channel_id):
        """
        Remove a channel from this FftWindow by its channel_id.
        """
        for channel in self.channels:
            if channel.channel_id == channel_id:
                channel.clear_viewbox()
                super().remove_channel(channel)
                break

    def channel_present(self, channel_id):
        """
        Check if a specified channel_id is already present in the FFT window.
        """
        return channel_id in (c.channel_id for c in self.channels)

    def show_legend(self):
        if not self.legend:
            logger.info("Showing legend for %s", self.name)
            self.legend = PlotLegend(parent=self, offset=self.legend_offset,
                                     show_numeric=False)
            self.legend_changed.emit(True)

    def hide_legend(self):
        if self.legend is not None:
            logger.info("Hiding legend for %s", self.name)
            self.legend.close()
            self.legend = None
            self.legend_changed.emit(False)
            self.legend_offset = (30, 30)

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

    def update_channel_data(self):
        """
        Triggers an update of the data for each live channel.
        """
        for channel in self.channels:
            if channel.live:
                channel.update_data()

    def serialise(self):
        logger.info("Serialising FftWindow %s", self.name)
        return {
            "name": self.name,
            "type": "fft",
            "legend": {
                "show": bool(self.legend),
                "offset": list(self.legend_offset),
                "show_numeric": self.numeric_in_legend,
            },
            "cursor": {
                "show": bool(self.cursor),
                "label_position": self.cursor_label_pos,
            },
            "channels": [c.serialise() for c in self.channels],
            "viewbox": self.vb.serialise(),
        }

    def deserialise(self, layout):
        self.rename(layout['name'], force=True)
        logger.info("Deserialising FftWindow %s", self.name)

        # Set legend offset before adding channels so that it is created in
        # the correct position when the second channel is added
        self.legend_offset = layout['legend']['offset']
        self.numeric_in_legend = layout['legend']['show_numeric']

        self.vb.deserialise(layout['viewbox'])
        self._update_viewboxes()

        for channel in layout['channels']:
            if channel['dataset'] not in self.app.datasets:
                logger.warning("Dataset '%s' not found", channel['dataset'])
                continue
            dataset = self.app.datasets[channel['dataset']]
            if channel['channel_id'] not in dataset.channels_by_id():
                logger.warning("Channel '%s' not found in dataset '%s'",
                               channel['channel_id'], channel['dataset'])
                continue
            fc = self.add_channel(dataset, channel['channel_id'])
            fc.deserialise(channel)

        if layout['legend']['show']:
            self.show_legend()
        else:
            self.hide_legend()

        self.cursor_label_pos = layout['cursor']['label_position']
        if layout['cursor']['show']:
            self.show_cursor()
        else:
            self.hide_cursor()
