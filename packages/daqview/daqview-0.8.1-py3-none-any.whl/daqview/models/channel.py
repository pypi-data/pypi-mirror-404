import logging
import pyqtgraph as pg
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from colour import web2hex

logger = logging.getLogger(__name__)

DEFAULT_COLOURS = [
    '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462',
    '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f']
DEFAULT_COLOURS_IDX = 0


def get_default_colour():
    global DEFAULT_COLOURS_IDX
    colspec = DEFAULT_COLOURS[DEFAULT_COLOURS_IDX]
    DEFAULT_COLOURS_IDX = (DEFAULT_COLOURS_IDX + 1) % len(DEFAULT_COLOURS)
    return colspec


class Channel(QObject):
    """
    Represents one channel inside a Window.
    """
    def __init__(self, dataset, channel_id, window):
        super().__init__()
        self.dataset = dataset
        self.channel_id = channel_id
        self.window = window
        self.channel_cfg = self.dataset.get_channel_config(channel_id)
        self.name = self.channel_cfg['name']
        self.units = self.channel_cfg['units']
        self.format = self._format_checked(self.channel_cfg)
        if QApplication.instance().prefs.get_use_server_colours():
            self.colour = self._colour_checked(self.channel_cfg)
        else:
            self.colour = get_default_colour()
        self.live = self.dataset.live
        self.current_value = 0.0
        self.zero_offset = None

        if self.live:
            self.dataset.data_updated.connect(self.update_data)

    def update_data(self):
        raise NotImplementedError()

    def get_name(self):
        if self.zero_offset is None:
            return self.name
        else:
            return f"{self.name} [Zeroed]"

    def remove(self):
        logger.info("Removing channel %s", self.name)
        self.window.remove_channel(self)

    def serialise(self):
        logger.info("Serialising channel %s", self.name)
        return {
            "dataset": self.dataset.name(),
            "channel_id": self.channel_id,
            "colour": self.colour,
            "format": self.format,
        }

    def deserialise(self, layout):
        logger.info("Deserialising channel %s", self.name)
        self.update_colour(layout.get("colour"))
        self.format = self._format_checked(layout)

    def formatted_value(self, time=None, value=None):
        """
        Formats the given value according to the channel configuration.
        If no value is given but a time is given, use the channel value
        at that time. If no time is given either, uses the current value.
        """
        if value is None:
            if time is None:
                value = self.current_value
            else:
                value = self.value_for_time(time)

        return self.format % value

    def formatted_value_with_units(self, time=None, value=None):
        """
        Returns the value as per formatted_value, but with the channel's
        units appended.
        """
        return self.formatted_value(time, value) + " " + self.units

    def value_for_time(self, time):
        """
        Returns the value for this channel at the closest point to the given
        time.
        """
        if not self.data.size:
            return 0.0
        idx = np.searchsorted(self.time, time)
        if idx >= self.data.size:
            idx -= 1
        d = self.data[idx]
        if self.zero_offset is not None:
            d -= self.zero_offset
        return d

    def values_for_times(self, t0, t1):
        """
        Returns arrays of timestamps and corresponding values for this channel
        between times t0 and t1. If the times are invalid or no data exists
        between those times returns empty arrays.
        """
        idx0 = np.searchsorted(self.time, t0)
        idx1 = np.searchsorted(self.time, t1)
        idx0 = max(idx0, 0)
        idx1 = min(idx1, self.time.size)
        d = self.data[idx0:idx1]
        if self.zero_offset is not None:
            d = self.data[idx0:idx1] - self.zero_offset
        return self.time[idx0:idx1], d

    def first_value(self):
        """
        Returns the first value stored for this channel,
        or 0.0 if no values are stored.
        """
        if not self.data.size:
            return 0.0
        elif self.zero_offset is not None:
            return self.data[0] - self.zero_offset
        else:
            return self.data[0]

    def set_zero_offset(self, z):
        """
        Set the zero-offset for this channel to `z`.

        When set to 0.0 or None, no zero offset is applied.

        The zero offset is automatically applied whenever data is returned
        by the class, e.g. through the `values_for_times` methods or when
        being plotted.
        """
        logger.info("Channel %s setting zero offset to %f", self.channel_id, z)
        if z == 0.0 or z is None:
            self.zero_offset = None
        else:
            self.zero_offset = float(z)
        self.window.channels_changed.emit()

    def streaming_channel_ids(self):
        """
        Returns a list of channel IDs which must be streamed for this channel.
        For most channels this is just a single-item list with its own ID,
        but for channels that are derived from multiple source channels,
        it contains each of their IDs rather than its own (which is unknown
        to the server).
        """
        return self.dataset.get_channel_dependencies(self.channel_id)

    def update_colour(self, new_colour):
        logger.info("New colour %s for channel %s", new_colour, self.name)
        self.colour = self._colour_checked({"colour": new_colour})

    def _colour_checked(self, channel):
        """
        Check the given colour can be used safely by pyqtgraph and
        return a default if not.
        """
        # Use default colour if none is specified
        if "colour" not in channel:
            return get_default_colour()

        # Attempt to decode a web colour name. The result of web2hex is always
        # valid for mkColor.
        try:
            colspec = web2hex(channel['colour'])
            return colspec
        except (ValueError, AttributeError):
            pass

        # If web2hex can't decode the colour, it might be another format that
        # mkColor accepts, such as 'r' or a single number.
        try:
            colspec = channel['colour']
            pg.mkColor(colspec)
            return colspec
        except (ValueError, TypeError, IndexError, KeyError, UnboundLocalError,
                Exception):
            # mkColor can throw a really wild menagerie of errors
            return get_default_colour()

    def get_qcolor(self):
        return pg.mkColor(self.colour)

    def _format_checked(self, channel):
        """
        Check the given format can be used and return a default if not.
        """
        try:
            fstr = channel['format']
            fstr % 123.45
            return fstr
        except (KeyError, TypeError):
            return "%.02f"
