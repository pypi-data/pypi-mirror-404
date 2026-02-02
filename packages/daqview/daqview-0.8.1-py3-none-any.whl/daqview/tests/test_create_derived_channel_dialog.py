# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.models.file_dataset import FileDataset
from daqview.views.create_derived_channel_dialog import \
    CreateDerivedChannelDialog


@pytest.fixture
def cdcdialog(h5, app):
    df = FileDataset(h5)
    d = CreateDerivedChannelDialog(df)
    return d


def test_show(cdcdialog, qtbot, app):
    cdcdialog.show()
    qtbot.wait(1)
