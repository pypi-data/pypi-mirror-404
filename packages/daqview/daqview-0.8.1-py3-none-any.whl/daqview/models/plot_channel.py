import copy
import logging
import pyqtgraph as pg

import numpy as np

from .channel import Channel
from .curve_fit import LinearCurveFit, SinusoidalCurveFit, ExponentialCurveFit

logger = logging.getLogger(__name__)

DS_RATE = 3000


class PlotChannel(Channel):
    """
    Represents one channel of data inside a PlotWindow.

    Manages a main PlotDataItem, and optionally additional items for
    showing min/max lines.
    """
    def __init__(self, dataset, channel_id, plot_window, viewbox):
        """
        dataset: the underlying Dataset which contains data for this channel
        channel_id: the channel id string
        plot_window: the parent plot_window this channel belongs to
        viewbox: the parent viewbox this channel will be rendered in
        """
        super().__init__(dataset, channel_id, plot_window)
        self.pw = plot_window
        self.vb = viewbox
        self.vb.scale_offset_changed.connect(self._set_data)
        self.vb.sigXRangeChanged.connect(self._set_data)
        self.redline = self.channel_cfg.get('redline')
        self.yellowline = self.channel_cfg.get('yellowline')
        self.has_limits = bool(self.redline or self.yellowline)
        self.has_minmax = self.dataset.live and "expr" not in self.channel_cfg

        self.show_channel = False
        self.show_minmax = False
        self.show_limits = False
        self.highlight = False

        self.fit = None
        self.fit_times = (0, 0)
        self.fit_autofit = True

        self.init_plotitems()

    def init_plotitems(self):
        # Create underlying PlotDataItem for this channel
        self.time, self.data = self.dataset.get_channel_data(self.channel_id)
        self.datamin = self.datamax = self.data
        start_empty = self.time.size < 2 or np.all(np.isnan(self.data))
        if start_empty:
            # If we don't yet have at least 2 points for this channel, we'll
            # create it with no data set, to prevent crashes if we'd given
            # it empty lists instead.
            self.pdi = pg.PlotDataItem(name=self.name, pen=self.colour)
        else:
            # If data does already exist we can create the PlotDataItem
            # with that data.
            self.pdi = pg.PlotDataItem(
                self.time, self.data, name=self.name, pen=self.colour)
            self.current_value = self.data[-1]
        self.pdi.setAlpha(*self.pw.pi.alphaState())
        self.pdi.setDownsampling(*self.pw.pi.downsampleMode())
        self.pdi.setVisible(True)
        self.vb.addItem(self.pdi)
        # Warning, we need to set clipToView _after_ adding the item to the
        # viewbox or pyqtgraph will crash out.
        self.pdi.setClipToView(self.pw.pi.clipToViewMode())

        # Clear PlotDataItem for a potential curve fit.
        self.pdi_fit = pg.PlotDataItem()
        self.pdi_fit.setPen({"color": self.colour, "width": 3})
        self.pdi_fit.setDownsampling(*self.pw.pi.downsampleMode())
        self.pdi_fit.setVisible(False)
        self.vb.addItem(self.pdi_fit)
        self.pdi_fit.setClipToView(self.pw.pi.clipToViewMode())

        if self.live:
            # Create PlotDataItems for min/max lines, and then a new item for
            # the fill in between them (which we might actually render)
            if start_empty:
                self.pdi_min = pg.PlotDataItem()
                self.pdi_max = pg.PlotDataItem()
            else:
                self.pdi_min = pg.PlotDataItem(self.time, self.data)
                self.pdi_max = pg.PlotDataItem(self.time, self.data)
            self.pdi_min.setDownsampling(*self.pw.pi.downsampleMode())
            self.pdi_max.setDownsampling(*self.pw.pi.downsampleMode())
            fill_brush = pg.mkBrush(self.colour)
            fill_colour = fill_brush.color()
            fill_colour.setAlpha(50)
            fill_brush.setColor(fill_colour)
            self.pdi_fill = pg.FillBetweenItem(
                self.pdi_min, self.pdi_max, pen=None, brush=fill_brush)
            self.pdi_fill.setVisible(self.show_minmax)
            self.vb.addItem(self.pdi_fill)

            # Create the limit lines we might show later
            self._redline_item = None
            self._yellowline_item = None
            if self.redline:
                self._redline_item = pg.InfiniteLine(
                    self.redline, angle=0, pen='r')
                self._redline_item.setVisible(self.show_limits)
                self.vb.addItem(self._redline_item)
            if self.yellowline:
                self._yellowline_item = pg.InfiniteLine(
                    self.yellowline, angle=0, pen='y')
                self._yellowline_item.setVisible(self.show_limits)
                self.vb.addItem(self._yellowline_item)

    def update_viewbox(self, vb):
        self.clear_viewbox()
        self.vb = vb
        self.init_plotitems()

    def clear_viewbox(self):
        """
        Remove items belonging to this PlotChannel from its current ViewBox.
        """
        if self.pdi in self.vb.allChildren():
            self.vb.removeItem(self.pdi)
        if self.live and self.pdi_fill in self.vb.allChildren():
            self.vb.removeItem(self.pdi_fill)
        if self.redline and self._redline_item in self.vb.allChildren():
            self.vb.removeItem(self._redline_item)
        if self.yellowline and self._yellowline_item in self.vb.allChildren():
            self.vb.removeItem(self._yellowline_item)
        if self.pdi_fit in self.vb.allChildren():
            self.vb.removeItem(self.pdi_fit)

    def update_data(self):
        """
        Gets latest data for this channel from its Dataset and updates
        the corresponding plot items. Triggered by Dataset.data_updated.
        """
        if self.live and self.show_minmax:
            self.time, self.data, self.datamin, self.datamax = \
                self.dataset.get_channel_data_minmax(self.channel_id)
        else:
            self.time, self.data = \
                self.dataset.get_channel_data(self.channel_id)
        self.current_value = self.data[-1]

        # If we're in last_n mode then the time update will trigger an x-axis
        # update which triggers _set_data, so don't do it twice.
        if self.vb.get_x_mode() != "last_n":
            self._set_data()

    def _set_data(self):
        """
        Update the PlotDataItem data by selecting a suitable range and
        downsample from our underlying data, then applying a scale and offset.
        """
        time, data = self.time, self.data
        if self.live and self.show_minmax:
            datamin, datamax = self.datamin, self.datamax

        ds = None

        # Cut down the dataset to roughly the points to be displayed
        if self.vb.get_x_mode() != "all":
            xmin, xmax = self.vb.get_x_range()
            imin = np.searchsorted(time, xmin, 'left')
            imax = np.searchsorted(time, xmax, 'right')
            imin = max(0, imin - 200)
            imax += 200
            # Shift imin so we always show the same downsampled points
            ds = max(1, (imax-imin)//DS_RATE)
            imin -= imin % ds
            imin = max(0, imin)
            time = time[imin:imax]
            data = data[imin:imax]
            if self.live and self.show_minmax:
                datamin = datamin[imin:imax]
                datamax = datamax[imin:imax]

        if time.size <= 3:
            return

        # Downsample to maintain at most 6000 points being displayed
        if ds is None:
            ds = max(1, data.size//DS_RATE)
        if ds > 1:
            time = time[::ds]
            data = data[::ds]
            if self.show_minmax:
                datamin = datamin[::ds]
                datamax = datamax[::ds]

        data = self._scale_offset_data(data)
        self.pdi.setData(time, data)

        # If we're showing min/max region too, scale and render those
        if self.live and self.show_minmax:
            datamin = self._scale_offset_data(datamin)
            datamax = self._scale_offset_data(datamax)
            self.pdi_min.setData(time, datamin)
            self.pdi_max.setData(time, datamax)

        self.update_fit()

    def update_fit(self):
        # If we're showing a fit, re-evaluate it on the new times.
        if self.fit is not None:
            t, _ = self.values_for_times(*self.fit_times)
            y = self._scale_offset_data(self.fit.evaluate(t))
            self.pdi_fit.setData(t, y)

    def _scale_offset_data(self, data):
        yscale = self.vb.get_y_scale()
        yoffset = self.vb.get_y_offset()
        if yscale != 1.0 and yoffset == 0.0:
            data = data * yscale
        elif yscale == 1.0 and yoffset != 0.0:
            data = data + yoffset
        elif yscale != 1.0 and yoffset != 0.0:
            data = data * yscale + yoffset
        if self.zero_offset is not None:
            data = data - self.zero_offset
        return data

    def show(self):
        """
        Show this channel's line, and also the minmax and limits if enabled.
        """
        if self.show_channel:
            return
        logger.info("Showing channel %s", self.channel_id)
        self.show_channel = True

        self.pdi.setVisible(True)
        if self.show_minmax:
            self.pdi_fill.setVisible(True)
        if self.show_limits:
            if self._redline_item:
                self._redline_item.setVisible(True)
            if self._yellowline_item:
                self._yellowline_item.setVisible(True)
        if self.fit is not None:
            self.pdi_fit.setVisible(True)

    def hide(self):
        """
        Hide this channel's line, and also the minmax and limits if enabled.
        """
        if not self.show_channel:
            return
        logger.info("Hiding channel %s", self.channel_id)
        self.show_channel = False
        self.pdi.setVisible(False)
        if self.show_minmax:
            self.pdi_fill.setVisible(False)
        if self.show_limits:
            if self._redline_item:
                self._redline_item.setVisible(False)
            if self._yellowline_item:
                self._yellowline_item.setVisible(False)
        if self.fit is not None:
            self.pdi_fit.setVisible(False)

    def hide_others(self):
        for channel in self.pw.channels:
            if channel != self:
                channel.hide()

    def set_fit_autofit(self, autofit=True):
        self.fit_autofit = autofit
        if autofit:
            self.fit.fit(*self.values_for_times(*self.fit_times))
            self.update_fit()

    def get_fit_autofit(self):
        return self.fit_autofit

    def set_fit_params(self, params):
        if self.fit is not None:
            self.fit.set_params(params)
            self.update_fit()

    def get_fit_params(self):
        if self.fit is not None:
            return self.fit.params()
        else:
            return {}

    def set_fit_none(self):
        logger.info("Hiding curve fit on channel %s", self.channel_id)
        self.pdi_fit.setVisible(False)
        self.fit = None

    def set_fit_linear(self, t0, t1):
        self.fit_times = (t0, t1)
        times, values = self.values_for_times(t0, t1)
        fit = LinearCurveFit()
        if self.fit_autofit:
            fit.fit(times, values)
        self._set_curve_fit(fit)

    def set_fit_sinusoidal(self, t0, t1):
        self.fit_times = (t0, t1)
        fit = SinusoidalCurveFit()
        if self.fit_autofit:
            times, values = self.values_for_times(t0, t1)
            fit.fit(times, values)
        self._set_curve_fit(fit)

    def set_fit_exponential(self, t0, t1):
        self.fit_times = (t0, t1)
        fit = ExponentialCurveFit()
        if self.fit_autofit:
            times, values = self.values_for_times(t0, t1)
            fit.fit(times, values)
        self._set_curve_fit(fit)

    def fit_region_changed(self, t0, t1):
        if self.fit:
            if self.fit_autofit:
                self.fit.fit(*self.values_for_times(t0, t1))
            self.fit_times = (t0, t1)
            self.update_fit()

    def _set_curve_fit(self, fit):
        logger.info("Showing curve fit on channel %s", self.channel_id)
        self.fit = fit
        self.pdi_fit.setVisible(True)
        self.update_fit()

    def set_highlight(self, highlight=True):
        width = 4 if highlight else 1
        self.highlight = highlight
        self.pdi.setPen({"color": self.colour, "width": width})

    def set_temporary_highlight(self, highlight=True):
        width = 6 if highlight else (4 if self.highlight else 1)
        self.pdi.setPen({"color": self.colour, "width": width})
        for channel in self.pw.channels:
            if channel != self:
                channel.set_temporary_dim(highlight)

    def set_temporary_dim(self, dim=True):
        colour = copy.copy(pg.mkColor(self.colour))
        if dim:
            colour.setAlphaF(0.5)
        else:
            self.set_highlight(self.highlight)
        self.pdi.setPen({"color": colour, "width": 1})
        self.pdi_fit.setPen({"color": colour, "width": 3})

    def update_colour(self, new_colour):
        super().update_colour(new_colour)
        self.pdi.setPen({"color": self.colour, "width": 1})
        self.pdi_fit.setPen({"color": self.colour, "width": 3})

    def separate_y_axis(self):
        self.pw.separate_channel_y_axis(self)

    def set_minmax(self, show_minmax):
        self.show_minmax = show_minmax
        if self.show_channel:
            if self.show_minmax:
                self.pdi_fill.setVisible(True)
            else:
                self.pdi_fill.setVisible(False)

    def set_limits(self, show_limits):
        self.show_limits = show_limits
        if self.show_channel:
            if self.show_limits:
                if self._redline_item:
                    self._redline_item.setVisible(True)
                if self._yellowline_item:
                    self._yellowline_item.setVisible(True)
            else:
                if self._redline_item:
                    self._redline_item.setVisible(False)
                if self._yellowline_item:
                    self._yellowline_item.setVisible(False)

    def units_unique(self):
        """
        Returns True if this channel is the only one with its units in its
        parent PlotWindow.
        """
        return self.pw.channel_units_unique(self)

    def formatted_value_with_units(self, time=None, value=None):
        units = self.vb.get_y_units()
        return self.formatted_value(time, value) + " " + units

    def set_zero_offset(self, z):
        super().set_zero_offset(z)
        self.update_data()

    def serialise(self):
        logger.info("Serialising channel %s", self.name)
        ser = super().serialise()
        ser.update({
            "show_channel": self.show_channel,
            "show_minmax": self.show_minmax,
            "show_limits": self.show_limits,
            "highlight": self.highlight,
            "viewbox_idx": self.pw.viewbox_idx(self.vb),
        })
        return ser

    def deserialise(self, layout):
        """
        layout: an item from the `channels` list inside windows in layouts
        """
        logger.info("Deserialising channel %s", self.name)
        super().deserialise(layout)
        if layout['show_channel'] is False:
            self.hide()
        if self.live:
            self.set_minmax(layout['show_minmax'])
            self.set_limits(layout['show_limits'])
        if layout.get('highlight', False):
            self.set_highlight(True)
