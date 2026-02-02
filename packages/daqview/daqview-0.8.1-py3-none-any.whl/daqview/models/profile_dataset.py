import logging

import numpy as np
import datetime
import socket
import getpass
import json
import h5py

from .dataset import Dataset
from .sequencing import DAQ_SEQ_ID_RUN, DAQ_SEQ_ID_STOP

logger = logging.getLogger(__name__)


class ProfileDataset(Dataset):
    """
    Store a dataset generated from a templated profile.
    """

    def __init__(self, rendered):
        channels = {}
        groups = [
            {"id": "run_profiles", "name": "Run Profiles"},
            {"id": "stop_profiles", "name": "Stop Profiles"},
            {"id": "run_seq", "name": "Run Sequences"},
            {"id": "stop_seq", "name": "Stop Sequences"},
        ]
        self.channel_time = {}
        self.channel_data = {}
        self.rendered = rendered

        for profile in rendered.profiles:
            display = profile.to_display()
            for seq_type, seq_name in (
                (DAQ_SEQ_ID_RUN, "run"),
                (DAQ_SEQ_ID_STOP, "stop"),
            ):
                if seq_type in display:
                    for t, p, role, name, units in display[seq_type]:
                        role = f"{role}-{seq_name}"
                        channels[role] = {
                            "id": role,
                            "name": name,
                            "format": "%0.3f",
                            "groups": [f"{seq_name}_profiles"],
                            "units": units,
                        }
                        self.channel_time[role] = np.asarray(t)
                        self.channel_data[role] = np.asarray(p)
        run_idx = stop_idx = 0
        digital_channels = []
        for sequence in rendered.sequences:
            displays = sequence.to_display()
            runs = displays[DAQ_SEQ_ID_RUN]
            stops = displays[DAQ_SEQ_ID_STOP]

            def add_ch(t, d, role, name, group, idx):
                ch_id = f"{role}-{group}"
                channels[ch_id] = {
                    "id": ch_id,
                    "name": name,
                    "format": "%.1f",
                    "groups": [f"{group}_seq"],
                    "units": "",
                }
                digital_channels.append(ch_id)
                self.channel_time[ch_id] = np.asarray(t)
                self.channel_data[ch_id] = np.asarray(d)

            for (t, d, role, name) in runs:
                add_ch(t, d, role, name, "run", run_idx)
                run_idx += 1
            for (t, d, role, name) in stops:
                add_ch(t, d, role, name, "stop", stop_idx)
                stop_idx += 1
        idx = 0
        for ch in sorted(self.channel_data, reverse=True):
            if ch in digital_channels:
                self.channel_data[ch] += idx
                idx += 1

        super().__init__(list(channels.values()), groups)

    def name(self):
        return "Profile Data"

    def get_channel_data(self, channel_id):
        time = self.channel_time[channel_id]
        data = self.channel_data[channel_id]
        idx = min(time.size, data.size)
        return time[:idx], data[:idx]

    def save_data(self, fname):
        logger.info("Saving sequence dataset to file '%s'", fname)
        h5f = h5py.File(fname, "w")
        tnow = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        tpl = self.rendered.template
        h5f.attrs["version"] = 2
        h5f.attrs["name"] = "Sequence {}".format(tpl.name)
        h5f.attrs["start_datetime"] = tnow
        h5f.attrs["t0_datetime"] = tnow
        h5f.attrs["end_datetime"] = tnow
        h5f.attrs["location"] = "DAQview"
        h5f.attrs["hostname"] = socket.gethostname()
        h5f.attrs["operator"] = getpass.getuser()
        h5f.attrs["summary"] = "Sequence export for {}".format(tpl.name)
        h5f.attrs["project"] = ""
        h5f.attrs["daq_git_commit"] = ""
        h5f.attrs["analysis_metadata"] = json.dumps(self.rendered.generate_metadata())
        self._save_data_to_h5(h5f)
