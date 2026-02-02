# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import numpy as np
from daqview.models.live_dataset import LiveDataset
from .mock_server import SAMPLE_CONFIG


def wait_for_data(qtbot, ld, ch, n):
    _, d = ld.get_channel_data(ch)
    while d.size < n:
        qtbot.wait(10)
        _, d = ld.get_channel_data(ch)


def test_handles_updates():
    ld = LiveDataset(SAMPLE_CONFIG['channels'], SAMPLE_CONFIG['groups'])
    ch = [SAMPLE_CONFIG['channels'][0]['id']]
    ts = np.array([1.0, 2.0, 3.0])
    x = np.array([[.1, .2, .3]])
    xmin = np.array([[.095, .195, .295]])
    xmax = np.array([[.105, .205, .305]])
    status = np.array([[0, 0, 0]], dtype=np.uint8)
    ld.data_update(ts, ch, x, xmin, xmax, status)

    ct, cx = ld.get_channel_data(ch[0])
    assert np.all(ct == ts)
    assert np.all(cx == x[0])

    ct, cx = ld.get_channel_data(SAMPLE_CONFIG['channels'][1]['id'])
    assert np.all(ct == ts)
    assert np.all(np.isnan(cx))

    ct, cx, cminx, cmaxx = ld.get_channel_data_minmax(ch[0])
    assert np.all(ct == ts)
    assert np.all(cx == x[0])
    assert np.all(cminx == xmin[0])
    assert np.all(cmaxx == xmax[0])

    new_ts = np.array([4.0, 5.0])
    new_x = np.array([[.4, .5]])
    new_xmin = np.array([[.395, .495]])
    new_xmax = np.array([[.405, .505]])
    new_status = np.array([[0, 0]], dtype=np.uint8)
    ld.data_update(new_ts, ch, new_x, new_xmin, new_xmax, new_status)

    ct, cx, cminx, cmaxx = ld.get_channel_data_minmax(ch[0])
    assert np.all(ct == np.concatenate((ts, new_ts)))
    assert np.all(cx == np.concatenate((x[0], new_x[0])))
    assert np.all(cminx == np.concatenate((xmin[0], new_xmin[0])))
    assert np.all(cmaxx == np.concatenate((xmax[0], new_xmax[0])))


def test_grow_buffers():
    ld = LiveDataset([SAMPLE_CONFIG['channels'][0]], SAMPLE_CONFIG['groups'])
    ch = [SAMPLE_CONFIG['channels'][0]['id']]
    t1 = np.linspace(0, 3600, 3600*100)
    t2 = np.linspace(3600, 3700, 100)
    x1 = np.sin(2*np.pi*10*t1).reshape((1, -1))
    x2 = np.sin(2*np.pi*10*t2).reshape((1, -1))
    s1 = np.zeros(t1.size, dtype=np.uint8).reshape((1, -1))
    s2 = np.zeros(t2.size, dtype=np.uint8).reshape((1, -1))
    ld.data_update(t1, ch, x1, x1, x1, s1)
    assert ld.timestamps.size == 3600 * 100
    ld.data_update(t2, ch, x2, x2, x2, s2)
    assert ld.timestamps.size == 3600 * 100 * 2

    ct, cx, cminx, cmaxx = ld.get_channel_data_minmax(ch[0])
    assert np.all(ct == np.concatenate((t1, t2)))
    assert np.all(cx == np.concatenate((x1[0], x2[0])))
    assert np.all(cminx == np.concatenate((x1[0], x2[0])))
    assert np.all(cmaxx == np.concatenate((x1[0], x2[0])))


def test_add_derived(app, qtbot):
    ld = app.server.live_data
    app.server.set_live_channels(["pc1"])
    wait_for_data(qtbot, ld, "pc1", 4)
    ch = {"id": "test", "name": "test"}
    ld.add_derived_channel(ch, "pc1*2")
    wait_for_data(qtbot, ld, "pc1", 8)
    _, d1 = ld.get_channel_data("pc1")
    _, d2 = ld.get_channel_data("test")
    assert np.allclose(np.array(d2), 2*np.array(d1), equal_nan=True)
    assert "test" in [c['id'] for c in ld.channels]
    assert "pc1" in ld.derived_channels['test']['dependencies']


