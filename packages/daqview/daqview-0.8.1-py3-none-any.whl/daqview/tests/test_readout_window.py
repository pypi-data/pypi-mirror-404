# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab import LiveTab
from daqview.views.readout_window import ReadoutWindow


@pytest.fixture
def readoutwindow(app, h5):
    tab = LiveTab()
    window = ReadoutWindow("Test Window", tab.dock)
    window._test_tab = tab
    app._test_window = window
    return window


def test_add_channel(qtbot, readoutwindow):
    readoutwindow.add_channel(readoutwindow._test_tab.dataset, "p_inj_fl")
    qtbot.wait(1)
