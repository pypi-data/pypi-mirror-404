# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab import LiveTab
from daqview.views.readout_window import ReadoutWindow


@pytest.fixture
def readoutchannel(app):
    livetab = LiveTab()
    rw = ReadoutWindow("Test Window", livetab.dock)
    rc = rw.add_channel(livetab.dataset, "pc1")
    app._test_tab = livetab
    app._test_window = rw
    return rc


def test_highlight(qtbot, readoutchannel):
    readoutchannel.set_highlight(True)
    qtbot.wait(1)
