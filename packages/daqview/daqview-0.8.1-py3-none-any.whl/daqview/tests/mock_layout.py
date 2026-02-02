import os.path
import yaml


def make_mock_layout_file(h5path, ymlpath):
    """
    Read mock_layout.yml, update the path to the h5 file dataset,
    and write it to the provided ymlpath.
    """
    path = os.path.join(
        os.path.split(os.path.abspath(__file__))[0],
        "mock_layout.yml")
    with open(path) as f:
        layout = yaml.safe_load(f)
    layout['dataset']['filename'] = str(h5path)
    with open(ymlpath, "w") as f:
        f.write(yaml.safe_dump(layout))


def make_mock_layout_server(server, ymlpath):
    """
    Read mock_layout.yml, update the path to the currently running server,
    and write it to the provided ymlpath.
    """
    path = os.path.join(
        os.path.split(os.path.abspath(__file__))[0],
        "mock_layout.yml")
    with open(path) as f:
        layout = yaml.safe_load(f)
    layout['dataset']['filename'] = str(server)
    layout['dataset']['live'] = True
    layout['dataset']['name'] = 'Live'
    with open(ymlpath, "w") as f:
        f.write(yaml.safe_dump(layout))
