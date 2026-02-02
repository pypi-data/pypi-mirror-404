import h5py
import numpy as np

from .mock_server import SAMPLE_CONFIG


def make_mock_file(path):
    h5f = h5py.File(path, 'w')
    h5f.create_group("channels")
    h5f.create_group("groups")
    h5f.create_group("sequences")
    h5f.create_group("raw_data")

    t = np.linspace(0, 10, 100)
    x = np.sin(2*np.pi*10*t)

    time_dset = None
    for channel in SAMPLE_CONFIG['channels']:
        chgrp = h5f['channels'].create_group(channel['id'])
        if time_dset is None:
            time_dset = chgrp.create_dataset(
                'time', data=t, compression='gzip', fletcher32=True)
        else:
            chgrp['time'] = time_dset
        chgrp.create_dataset(
            'data', data=x, compression='gzip', fletcher32=True)
        for k in ('name', 'units', 'colour'):
            if k in channel and channel[k]:
                chgrp.attrs[k] = channel[k]
            else:
                chgrp.attrs[k] = ""

    for group in SAMPLE_CONFIG['groups']:
        ggrp = h5f['groups'].create_group(group['id'])
        ggrp.attrs['name'] = group['name']
        for channel in SAMPLE_CONFIG['channels']:
            if group['id'] in channel['groups']:
                chid = channel['id']
                ggrp[chid] = h5py.SoftLink("/channels/" + chid)

    h5f.attrs['version'] = 1
    h5f.attrs['name'] = "Mock Dataset"
    h5f.attrs['start_datetime'] = "2018-01-01T00:00:00.000000Z"
    h5f.attrs['t0_datetime'] = "2018-01-01T00:00:00.500000Z"
    h5f.attrs['end_datetime'] = "2018-01-01T00:00:01.000000Z"
    h5f.attrs['location'] = "Mock Server"
    h5f.attrs['hostname'] = "Mock Hostname"
    h5f.attrs['operator'] = "Mock Operator"
    h5f.attrs['summary'] = "Mock Summary"
    h5f.attrs['project'] = "Mock Project"
    h5f.attrs['config_file_path'] = "/mock/config/path"
    h5f.attrs['config_file_sha256'] = "mock"
    h5f.attrs['config_file_git_commit'] = "mock"
    h5f.attrs['assets_file_path'] = "/mock/assets/path"
    h5f.attrs['assets_file_sha256'] = "mock"
    h5f.attrs['assets_file_git_commit'] = "mock"
    h5f.attrs['daq_git_commit'] = "mock"
