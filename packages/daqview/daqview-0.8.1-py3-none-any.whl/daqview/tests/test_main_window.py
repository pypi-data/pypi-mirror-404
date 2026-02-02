# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

from daqview.views.main_window import MainWindow
from daqview.views.about_dialog import AboutDialog


def test_init(app, qtbot):
    w = MainWindow()
    w.show()


def test_local_dataset(app, qtbot, h5):
    w = MainWindow()
    w.show()
    w.open_dataset(fname=h5)
    assert app.datasets['Mock Dataset']
    assert h5 in app.prefs.get_recent_datasets()
    qtbot.wait(1)
    w.view_dataset_meta()
    qtbot.wait(1)
    w.close_dataset()


def test_open_dataset_cancelled(app, qtbot):
    w = MainWindow()
    w.show()
    w.open_dataset(fname="")
    qtbot.wait(1)


def test_apply_layout_file(app, qtbot, layout_file, h5):
    w = MainWindow()
    w.show()
    w.open_dataset(fname=h5)
    qtbot.wait(1)
    assert w.apply_layout(fname=layout_file)
    qtbot.wait(1)
    assert layout_file in app.prefs.get_recent_layouts()


def test_apply_layout_server(app, qtbot, layout_server):
    w = MainWindow()
    w.show()
    assert w.apply_layout(fname=layout_server)
    qtbot.wait(1)
    assert app.server.is_connected()


def test_save_layout(app, qtbot, layout_file, tmpdir):
    w = MainWindow()
    w.show()
    w.apply_layout(fname=layout_file)
    qtbot.wait(1)
    path = str(tmpdir.join("saved_layout.yml"))
    w.save_layout(fname=path)


def test_save_layout_cancelled(app, qtbot):
    w = MainWindow()
    w.show()
    w.save_layout(fname="")
    qtbot.wait(1)


def test_about(app, qtbot):
    # We can't use w.show_about() because it calls exec_ which will block.
    d = AboutDialog()
    d.show()


def test_export_image(app, qtbot, layout_file, tmpdir):
    w = MainWindow()
    w.show()
    w.apply_layout(fname=layout_file)
    qtbot.wait(1)
    path = tmpdir.join("main_window.jpg")
    w.export_image(fname=str(path))


def test_export_image_cancelled(app, qtbot):
    w = MainWindow()
    w.show()
    w.export_image(fname="")
    qtbot.wait(1)


def test_view_channels(app, qtbot, daqserver):
    app.server.connect_to_host(daqserver)
    w = MainWindow()
    w.show()
    with qtbot.waitSignal(app.server.time_update):
        pass
    w.view_channels()
    qtbot.wait(1)
