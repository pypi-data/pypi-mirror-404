# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.tab import FileTab
from daqview.models.file_dataset import FileDataset
from daqview.views.plot_window import PlotWindow
from daqview.models.measurements import MEASUREMENTS


@pytest.fixture
def plotwindow(app, h5):
    filedataset = FileDataset(h5)
    filetab = FileTab(filedataset)
    plotwindow = PlotWindow("Test Window", filetab.dock)
    plotwindow._test_dataset = filedataset
    app._test_tab = filetab
    app._test_window = plotwindow
    return plotwindow


def test_add_first_channel(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")


def test_add_channel_existing_vbox(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_ox")
    plotwindow.add_channel(plotwindow._test_dataset, "pc1")


def test_add_channel_new_vbox(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.add_channel(plotwindow._test_dataset, "t_inj_fl")


def test_remove_channel(qtbot, plotwindow):
    c = plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_ox")
    plotwindow.remove_channel(c)


def test_separate_y_axis(qtbot, plotwindow):
    c = plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_ox")
    plotwindow.separate_channel_y_axis(c)


def test_legend(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.show_legend()
    qtbot.wait(1)
    plotwindow.set_numeric_in_legend(True)
    qtbot.wait(1)
    plotwindow.set_numeric_in_legend(False)
    qtbot.wait(1)
    plotwindow.hide_legend()
    qtbot.wait(1)


def test_cursor(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.show_cursor()
    qtbot.wait(1)
    plotwindow.hide_cursor()
    qtbot.wait(1)


def test_region(qtbot, plotwindow):
    plotwindow.add_channel(plotwindow._test_dataset, "p_inj_fl")
    plotwindow.show_region()
    qtbot.wait(1)
    for m in MEASUREMENTS:
        plotwindow.region.set_measurement_enabled(m.KEY, True)
    qtbot.wait(1)
    plotwindow.hide_region()
    qtbot.wait(1)
