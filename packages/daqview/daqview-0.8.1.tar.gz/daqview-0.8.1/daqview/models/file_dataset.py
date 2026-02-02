import logging
import numpy as np
import numexpr
import h5py

from .dataset import Dataset

logger = logging.getLogger(__name__)


class FileDataset(Dataset):
    """
    Store a dataset loaded from a file. Cannot be updated after loading.
    """
    def __init__(self, filename):
        channels = {}
        groups = []
        self.channel_time = {}
        self.channel_data = {}
        self._filename = filename
        self.h5file = h5py.File(filename, 'r')
        self.attrs = dict(self.h5file.attrs.items())
        if 'version' not in self.attrs or self.attrs['version'] not in (1, 2):
            logger.warning("Unknown HDF5 file version. Proceeding anyway.")
        if self.attrs.get('version') == 2:
            for fname in self.h5file.get('config'):
                for k, v in dict(self.h5file['config'][fname].attrs).items():
                    self.attrs[fname+"_"+k] = v
        self._name = self.attrs['name']
        for ch in self.h5file['channels']:
            attrs = self.h5file['channels'][ch].attrs
            channel = {"id": ch, "name": attrs.get('name', ch),
                       "units": attrs.get('units', ''), "groups": []}
            for attr in ("format", "colour"):
                if attr in attrs:
                    channel[attr] = attrs[attr]
            channels[ch] = channel
            self.channel_time[ch] = self.h5file['channels'][ch]['time']
            self.channel_data[ch] = self.h5file['channels'][ch]['data']
        for gr in self.h5file['groups']:
            group = {"id": gr, "name": self.h5file['groups'][gr].attrs['name']}
            groups.append(group)
            for ch in self.h5file['groups'][gr]:
                channels[ch]['groups'].append(gr)
        super().__init__(list(channels.values()), groups)

    def name(self):
        return self._name

    def filename(self):
        return self._filename

    def close(self):
        if self.h5file:
            self.h5file.close()

    def get_channel_data(self, channel_id):
        time = self.channel_time[channel_id]
        data = self.channel_data[channel_id]
        idx = min(time.size, data.size)
        return time[:idx], data[:idx]

    def get_channel_dependencies(self, channel_id):
        """
        File dataset channels never have any dependencies which need streaming.
        """
        return []

    def get_file_metadata(self):
        return self.attrs

    def add_derived_channel(self, channel, expr):
        super().add_derived_channel(channel, expr)

        # After adding the new derived channel, we need to
        # actually compute what its time and data arrays must be
        dc = self.derived_channels[channel['id']]
        expr = dc['expr']
        dependencies = dc['dependencies']

        if not dependencies:
            # If there are no dependencies, then we can simply run the
            # expression over the longest timebase in the dataset.
            longest_channel = None
            longest_length = 0
            longest_time = None
            for channel_id, time in self.channel_time.items():
                if time.size > longest_length:
                    longest_channel = channel_id
                    longest_time = time
            if longest_channel is None:
                raise ValueError("Couldn't find any channels in dataset")
            self.channel_time[channel['id']] = longest_time
            self.channel_data[channel['id']] = np.ones(longest_time.shape)
            self.channel_data[channel['id']] *= self.evaluate(expr, [])
        else:
            # We need to compute the new (time, data) arrays for this channel.
            # Since the channels in a FileDataset do not necessarily share the
            # same timebase, we have to find the time points that are shared
            # by all dependent channels and then compute on those points only.
            t0, d0 = self.get_channel_data(dependencies[0])
            tsel = np.ones(t0.shape, dtype=bool)

            for dep in dependencies[1:]:
                t, _ = self.get_channel_data(dep)
                tsel &= np.isin(t0, t, assume_unique=True)

            channel_time = t0[tsel]
            self.channel_time[channel['id']] = channel_time

            # Now we can go through and work out which data points from each
            # channel should be used.
            datas = {}
            datas[dependencies[0]] = d0[tsel]
            for dep in dependencies[1:]:
                t, d = self.get_channel_data(dep)
                tsel = np.isin(t, channel_time, assume_unique=True)
                datas[dep] = d[tsel]

            data = numexpr.evaluate(expr, local_dict=datas, global_dict={})
            self.channel_data[channel['id']] = data

    def get_start_time(self):
        return self.h5file.attrs['start_datetime']

    def get_t0_time(self):
        return self.h5file.attrs['t0_datetime']

    def get_end_time(self):
        return self.h5file.attrs['end_datetime']
