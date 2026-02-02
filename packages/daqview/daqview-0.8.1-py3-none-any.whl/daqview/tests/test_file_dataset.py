# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import numpy as np
from daqview.models.file_dataset import FileDataset
from .mock_server import SAMPLE_CONFIG


def test_read_file(h5):
    df = FileDataset(h5)
    assert df.name() == "Mock Dataset"
    assert df.filename() == h5
    assert df.get_file_metadata()['summary'] == "Mock Summary"
    channels = set(df.channels_by_id())
    assert channels == set(c['id'] for c in SAMPLE_CONFIG['channels'])
    channel = SAMPLE_CONFIG['channels'][0]
    t, x = df.get_channel_data(channel['id'])
    assert t.size, x.size
    assert df.get_channel_config(channel['id'])["colour"] == channel['colour']
    assert df.get_group_name("fl") == "Fuel"


def test_serialise(h5):
    df = FileDataset(h5)
    s = df.serialise()
    assert s == {
        "name": "Mock Dataset", "filename": h5, "live": False,
        "derived_channels": {}
    }


def test_ungrouped(h5):
    df = FileDataset(h5)
    groups = df.channels_by_group()
    assert groups['ungrouped'][0]['id'] == 'thrust'


def test_evaluate(h5):
    df = FileDataset(h5)
    result = df.evaluate("p_inj_ox + p_inj_fl * 2")
    _, d1 = df.get_channel_data("p_inj_ox")
    _, d2 = df.get_channel_data("p_inj_fl")
    assert result == d1[-1] + 2*d2[-1]


def test_add_derived(h5):
    df = FileDataset(h5)
    ch = {"id": "test", "name": "test"}
    df.add_derived_channel(ch, "pc1*2")
    _, d1 = df.get_channel_data("pc1")
    _, d2 = df.get_channel_data("test")
    assert np.allclose(np.array(d2), 2*np.array(d1))
    assert "test" in [c['id'] for c in df.channels]
    assert "pc1" in df.derived_channels['test']['dependencies']


def test_add_constant_derived(h5):
    df = FileDataset(h5)
    ch = {"id": "test", "name": "test"}
    df.add_derived_channel(ch, "100")
    _, d1 = df.get_channel_data("test")
    assert np.allclose(np.array(d1), 100*np.ones(d1.size))


def test_add_twoch_derived(h5):
    df = FileDataset(h5)
    ch = {"id": "test", "name": "test"}
    df.add_derived_channel(ch, "p_inj_ox - pc1")
    _, d1 = df.get_channel_data("p_inj_ox")
    _, d2 = df.get_channel_data("pc1")
    _, d3 = df.get_channel_data("test")
    assert np.allclose(np.array(d3), np.array(d1) - np.array(d2))
    assert "test" in [c['id'] for c in df.channels]
    assert "pc1" in df.derived_channels['test']['dependencies']
    assert "p_inj_ox" in df.derived_channels['test']['dependencies']


def test_serialise_derived(h5):
    df = FileDataset(h5)
    ch = {"id": "test", "name": "Test"}
    df.add_derived_channel(ch, "pc1*2")
    s = df.serialise()
    assert s == {
        "name": "Mock Dataset", "filename": h5, "live": False,
        "derived_channels": {
            "test": {
                "id": "test", "name": "Test", "groups": ["derived"],
                "expr": "pc1*2", "dependencies": ["pc1"]
            }
        }
    }


def test_get_channel_dependencies(h5):
    df = FileDataset(h5)
    ch1 = {"id": "t1", "name": "Test 1"}
    ch2 = {"id": "t2", "name": "Test 2"}
    ch3 = {"id": "t3", "name": "Test 3"}
    df.add_derived_channel(ch1, "pc1+1")
    df.add_derived_channel(ch2, "t1*2 + p_inj_ox")
    df.add_derived_channel(ch3, "t2 + pc1")
    assert df.get_channel_dependencies("pc1") == []
    assert df.get_channel_dependencies("t1") == []
    assert df.get_channel_dependencies("t2") == []
    assert df.get_channel_dependencies("t3") == []
