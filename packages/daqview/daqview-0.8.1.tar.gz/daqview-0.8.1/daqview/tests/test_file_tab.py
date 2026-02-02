# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.models.file_dataset import FileDataset
from daqview.views.tab import FileTab


@pytest.fixture
def filedataset(app, h5):
    return FileDataset(h5)


def test_add_channel_chart(qtbot, filedataset):
    tab = FileTab(filedataset)
    tab.add_channel_chart("p_inj_ox")


def test_add_channel_readout(qtbot, filedataset):
    tab = FileTab(filedataset)
    tab.add_channel_readout("p_inj_ox")
    qtbot.wait(1)


def test_add_group_chart(qtbot, filedataset):
    tab = FileTab(filedataset)
    tab.add_group_chart("inj")
    qtbot.wait(1)
    tab.add_group_chart("ungrouped")
    qtbot.wait(1)


def test_add_group_readout(qtbot, filedataset):
    tab = FileTab(filedataset)
    tab.add_group_readout("p")
    qtbot.wait(1)
