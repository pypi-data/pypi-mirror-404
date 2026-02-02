# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab import FileTab
from daqview.models.file_dataset import FileDataset
from daqview.views.plot_window import PlotWindow
from daqview.views.plot_viewbox import PlotViewBox


@pytest.fixture
def plotviewbox(app, h5):
    filedataset = FileDataset(h5)
    filetab = FileTab(filedataset)
    plotwindow = PlotWindow("Test Window", filetab.dock)
    plotvb = PlotViewBox(plotwindow)
    plotvb._test_dataset = filedataset
    app._test_tab = filetab
    app._test_window = plotwindow
    app._test_viewbox = plotvb
    return plotvb


def test_twinx(qtbot, plotviewbox):
    other_vb = PlotViewBox(plotviewbox.pw)
    other_vb.set_x_units("s")
    other_vb.set_y_units("bar(g)")
    plotviewbox.twinx(other_vb, "N")
    qtbot.wait(1)
    assert plotviewbox.get_y_units() == "N"
    assert other_vb.get_y_units() == "bar(g)"


def test_x_mode(qtbot, plotviewbox):
    plotviewbox.set_x_mode("last_n")
    qtbot.wait(1)
    assert plotviewbox.get_x_mode() == "last_n"
    plotviewbox.set_x_mode("all")
    qtbot.wait(1)
    assert plotviewbox.get_x_mode() == "all"
    plotviewbox.set_x_mode("link")
    qtbot.wait(1)
    assert plotviewbox.get_x_mode() == "link"
    plotviewbox.set_x_mode("manual")
    qtbot.wait(1)
    assert plotviewbox.get_x_mode() == "manual"


def test_x_last_n(qtbot, plotviewbox):
    plotviewbox.set_x_last_n_secs(5)
    qtbot.wait(1)
    assert plotviewbox.get_x_last_n_secs() == 5


def test_x_manual(qtbot, plotviewbox):
    plotviewbox.set_x_mode("manual")
    plotviewbox.set_manual_x_range(0.1, 0.2)
    qtbot.wait(1)
    assert plotviewbox.get_x_manual_from() == 0.1
    assert plotviewbox.get_x_manual_to() == 0.2
    assert plotviewbox.get_manual_x_range() == (0.1, 0.2)


def test_x_mouse(qtbot, plotviewbox):
    plotviewbox.set_x_mouse(True)
    qtbot.wait(1)
    plotviewbox.set_x_mouse(False)
    qtbot.wait(1)


def test_x_grid(qtbot, plotviewbox):
    plotviewbox.set_x_grid(True)
    qtbot.wait(1)
    plotviewbox.set_x_grid(False)
    qtbot.wait(1)


def test_y_mode(qtbot, plotviewbox):
    plotviewbox.set_y_mode("auto_vis")
    qtbot.wait(1)
    assert plotviewbox.get_y_mode() == "auto_vis"
    plotviewbox.set_y_mode("auto_all")
    qtbot.wait(1)
    assert plotviewbox.get_y_mode() == "auto_all"
    plotviewbox.set_y_mode("manual")
    qtbot.wait(1)
    assert plotviewbox.get_y_mode() == "manual"


def test_y_manual(qtbot, plotviewbox):
    plotviewbox.set_y_mode("manual")
    plotviewbox.set_manual_y_range(0.1, 0.2)
    qtbot.wait(1)
    assert plotviewbox.get_y_manual_from() == 0.1
    assert plotviewbox.get_y_manual_to() == 0.2
    assert plotviewbox.get_manual_y_range() == (0.1, 0.2)


def test_y_mouse(qtbot, plotviewbox):
    plotviewbox.set_y_mouse(True)
    qtbot.wait(1)
    plotviewbox.set_y_mouse(False)
    qtbot.wait(1)


def test_y_grid(qtbot, plotviewbox):
    plotviewbox.set_y_grid(True)
    qtbot.wait(1)
    plotviewbox.set_y_grid(False)
    qtbot.wait(1)
