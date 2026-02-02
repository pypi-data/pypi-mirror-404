import copy
import logging
import pyqtgraph as pg
import numpy as np

from .channel import Channel

logger = logging.getLogger(__name__)


class FftChannel(Channel):
    """
    Represents one channel of data inside an FftWindow.

    Manages one PlotDataItem.
    """
    def __init__(self, dataset, channel_id, region, fft_window):
        super().__init__(dataset, channel_id, fft_window)
        self.fw = fft_window
        self.vb = fft_window.vb
        self.pr = region
        self.show_channel = True
        self.highlight = False
        self.init_plotitems()
        self.pr.sigRegionChanged.connect(self.update_range)

    def init_plotitems(self):
        self.pdi = pg.PlotDataItem(name=self.name, pen=self.colour)
        self.update_data()
        self.pdi.setAlpha(*self.fw.pi.alphaState())
        self.pdi.setDownsampling(*self.fw.pi.downsampleMode())
        self.pdi.setVisible(True)
        self.vb.addItem(self.pdi)
        self.pdi.setClipToView(self.fw.pi.clipToViewMode())

    def update_viewbox(self, vb):
        self.clear_viewbox()
        self.vb = vb
        self.init_plotitems()

    def clear_viewbox(self):
        """Remove items belonging to this FftChannel from its ViewBox."""
        if self.pdi in self.vb.allChildren():
            self.vb.removeItem(self.pdi)

    def update_data(self):
        """
        Get latest data for this channel from its Dataset and update the
        corresponding plot items. Triggered by Dataset.data_updated.
        """
        self.time, self.data = self.dataset.get_channel_data(self.channel_id)

    def update_range(self):
        t0, t1 = self.pr.getRegion()
        time, data = self.values_for_times(t0, t1)
        if len(time) < 2:
            # Don't show anything if not enough data points to work out dt
            self.pdi.setData([], [])
            return
        dt = time[-1] - time[-2]
        mag = 10*np.log10(np.abs(np.fft.rfft(data)))
        freqs = np.fft.rfftfreq(data.size, d=dt)
        self.pdi.setData(freqs, mag)

    def show(self):
        """Show this channel on the FftWindow."""
        if self.show_channel:
            return
        logger.info("Showing channel %s", self.channel_id)
        self.show_channel = True
        self.pdi.setVisible(True)

    def hide(self):
        """Hide this channel on the FftWindow."""
        if not self.show_channel:
            return
        logger.info("Hiding channel %s", self.channel_id)
        self.show_channel = False
        self.pdi.setVisible(False)

    def hide_others(self):
        for channel in self.fw.channels:
            if channel != self:
                channel.hide()

    def set_highlight(self, highlight=True):
        width = 4 if highlight else 1
        self.highlight = highlight
        self.pdi.setPen({"color": self.colour, "width": width})

    def set_temporary_highlight(self, highlight=True):
        width = 6 if highlight else 1
        self.pdi.setPen({"color": self.colour, "width": width})
        for channel in self.fw.channels:
            if channel != self:
                channel.set_temporary_dim(highlight)

    def set_temporary_dim(self, dim=True):
        colour = copy.copy(pg.mkColor(self.colour))
        if dim:
            colour.setAlphaF(0.5)
        else:
            self.set_highlight(self.highlight)
        self.pdi.setPen({"color": colour, "width": 1})

    def update_colour(self, new_colour):
        super().update_colour(new_colour)
        self.pdi.setPen({"color": self.colour, "width": 1})

    def serialise(self):
        logger.info("Serialising channel %s", self.name)
        ser = super().serialise()
        ser.update({
            "show_channel": self.show_channel,
            "highlight": self.highlight,
        })
        return ser

    def deserialise(self, layout):
        logger.info("Deserialising channel %s", self.name)
        super().deserialise(layout)
        if not layout['show_channel']:
            self.hide()
        if layout.get('highlight', False):
            self.set_highlight(True)
