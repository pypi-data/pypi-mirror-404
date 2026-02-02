# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import os.path
from daqview.models import preferences


def test_new(tmpdir):
    preferences.PREF_DIR = str(tmpdir.mkdir("prefs"))
    p = preferences.Preferences()
    assert p.get_last_server() == "localhost:1736"
    p.save()
    with open(os.path.join(preferences.PREF_DIR, preferences.PREF_FILE)) as f:
        prefs = f.read()
    assert prefs == "[DAQview]\n\n"


def test_existing(tmpdir):
    preferences.PREF_DIR = str(tmpdir.mkdir("existing_prefs"))
    pref_path = os.path.join(preferences.PREF_DIR, preferences.PREF_FILE)
    with open(pref_path, "w") as f:
        f.write("[DAQview]\nlast_server = test:321\n\n")
    p = preferences.Preferences()
    assert p.get_last_server() == "test:321"


def test_save(tmpdir):
    preferences.PREF_DIR = str(tmpdir.mkdir("prefs"))
    p = preferences.Preferences()
    p.set_last_server("remote:1234")
    assert p.get_last_server() == "remote:1234"
    with open(os.path.join(preferences.PREF_DIR, preferences.PREF_FILE)) as f:
        prefs = f.read()
    assert prefs == "[DAQview]\nlast_server = remote:1234\n\n"


def test_recent_derived_channels(tmpdir):
    preferences.PREF_DIR = str(tmpdir.mkdir("prefs"))
    p = preferences.Preferences()
    num = preferences.NUM_RECENT
    entries = [{"id": f"test{i}"} for i in range(num+5)]
    for entry in entries[:3]:
        p.add_recent_derived_channel(entry)
    assert p.get_recent_derived_channels() == entries[:3]
    for entry in entries[3:]:
        p.add_recent_derived_channel(entry)
    assert p.get_recent_derived_channels() == entries[-num:]


def test_recents(tmpdir):
    preferences.PREF_DIR = str(tmpdir.mkdir("prefs"))
    p = preferences.Preferences()
    num = preferences.NUM_RECENT
    entries = [f"test/path/to/test{i}" for i in range(num+5)]
    for entry in entries[:3]:
        p.add_recent_derived_channel(entry)
    assert p.get_recent_derived_channels() == entries[:3]
    for entry in entries[3:]:
        p.add_recent_derived_channel(entry)
    assert p.get_recent_derived_channels() == entries[-num:]
