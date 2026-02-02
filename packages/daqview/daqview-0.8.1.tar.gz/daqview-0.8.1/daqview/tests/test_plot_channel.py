# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab import FileTab, LiveTab
from daqview.models.file_dataset import FileDataset
from daqview.views.plot_window import PlotWindow


@pytest.fixture
def file_plotchannel(app, h5):
    filedataset = FileDataset(h5)
    filetab = FileTab(filedataset)
    plotwindow = PlotWindow("Test Window", filetab.dock)
    plotwindow._test_dataset = filedataset
    plotchannel = plotwindow.add_channel(filetab.dataset, "pc1")
    app._test_tab = filetab
    app._test_window = plotwindow
    return plotchannel


@pytest.fixture
def live_plotchannel(app, qtbot):
    livetab = LiveTab()
    plotwindow = PlotWindow("Test Window", livetab.dock)
    plotchannel = plotwindow.add_channel(livetab.dataset, "pc1")
    app._test_tab = livetab
    app._test_window = plotwindow
    return plotchannel


def test_hide(qtbot, file_plotchannel):
    file_plotchannel.hide()
    qtbot.wait(1)
    file_plotchannel.show()
    qtbot.wait(1)


def test_hide_others(qtbot, file_plotchannel):
    file_plotchannel.pw.add_channel(file_plotchannel.dataset, "p_inj_fl")
    qtbot.wait(1)
    file_plotchannel.hide_others()
    qtbot.wait(1)


def test_highlight(qtbot, file_plotchannel):
    qtbot.wait(1)
    file_plotchannel.set_highlight(True)
    qtbot.wait(1)
    file_plotchannel.set_highlight(False)
    qtbot.wait(1)


def test_temporary_highlight(qtbot, file_plotchannel):
    qtbot.wait(1)
    file_plotchannel.set_temporary_highlight(True)
    qtbot.wait(1)
    file_plotchannel.set_temporary_highlight(False)
    qtbot.wait(1)


def test_separate_y_axis(qtbot, file_plotchannel):
    qtbot.wait(1)
    file_plotchannel.separate_y_axis()
    qtbot.wait(1)


def test_remove(qtbot, file_plotchannel):
    file_plotchannel.remove()
    qtbot.wait(1)


def test_minmax(qtbot, live_plotchannel):
    live_plotchannel.set_minmax(True)
    qtbot.wait(1)
    live_plotchannel.set_minmax(False)
    qtbot.wait(1)


def test_limits(qtbot, live_plotchannel):
    live_plotchannel.set_limits(True)
    qtbot.wait(1)
    live_plotchannel.set_limits(False)
    qtbot.wait(1)


def test_streaming_ids(qtbot, live_plotchannel):
    pc = live_plotchannel
    assert pc.streaming_channel_ids() == [pc.channel_id]