def test_add_constant_derived(app, qtbot):
    ld = app.server.live_data
    qtbot.wait(1)
    qtbot.waitSignal(ld.data_updated)
    ch = {"id": "test", "name": "test"}
    ld.add_derived_channel(ch, "100")
    _, d1 = ld.get_channel_data("test")
    assert np.allclose(np.array(d1), 100*np.ones(d1.size), equal_nan=True)


def test_add_twoch_derived(app, qtbot):
    ld = app.server.live_data
    app.server.set_live_channels(["pc1", "p_inj_ox"])
    wait_for_data(qtbot, ld, "p_inj_ox", 4)
    ch = {"id": "test", "name": "test"}
    ld.add_derived_channel(ch, "p_inj_ox - pc1")
    wait_for_data(qtbot, ld, "p_inj_ox", 8)
    _, d1 = ld.get_channel_data("p_inj_ox")
    _, d2 = ld.get_channel_data("pc1")
    _, d3 = ld.get_channel_data("test")
    assert np.allclose(np.array(d3), np.array(d1) - np.array(d2),
                       equal_nan=True)
    assert "test" in [c['id'] for c in ld.channels]
    assert "pc1" in ld.derived_channels['test']['dependencies']
    assert "p_inj_ox" in ld.derived_channels['test']['dependencies']


def test_add_chained_derive(app, qtbot):
    ld = app.server.live_data
    app.server.set_live_channels(["pc1", "p_inj_ox"])
    wait_for_data(qtbot, ld, "p_inj_ox", 1)
    ch1 = {"id": "test1", "name": "test1"}
    ld.add_derived_channel(ch1, "p_inj_ox - pc1")
    wait_for_data(qtbot, ld, "test1", 2)
    ch2 = {"id": "test2", "name": "test2"}
    ld.add_derived_channel(ch2, "test1*2")
    wait_for_data(qtbot, ld, "test2", 3)
    _, d1 = ld.get_channel_data("test1")
    _, d2 = ld.get_channel_data("test2")
    assert np.allclose(2*np.array(d1), np.array(d2), equal_nan=True)


def test_zero_timestamps(app, qtbot):
    ld = app.server.live_data
    app.server.set_live_channels(["pc1", "p_inj_ox"])
    wait_for_data(qtbot, ld, "p_inj_ox", 10)
    ld.zero_timestamps()
    t, d1 = ld.get_channel_data("p_inj_ox")
    assert t[-1] == 0
    assert t[-2] < t[-1]


def test_get_channel_dependencies(app, qtbot):
    ld = app.server.live_data
    ch1 = {"id": "t1", "name": "Test 1"}
    ch2 = {"id": "t2", "name": "Test 2"}
    ch3 = {"id": "t3", "name": "Test 3"}
    ld.add_derived_channel(ch1, "pc1+1")
    ld.add_derived_channel(ch2, "t1*2 + p_inj_ox")
    ld.add_derived_channel(ch3, "t2 + pc1")
    assert ld.get_channel_dependencies("pc1") == ["pc1"]
    assert set(ld.get_channel_dependencies("t1")) == set(["pc1"])
    assert set(ld.get_channel_dependencies("t2")) == set(["pc1", "p_inj_ox"])
    assert set(ld.get_channel_dependencies("t3")) == set(["pc1", "p_inj_ox"])


def test_save_data(app, qtbot, tmpdir):
    ld = LiveDataset([SAMPLE_CONFIG['channels'][0]], SAMPLE_CONFIG['groups'])
    ch = [SAMPLE_CONFIG['channels'][0]['id']]
    t1 = np.linspace(0, 3600, 3600*100)
    x1 = np.sin(2*np.pi*10*t1).reshape((1, -1))
    s1 = np.zeros(t1.size, dtype=np.uint8).reshape((1, -1))
    ld.data_update(t1, ch, x1, x1, x1, s1)
    ld.save_data(str(tmpdir.join("saved_data.h5")))
