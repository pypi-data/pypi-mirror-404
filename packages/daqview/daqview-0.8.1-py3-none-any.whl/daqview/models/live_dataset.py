import logging
import datetime
import numpy as np
import numexpr
from PySide6.QtCore import Signal, QTimer

from .dataset import Dataset

logger = logging.getLogger(__name__)


class LiveDataset(Dataset):
    """
    Store data being streamed live from a server. Preallocates some space
    and can be subsequently updated as data comes in.

    Signals:
    channels_changed: emitted when the list of available channels has changed,
                      for example when connecting to a server.
    data_updated: emitted when a new data point is received from the server.
    """
    data_updated = Signal()

    def __init__(self, channels, groups):
        super().__init__(channels, groups)

        # Preallocate an hour worth (at 100Hz, realistically might be less)
        # of timestamp storage.
        self.timestamps = np.empty(3600 * 100)
        self.next_tidx = 0
        self.last_time = None

        # Store a dict of ndarrays keyed by channel IDs
        self.live_channels = {}
        self.live_channels_min = {}
        self.live_channels_max = {}

        # Optional offset to timestamps
        self.t_offset = None

        # Store how many pending emits of data_updated we have
        self._pending_emits = 0

        self.live = True

    def name(self):
        return "Live"

    def filename(self):
        return self.app.server.last_host

    def clear_data(self):
        """
        Clear all the buffered live data and restart recording.
        """
        logger.info("Clearing live data")
        self.timestamps = np.empty(3600 * 100)
        self.next_tidx = 0
        self.live_channels = {}
        self.live_channels_min = {}
        self.live_channels_max = {}

    def data_update(self, times, channel_ids,
                    data_fils, data_mins, data_maxs, _statuses,
                    emit_update=True):
        """
        Process a new datapoint for the currently streamed channels.

        Inserts NaN to non-streamed channels to keep their time indices
        in-sync.

        times: timestamps for new data point, array of floats
        channel_ids: list of channel IDs being updated
        data_fils: filtered data, 2d float array
        data_mins: min data, 2d float array
        data_maxs: max data, 2d float array
        status: status for each channel, 2d uint8 array
        emit_update: whether to emit data_updated signal
        All 2d arrays are of size [n_channels, n_updates]
        """
        assert len(channel_ids) == data_fils.shape[0]
        assert data_fils.shape == data_mins.shape == data_maxs.shape
        n_updates = times.size

        # Check if we are pending a zeroing and perform it if so
        if self.t_offset == "pending":
            self.zero_timestamps()

        # Check if we've gone backwards in time and if so, dump everything.
        if self.last_time is not None and self.last_time > times[-1]:
            logger.warning("Server time has gone backwards, discarding data")
            self.clear_data()

        # Check if we need to expand the buffers first
        if self.next_tidx + n_updates > self.timestamps.size:
            self._grow_buffers()

        self.last_time = times[-1]
        tidx0 = self.next_tidx
        tidx1 = tidx0 + n_updates
        self.timestamps[tidx0:tidx1] = times

        # Save the points received for each channel
        for idx, channel in enumerate(channel_ids):
            if channel not in self.live_channels:
                self._add_channel_storage(channel)
            self.live_channels[channel][tidx0:tidx1] = data_fils[idx]
            self.live_channels_min[channel][tidx0:tidx1] = data_mins[idx]
            self.live_channels_max[channel][tidx0:tidx1] = data_maxs[idx]

        # Evaluate new points for all derived channels
        for dc in self.derived_channels.values():
            if dc['id'] not in self.live_channels:
                self._add_channel_storage(dc['id'])
            expr = dc['expr']
            deps = {}
            for dep_id in dc['dependencies']:
                if dep_id not in self.live_channels:
                    self._add_channel_storage(dep_id)
                deps[dep_id] = self.live_channels[dep_id][tidx0:tidx1]
            data = numexpr.evaluate(expr, local_dict=deps, global_dict={})
            self.live_channels[dc['id']][tidx0:tidx1] = data

        # Fill in NaNs for channels not currently updated
        not_updated = set(channel_ids) - set(self.live_channels.keys()) \
            - set(self.derived_channels.keys())
        for channel in not_updated:
            self.live_channels[channel][tidx0:tidx1] = np.nan
            self.live_channels_min[channel][tidx0:tidx1] = np.nan
            self.live_channels_max[channel][tidx0:tidx1] = np.nan

        # Increment timestamp
        self.next_tidx += n_updates

        if emit_update:
            # Enqueue a data_updated for when we are next idle
            self._pending_emits += 1
            QTimer.singleShot(0, self._emit_data_updated)

    def _emit_data_updated(self):
        """Emit data_updated, called from timer callback."""
        if self._pending_emits > 0:
            self.data_updated.emit()
            self._pending_emits = 0

    def _add_channel_storage(self, channel_id):
        """
        Create storage for this channel if it didn't previously exist.

        channel_id: ID of new channel to create storage for
        """
        if channel_id in self.live_channels:
            logger.warning("Not adding storage for existing channel '%s'",
                           channel_id)
            return

        logger.info("Creating storage for new channel %s", channel_id)
        n = self.timestamps.size

        self.live_channels[channel_id] = np.empty(n)
        self.live_channels[channel_id][:] = np.nan
        self.live_channels_min[channel_id] = np.empty(n)
        self.live_channels_min[channel_id][:] = np.nan
        self.live_channels_max[channel_id] = np.empty(n)
        self.live_channels_max[channel_id][:] = np.nan

    def _grow_buffers(self):
        """
        Increase the size of all the buffers and copy the old data across.
        """
        logger.info("Growing storage buffers")
        old_size = self.timestamps.size
        new_timestamps = np.empty(old_size + 3600 * 100)
        new_timestamps[:old_size] = self.timestamps
        self.timestamps = new_timestamps

        for channel in self.live_channels:
            n = self.timestamps.size
            new_channel = np.empty(n)
            new_channel[:old_size] = self.live_channels[channel]
            self.live_channels[channel] = new_channel
            new_channel_min = np.empty(n)
            new_channel_min[:old_size] = self.live_channels_min[channel]
            self.live_channels_min[channel] = new_channel_min
            new_channel_max = np.empty(n)
            new_channel_max[:old_size] = self.live_channels_max[channel]
            self.live_channels_max[channel] = new_channel_max

    def get_channel_data(self, channel_id):
        """
        Fetch the time series and data points for a specific channel_id.
        """
        if channel_id not in self.live_channels:
            self._add_channel_storage(channel_id)
        idx = self.next_tidx
        t = self.timestamps[:idx]
        if self.t_offset is not None:
            t = t - self.t_offset
        return t, self.live_channels[channel_id][:idx]

    def get_channel_data_minmax(self, channel_id):
        """
        Fetch the time series and min/max data for a specific channel_id.
        """
        if channel_id not in self.live_channels:
            self._add_channel_storage(channel_id)
        idx = self.next_tidx
        t = self.timestamps[:idx]
        if self.t_offset is not None:
            t = t - self.t_offset
        return (
            t,
            self.live_channels[channel_id][:idx],
            self.live_channels_min[channel_id][:idx],
            self.live_channels_max[channel_id][:idx]
        )

    def add_derived_channel(self, channel, expr):
        super().add_derived_channel(channel, expr)

        # Having added the new channel, we must now compute
        # its back values for the data in our buffers
        self._add_channel_storage(channel['id'])
        dc = self.derived_channels[channel['id']]
        expr = dc['expr']
        deps = {}
        for dep_id in dc['dependencies']:
            deps[dep_id] = self.live_channels[dep_id][:self.next_tidx]
        data = numexpr.evaluate(expr, local_dict=deps, global_dict={})
        self.live_channels[channel['id']][:self.next_tidx] = data

    def zero_timestamps(self):
        if self.next_tidx > 0:
            self.t_offset = self.timestamps[self.next_tidx - 1]
            logger.info("Time offset set to %f", self.t_offset)
        else:
            self.t_offset = "pending"
            logger.info("No time data received yet, zeroing pending")

    def get_start_time(self):
        tnow = datetime.datetime.utcnow()
        dt = self.timestamps[self.next_tidx-1] - self.timestamps[0]
        tstart = tnow - datetime.timedelta(seconds=dt)
        return tstart.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def get_t0_time(self):
        t0 = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.timestamps[self.next_tidx-1])
        return t0.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def get_end_time(self):
        tnow = datetime.datetime.utcnow()
        return tnow.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def deserialise(self, layout):
        if self.app.server.is_connected():
            super().deserialise(layout)
        else:
            self.deferred_layout = layout
            self.app.server.time_update.connect(self.defer_deserialise)

    def defer_deserialise(self, time):
        if hasattr(self, 'deferred_layout'):
            logger.info("Running deferred deserialisation of LiveDataset")
            for dc in self.deferred_layout['derived_channels'].values():
                for dep_id in dc['dependencies']:
                    if dep_id not in self.live_channels:
                        self._add_channel_storage(dep_id)
            super().deserialise(self.deferred_layout)
            del self.deferred_layout
        self.app.server.time_update.disconnect(self.defer_deserialise)
