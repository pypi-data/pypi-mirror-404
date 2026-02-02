# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

import pytest
from daqview.views.sequence_generator_dialog import SequenceGeneratorDialog


@pytest.fixture
def sgdialog(app, sequence_template):
    d = SequenceGeneratorDialog()
    d.read_cfg_file(fname=sequence_template)
    return d


def test_show(sgdialog, qtbot, app):
    sgdialog.show()
    qtbot.wait(1)
