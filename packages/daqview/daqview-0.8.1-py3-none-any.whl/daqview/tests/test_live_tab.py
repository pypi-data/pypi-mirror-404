# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

from daqview.views.tab import LiveTab


def test_add_channel_chart(app, qtbot):
    app.tab = LiveTab()
    app.tab.add_channel_chart("p_inj_ox")
    qtbot.wait(1)


def test_add_channel_readout(app, qtbot):
    app.tab = LiveTab()
    app.tab.add_channel_readout("p_inj_ox")
    qtbot.wait(1)


def test_add_group_chart(app, qtbot):
    app.tab = LiveTab()
    app.tab.add_group_chart("inj")
    qtbot.wait(1)
    app.tab.add_group_chart("ungrouped")
    qtbot.wait(1)


def test_add_group_readout(app, qtbot):
    app.tab = LiveTab()
    app.tab.add_group_readout("p")
    qtbot.wait(1)
