# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab_dock import TabDock


@pytest.fixture
def tabdock(app):
    return TabDock(False)


def test_shows_help(tabdock):
    assert tabdock.help_dock is not None
    window = tabdock.new_readout_window()
    assert tabdock.help_dock is None
    window.close()
    assert tabdock.help_dock is not None


def test_names(tabdock):
    rw1 = tabdock.new_readout_window()
    assert rw1.name == "Readout 1"
    rw2 = tabdock.new_readout_window()
    assert rw2.name == "Readout 2"
    rw3 = tabdock.new_readout_window()
    assert rw3.name == "Readout 3"
    pw1 = tabdock.new_plot_window()
    assert pw1.name == "Plot 1"
    pw2 = tabdock.new_plot_window()
    assert pw2.name == "Plot 2"
    pw3 = tabdock.new_plot_window("My Window")
    assert pw3.name == "My Window"
    pw4 = tabdock.new_plot_window("My Window")
    assert pw4.name == "My Window 2"
    pw5 = tabdock.new_plot_window("My Window")
    assert pw5.name == "My Window 3"


def test_allow_renames(tabdock):
    rw1 = tabdock.new_readout_window()
    rw2 = tabdock.new_readout_window()
    assert not tabdock.allow_rename(rw1.name)
    assert tabdock.allow_rename("New " + rw2.name)
