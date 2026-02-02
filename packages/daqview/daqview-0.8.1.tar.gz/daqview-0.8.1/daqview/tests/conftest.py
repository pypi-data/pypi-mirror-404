import pytest
import daqview
import yaml
import os.path
from . import mock_server, mock_file, mock_layout

daqserver_address = None


@pytest.fixture(scope='session', autouse=True)
def daqserver():
    """
    Creates a mock server for daqview to connect to.
    Returns the hostname:port of the server.
    """
    global daqserver_address
    daqserver_address = mock_server.run()
    return daqserver_address


@pytest.fixture(scope='session', autouse=True)
def prefs(qapp):
    qapp.prefs = daqview.models.preferences.Preferences()


@pytest.fixture
def server(qapp, tmpdir, qtbot):
    daqview.models.preferences.PREF_DIR = str(tmpdir.mkdir("prefs"))
    server = daqview.models.server.Server()
    server.connect_to_host(daqserver_address)
    with qtbot.waitSignal(server.time_update):
        pass
    yield server
    server.disconnect_from_host()


@pytest.fixture
def app(qapp, qtbot, server, tmpdir):
    qapp.datasets = {}
    qapp.server = server
    return qapp


@pytest.fixture(autouse=True)
def mock_errmsg(mocker):
    """
    Mock out QErrorMessage to prevent xvfb crashes.
    """
    mocker.patch('daqview.models.server.QErrorMessage')
    mocker.patch('daqview.views.main_window.QErrorMessage')


@pytest.fixture(scope='session')
def h5(tmpdir_factory):
    """
    Creates a mock HDF5 file. Returns the path to the file.
    """
    path = tmpdir_factory.mktemp("mock_file").join("mock.h5")
    mock_file.make_mock_file(path)
    return path


@pytest.fixture(scope='session')
def layout_file(tmpdir_factory, h5):
    """
    Creates a mock layout file with lots of features enabled.
    The layout dataset will be a HDF5 file which exists.
    """
    path = str(tmpdir_factory.mktemp("mock_layout").join("mock_file.yml"))
    mock_layout.make_mock_layout_file(h5, path)
    return path


@pytest.fixture(scope='session')
def layout_server(tmpdir_factory):
    """
    Creates a mock layout file with lots of features enabled.
    The layout dataset will be a HDF5 file which exists.
    """
    path = str(tmpdir_factory.mktemp("mock_layout").join("mock_server.yml"))
    mock_layout.make_mock_layout_server(daqserver_address, path)
    return path


@pytest.fixture(scope='session')
def sequence_template(tmpdir_factory):
    """
    Creates a mock sequence template configuration file.
    """
    tplpath = os.path.join(
        os.path.split(os.path.abspath(__file__))[0],
        "sequence_template.yml")
    with open(tplpath) as f:
        tpl = yaml.safe_load(f)
    ymlpath = str(tmpdir_factory.mktemp("mock_seq_tpls").join("templates.yml"))
    with open(ymlpath, "w") as f:
        f.write(yaml.safe_dump(tpl))
    return ymlpath
