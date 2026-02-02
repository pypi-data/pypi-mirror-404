from collections import defaultdict
import traceback
import datetime
import socket
import getpass
import logging
import numexpr
import numpy as np
import h5py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Dataset(QObject):
    """
    Store and process time series data for channels.

    Stores a single ndarray of double precision timestamps against which
    all channel data is time-indexed.
    Stores an ndarray of double precision samples for each channel.

    Provides access to a view of the most recent n seconds worth of data for
    specified channel.

    Provides ability to add a new datapoint, given a timestamp and a set of
    channels to update. Manages increasing buffer sizes as new data arrives.

    Signals:
    channels_changed: emitted when the list of available channels has changed,
                      for example when connecting to a server.
    """
    channels_changed = Signal()

    def __init__(self, channels, groups):
        """
        channels: list of channel configuration dicts.
        groups: list of group configuration dicts.
        """
        super().__init__()
        self.live = False
        self.app = QApplication.instance()
        if hasattr(self.app, 'datasets'):
            QApplication.instance().datasets[self.name()] = self
        self.derived_channels = {}
        self.update_channels(channels, groups)

    def update_channels(self, channels, groups):
        """
        Change which channels are available in this dataset.
        Used if the server channel configuration changes at runtime,
        e.g. after first connection and subsequently if the server
        reloads its configuration.

        channels: a list of channel configuration dicts
        """
        logger.info("Updating list of available channels")
        self.channels = channels
        self.groups = {g['id']: g for g in groups}
        self.groups['ungrouped'] = {'id': 'ungrouped', 'name': 'Ungrouped'}
        self.channels_changed.emit()

    def channels_by_id(self):
        return {c['id']: c for c in self.channels}

    def channels_by_group(self):
        groups = defaultdict(list)
        for channel in self.channels:
            if channel['groups']:
                for group in channel['groups']:
                    groups[group].append(channel)
            else:
                groups['ungrouped'].append(channel)
        return groups

    def get_channel_data(self, channel_id):
        raise NotImplementedError()

    def get_channel_config(self, channel_id):
        """
        Get a channel configuration dict by its ID.
        """
        return self.channels_by_id().get(channel_id, {})

    def get_channel_dependencies(self, channel_id):
        """
        Returns the channel IDs to stream in order to compute this channel.

        For most channels this is just a single-item list with its own ID,
        but for channels that are derived from multiple source channels,
        it contains each of their IDs rather than its own (which is unknown
        to the server).
        """
        cfg = self.get_channel_config(channel_id)
        if 'dependencies' in cfg:
            deps = []
            for ch in cfg['dependencies']:
                deps += self.get_channel_dependencies(ch)
            return list(set(deps))
        else:
            return [channel_id]

    def get_group_name(self, group_id):
        """
        Get the name for a given group_id
        """
        return self.groups[group_id]['name']

    def name(self):
        """
        Return a unique name for this dataset.
        """
        raise NotImplementedError()

    def evaluate(self, expr, dependencies=None):
        """
        Evaluate expression `expr` in the context of the latest value of each
        available channel.

        `dependencies` can be a list of channel IDs which the expression
        requires; if None then all the channel IDs in this dataset are used.

        Raises ValueError with an error message if the expression could not
        be evaluated.
        """
        context = {}
        if dependencies is None:
            dependencies = [c['id'] for c in self.channels]
        for channel_id in dependencies:
            if channel_id in expr:
                time, data = self.get_channel_data(channel_id)
                if len(data):
                    context[channel_id] = data[-1]
                else:
                    logger.warning("Dependency channel found but has no data")
                    context[channel_id] = np.nan
        try:
            return numexpr.evaluate(expr, local_dict=context, global_dict={})
        except (TypeError, KeyError, SyntaxError, AttributeError) as e:
            msg = "\n".join(traceback.format_exception_only(type(e), e))
            raise ValueError(msg)

    def add_derived_channel(self, channel, expr):
        """
        Add a new channel (with channel specification in `channel`),
        which is computed via `expr` from other channels.

        Raises ValueError with an error message if the channel couldn't be
        added, including if the expression fails to evaluate.
        """
        self.evaluate(expr)
        if not channel['name']:
            raise ValueError("Channel name required")
        if not channel['id']:
            raise ValueError("Channel ID required")
        if any(c['id'] == channel['id'] for c in self.channels):
            raise ValueError("Channel ID already in use")
        if 'groups' not in channel:
            channel['groups'] = ['derived']
        if 'derived' not in self.groups:
            self.groups['derived'] = {"id": "derived", "name": "Derived"}
        self.channels.append(channel)
        dependencies = []
        for maybe_dep in self.channels:
            if maybe_dep['id'] in expr:
                dependencies.append(maybe_dep['id'])
        channel['expr'] = expr
        channel['dependencies'] = dependencies
        self.derived_channels[channel['id']] = channel
        if channel not in self.app.prefs.get_recent_derived_channels():
            self.app.prefs.add_recent_derived_channel(channel)
        self.channels_changed.emit()

    def save_data(self, fname):
        """
        Save the current data to a file.
        """
        logger.info("Saving live data")
        h5f = h5py.File(fname, 'w')

        tnow = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        h5f.attrs['version'] = 2
        h5f.attrs['name'] = "Live Data {}".format(tnow)
        h5f.attrs['start_datetime'] = self.get_start_time()
        h5f.attrs['t0_datetime'] = self.get_t0_time()
        h5f.attrs['end_datetime'] = self.get_end_time()
        h5f.attrs['location'] = "Unknown"
        h5f.attrs['hostname'] = socket.gethostname()
        h5f.attrs['operator'] = getpass.getuser()
        h5f.attrs['summary'] = "Live Data export from DAQview"
        h5f.attrs['project'] = ""
        h5f.attrs['daq_git_commit'] = "Unknown"

        self._save_data_to_h5(h5f)

    def _save_data_to_h5(self, h5f):
        """
        Write all channel and groups to HDF5 dataset and close it.

        Ensure dataset is created and metadata set first.
        """
        h5f.create_group("channels")
        h5f.create_group("groups")
        h5f.create_group("config")
        for cid, c in self.channels_by_id().items():
            time, data = self.get_channel_data(cid)
            h5f['channels'].create_group(cid)
            h5f['channels'][cid].create_dataset(
                'time', data=time, compression='gzip', fletcher32=True)
            h5f['channels'][cid].create_dataset(
                'data', data=data, compression='gzip', fletcher32=True)
            for k in ('name', 'units', 'colour'):
                if k in c and c[k]:
                    h5f['channels'][cid].attrs[k] = c[k]
                else:
                    h5f['channels'][cid].attrs[k] = ""
            if 'latex_name' in c and c['latex_name']:
                h5f['channels'][cid].attrs['latex_name'] = c['latex_name']

        for gid, cs in self.channels_by_group().items():
            h5f['groups'].create_group(gid)
            h5f['groups'][gid].attrs['name'] = self.get_group_name(gid)
            for c in cs:
                cid = c['id']
                h5f['groups'][gid][cid] = h5py.SoftLink("/channels/" + cid)
        h5f.close()

    def get_start_time(self):
        raise NotImplementedError

    def get_t0_time(self):
        raise NotImplementedError

    def get_end_time(self):
        raise NotImplementedError

    def serialise(self):
        return {
            "name": self.name(),
            "filename": self.filename(),
            "live": self.live,
            "derived_channels": self.derived_channels,
        }

    def deserialise(self, layout):
        logger.info("Deserialising dataset")
        for dc in layout['derived_channels'].values():
            logger.info("Adding derived channel '%s'", dc['name'])
            for idx, channel in enumerate(self.channels):
                if channel['id'] == dc['id']:
                    del self.channels[idx]
                    break
            self.add_derived_channel(dc, dc['expr'])
