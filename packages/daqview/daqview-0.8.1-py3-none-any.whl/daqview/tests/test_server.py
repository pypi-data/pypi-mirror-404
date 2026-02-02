# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

from . import mock_server


def test_connect(server):
    assert server.is_connected()


def test_disconnect(server):
    assert server.is_connected()
    server.disconnect_from_host()
    assert not server.is_connected()


def test_reconnect(server):
    assert server.is_connected()
    server.reconnect()
    assert server.is_connected()


def test_get_config(server):
    assert server.get_config() == mock_server.SAMPLE_CONFIG
    assert server.get_channels() == mock_server.SAMPLE_CONFIG['channels']


def test_get_status(server):
    assert server.get_status() == mock_server.SAMPLE_STATUS


def test_get_time(server, qtbot):
    with qtbot.waitSignal(server.time_update) as blocker:
        pass
    t0 = blocker.args[0]
    with qtbot.waitSignal(server.time_update) as blocker:
        pass
    t1 = blocker.args[0]
    assert t1 > t0


def test_set_live_channels(server, qtbot, mocker):
    channels = [c['id'] for c in mock_server.SAMPLE_CONFIG["channels"][0:2]]
    mocker.spy(server.live_data, 'data_update')
    server.set_live_channels(channels)
    with qtbot.waitSignal(server.time_update):
        pass
    assert server.live_data.data_update.call_args[0][1] == channels


def test_ensure_live_channels(server, qtbot, mocker):
    channels = [c['id'] for c in mock_server.SAMPLE_CONFIG["channels"][0:2]]
    mocker.spy(server.live_data, 'data_update')
    server.set_live_channels(channels)
    with qtbot.waitSignal(server.time_update):
        pass
    channels = [c['id'] for c in mock_server.SAMPLE_CONFIG["channels"][0:3]]
    server.ensure_live_channels(channels)
    with qtbot.waitSignal(server.time_update):
        pass
    assert server.live_data.data_update.call_args[0][1] == channels
