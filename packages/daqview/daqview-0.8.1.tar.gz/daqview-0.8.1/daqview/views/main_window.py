import os
import logging
import traceback
import webbrowser
import yaml

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QLabel,
                               QLineEdit, QInputDialog, QApplication,
                               QErrorMessage, QMenu, QMessageBox, QFileDialog)
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import Slot, ClassInfo, Qt
from PySide6.QtDBus import QDBusAbstractAdaptor, QDBusMessage

from ..models.file_dataset import FileDataset
from .about_dialog import AboutDialog
from .create_derived_channel_dialog import CreateDerivedChannelDialog
from .channel_list import ChannelListDialog
from .tab import LiveTab, FileTab
from .file_metadata import FileMetadata
from .sequence_generator_dialog import SequenceGeneratorDialog

logger = logging.getLogger(__name__)


@ClassInfo({
    'D-Bus Interface': 'org.freedesktop.Application',
    'D-Bus Introspection': """
        <interface name="org.freedesktop.Application">
          <method name='Activate'>
            <arg type='a{sv}' name='platform_data' direction='in'/>
          </method>
          <method name='Open'>
            <arg type='as' name='uris' direction='in'/>
            <arg type='a{sv}' name='platform_data' direction='in'/>
          </method>
          <method name='ActivateAction'>
            <arg type='s' name='action_name' direction='in'/>
            <arg type='av' name='parameter' direction='in'/>
            <arg type='a{sv}' name='platform_data' direction='in'/>
          </method>
        </interface>""",
    })
class MainWindowDBusAdaptor(QDBusAbstractAdaptor):
    def __init__(self, parent):
        super().__init__(parent)

    @Slot(QDBusMessage)
    def Activate(self, msg):
        logger.info("DBus activation request received")
        self.parent().raise_to_front()

    @Slot(QDBusMessage)
    def Open(self, msg):
        uris = msg.arguments()[0]
        logger.info("DBus open request received for URIs %s", uris)
        for uri in uris:
            if uri.startswith("file://"):
                path = uri[7:]
                logger.info("Opening path from URI: %s", path)
                self.parent().generic_open(path)
            else:
                logger.warning("Cannot handle URI %s", uri)
        self.parent().raise_to_front()

    @Slot(QDBusMessage)
    def ActivateAction(self, msg):
        logger.info("DBus activate action request received")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.init_ui()
        self.setAcceptDrops(True)
        self.__dbusAdaptor = MainWindowDBusAdaptor(self)

    def init_ui(self):
        self.setWindowTitle("DAQview")
        self.init_menus()
        self.init_status_bar()
        self.init_tabs()
        self.statusBar().showMessage("Ready")

    def init_menus(self):
        self.menuBar().setNativeMenuBar(False)
        self.init_file_menu()
        self.init_channels_menu()
        self.init_server_menu()
        self.init_sequencing_menu()
        self.init_help_menu()

    def init_file_menu(self):
        file_menu = self.menuBar().addMenu('&File')

        open_local = QAction('&Open Dataset...', file_menu)
        open_local.setShortcut(QKeySequence.Open)
        open_local.triggered.connect(self.open_datasets)
        file_menu.addAction(open_local)

        self.open_recent_dataset_menu = QMenu('Open &Recent Dataset')
        self.open_recent_dataset_menu.aboutToShow.connect(
            self.set_open_recent_dataset_menu)
        file_menu.addMenu(self.open_recent_dataset_menu)

        save_local = QAction('&Save Dataset...', file_menu)
        save_local.setEnabled(False)
        save_local.setShortcut(QKeySequence.Save)
        file_menu.addAction(save_local)

        meta_local = QAction('View Dataset &Metadata...', file_menu)
        meta_local.setEnabled(False)
        meta_local.triggered.connect(self.view_dataset_meta)
        file_menu.addAction(meta_local)
        self.file_menu_meta_local = meta_local

        close_local = QAction('&Close Dataset', file_menu)
        close_local.setShortcut(QKeySequence.Close)
        close_local.triggered.connect(self.close_dataset)
        file_menu.addAction(close_local)
        self.file_menu_close_local = close_local

        file_menu.addSeparator()

        apply_layout = QAction('Apply Layout...', file_menu)
        apply_layout.triggered.connect(self.apply_layout)
        file_menu.addAction(apply_layout)

        self.copy_layout_menu = QMenu('Copy Layout', file_menu)
        self.copy_layout_menu.aboutToShow.connect(
            self.set_copy_layout_menu)
        file_menu.addMenu(self.copy_layout_menu)

        self.apply_recent_layout_menu = QMenu('Apply Recent Layout', file_menu)
        self.apply_recent_layout_menu.aboutToShow.connect(
            self.set_apply_recent_layout_menu)
        file_menu.addMenu(self.apply_recent_layout_menu)

        save_layout = QAction('Save Current Layout...', file_menu)
        save_layout.triggered.connect(self.save_layout)
        file_menu.addAction(save_layout)

        file_menu.addSeparator()

        export_image = QAction('Export Image...', file_menu)
        export_image.triggered.connect(self.export_image)
        file_menu.addAction(export_image)

        file_menu.addSeparator()

        prefs = QAction('&Preferences...', file_menu)
        prefs.setEnabled(False)
        prefs.setShortcut(QKeySequence.Preferences)
        file_menu.addAction(prefs)

        file_menu.addSeparator()

        exit_ = QAction('&Exit', self)
        exit_.triggered.connect(self.close)
        exit_.setShortcut(QKeySequence.Quit)
        file_menu.addAction(exit_)

    def set_recents_menu(self, menu, name, func):
        """
        Populate generic 'recents' menu keyed with 'name',
        which trigger 'func' with the recent item when clicked.
        """
        menu.clear()
        recents = self.app.prefs.get_recents(name)[::-1]
        if not recents:
            logger.info("No recent %s", name)
            action = QAction(f"No recent {name}", menu)
            action.setEnabled(False)
            menu.addAction(action)
        else:
            for item in recents:
                filename = os.path.split(item)[1]
                action = QAction(filename, menu)

                def wrapper(*args, item=item):
                    return func(item)

                action.triggered.connect(wrapper)
                menu.addAction(action)

    def set_open_recent_dataset_menu(self):
        """
        Populate the 'Recent Datasets' menu with recently opened datasets.
        """
        logger.info("Populating recent datasets menu")
        self.set_recents_menu(self.open_recent_dataset_menu, 'datasets',
                              lambda ds: self.open_dataset(fname=ds))

    def set_copy_layout_menu(self):
        """
        Populate the 'Copy Layout' menu with open tabs.
        """
        logger.info("Populating copy layout menu")
        self.copy_layout_menu.clear()
        for idx in range(1, self.tabs.count()):
            tab = self.tabs.widget(idx)
            action = QAction(tab.name, self.copy_layout_menu)
            if idx == self.tabs.currentIndex():
                action.setEnabled(False)

            def wrapper(*args, tab=tab):
                current_tab = self.tabs.currentWidget()
                layout = tab.serialise()
                for window in layout['dock']['windows']:
                    for channel in window['channels']:
                        channel['dataset'] = current_tab.dataset.name()
                current_tab.dataset.deserialise(layout['dataset'])
                current_tab.deserialise(layout)

            action.triggered.connect(wrapper)
            self.copy_layout_menu.addAction(action)

    def set_apply_recent_layout_menu(self):
        """
        Populate the 'Apply Recent Layout' menu with recently applied layouts.
        """
        logger.info("Populating recent layouts menu")
        self.set_recents_menu(self.apply_recent_layout_menu, 'layouts',
                              lambda ds: self.apply_layout(fname=ds))

    def init_channels_menu(self):
        channels_menu = self.menuBar().addMenu('&Channels')

        self.add_channel_chart_menu = QMenu('Add Channel Chart')
        self.add_channel_chart_menu.aboutToShow.connect(
            self.set_add_channel_chart_menu)
        channels_menu.addMenu(self.add_channel_chart_menu)

        self.add_channel_readout_menu = QMenu('Add Channel Readout')
        self.add_channel_readout_menu.aboutToShow.connect(
            self.set_add_channel_readout_menu)
        channels_menu.addMenu(self.add_channel_readout_menu)

        create_derived_ch = QAction("Create Derived Channel...",
                                    channels_menu)
        create_derived_ch.triggered.connect(self.create_derived_channel)
        channels_menu.addAction(create_derived_ch)

        # self.add_channel_control_menu = QMenu('Add Channel Control')
        # self.add_channel_control_menu.setEnabled(False)
        # channels_menu.addMenu(self.add_channel_control_menu)

        self.channels_menu = channels_menu

    def create_derived_channel(self):
        current_tab = self.tabs.currentWidget()
        dialog = CreateDerivedChannelDialog(current_tab.dataset, self)
        dialog.show()

    def open_datasets(self, *args, fnames=None):
        with self.app.server.updates_paused():
            if fnames is None:
                fnames = QFileDialog.getOpenFileNames(
                    self,
                    "Open Local Dataset...", "", "Data File (*.h5 *.hdf5)",
                    "")[0]
            if not fnames:
                logger.info("No file(s) provided, not opening dataset")
                return
            for fname in fnames:
                self.open_dataset(fname=fname)

    def open_dataset(self, *args, fname):
        with self.app.server.updates_paused():
            if not fname:
                logger.info("No file provided, not opening dataset")
                return
            if not os.path.isfile(fname):
                logger.info("Couldn't open non-existant file '%s'", fname)
                error = QErrorMessage(self)
                error.setModal(True)
                error.showMessage(f"File cannot be opened or doesn't exist:\n{fname}")
                return
            logger.info("Opening local dataset '%s'", fname)
            self.app.prefs.add_recent_dataset(fname)
            file_dataset = FileDataset(fname)
            file_tab = FileTab(file_dataset)
            tab_idx = self.tabs.addTab(file_tab, file_tab.name)
            self.tabs.setCurrentIndex(tab_idx)
            return file_dataset

    def view_dataset_meta(self):
        tab = self.tabs.currentWidget()
        metadata = tab.dataset.get_file_metadata()
        self.metadata_dialog = FileMetadata(metadata)
        self.metadata_dialog.show()

    def close_dataset(self, *args):
        tab = self.tabs.currentWidget()
        tab.close()
        self.tabs.removeTab(self.tabs.currentIndex())

    def save_layout(self, *args, fname=None):
        with self.app.server.updates_paused():
            layout = self.tabs.currentWidget().serialise()
            if fname is None:
                fname = QFileDialog.getSaveFileName(
                    self,
                    "Save Layout As...", "", "Layout File (*.yml)", "")[0]
                if fname != "" and not fname.endswith(".yml"):
                    fname = fname + ".yml"
            if not fname:
                logger.info("No file provided, not saving layout")
                return
            logger.info("Saving layout to '%s'", fname)
            with open(fname, "w") as f:
                f.write(yaml.safe_dump(layout))
            self.app.prefs.add_recent_layout(fname)

    def apply_layout(self, *args, fname=None):
        with self.app.server.updates_paused():
            if fname is None:
                fname = QFileDialog.getOpenFileName(
                    self, "Apply Layout...", "", "Layout File (*.yml)", "")[0]
            if not fname:
                logger.info("No file provided, not applying layout")
                return False
            logger.info("Applying layout from '%s'", fname)
            self.app.prefs.add_recent_layout(fname)
            with open(fname) as f:
                layout = yaml.safe_load(f.read())
            try:
                tab = self.tabs.currentWidget()
                # Patch dataset name
                for window in layout['dock']['windows']:
                    for channel in window['channels']:
                        channel['dataset'] = tab.dataset.name()
                tab.dataset.deserialise(layout['dataset'])
                tab.deserialise(layout)
            except (KeyError, ValueError) as e:
                logger.error("Error loading layout: %s", e)
                traceback.print_exc()
                error = QErrorMessage(self)
                error.setModal(True)
                error.showMessage("Error while applying layout: " + str(e))
                return False
            else:
                return True

    def export_image(self, *args, fname=None):
        with self.app.server.updates_paused():
            pixmap = self.tabs.currentWidget().grab()
            if fname is None:
                fname = QFileDialog.getSaveFileName(
                    self, "Export as...", "", "Images (*.png *.jpg *.bmp)",
                    "")[0]
            if not fname:
                logger.info("No file provided, not saving image")
                return
            if os.path.splitext(fname)[1] == "":
                fname = fname + ".png"
            logger.info("Saving image to '%s'", fname)
            pixmap.save(fname)

    def init_server_menu(self):
        server_menu = self.menuBar().addMenu('&Server')

        connect = QAction('&Connect...', server_menu)
        connect.triggered.connect(self.show_connect_dialogue)
        self.app.server.connected.connect(connect.setDisabled)
        server_menu.addAction(connect)

        reconnect = QAction('&Reconnect', server_menu)
        reconnect.setEnabled(False)
        reconnect.triggered.connect(self.app.server.reconnect)
        self.app.server.connected.connect(reconnect.setEnabled)
        server_menu.addAction(reconnect)

        disconnect = QAction('&Disconnect', server_menu)
        disconnect.setEnabled(False)
        disconnect.triggered.connect(self.app.server.disconnect_from_host)
        self.app.server.connected.connect(disconnect.setEnabled)
        server_menu.addAction(disconnect)

        server_menu.addSeparator()

        zero = QAction('Zero Timestamps', server_menu)
        zero.setEnabled(False)
        zero.triggered.connect(self.zero_timestamps)
        self.app.server.connected.connect(zero.setEnabled)
        server_menu.addAction(zero)

        clear = QAction('Clear Live Data', server_menu)
        clear.setEnabled(False)
        clear.triggered.connect(self.confirm_clear_data)
        self.app.server.connected.connect(clear.setEnabled)
        server_menu.addAction(clear)

        save = QAction('Save Live Data...', server_menu)
        save.triggered.connect(self.save_live_data)
        server_menu.addAction(save)

        server_menu.addSeparator()

        view_channels = QAction('View Channel &List...', server_menu)
        view_channels.setEnabled(False)
        view_channels.triggered.connect(self.view_channels)
        self.app.server.connected.connect(view_channels.setEnabled)
        server_menu.addAction(view_channels)

        view_config = QAction('View Server Config...', server_menu)
        view_config.setEnabled(False)
        # self.app.server.connected.connect(view_config.setEnabled)
        server_menu.addAction(view_config)

        view_browser = QAction('View In &Browser', server_menu)
        view_browser.setEnabled(False)
        self.app.server.connected.connect(view_browser.setEnabled)
        view_browser.triggered.connect(self.view_browser)
        server_menu.addAction(view_browser)

        server_menu.addSeparator()

        load_remote = QAction('Load Remote Dataset...', server_menu)
        load_remote.setEnabled(False)
        # self.app.server.connected.connect(load_remote.setEnabled)
        server_menu.addAction(load_remote)

        self.server_menu = server_menu

    def show_connect_dialogue(self):
        host, ok = QInputDialog.getText(
            self, 'Connect To Server', 'Server:',
            QLineEdit.Normal, self.app.server.last_host)
        if ok:
            self.app.server.connect_to_host(host)

    def zero_timestamps(self):
        logger.info("Zeroing timestamps in live dataset")
        self.app.server.live_data.zero_timestamps()

    def confirm_clear_data(self):
        choice = QMessageBox.question(
            self, "Confirm Clear Data",
            "Are you sure you want to clear all live data?",
            QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            self.app.server.live_data.clear_data()

    def save_live_data(self, *args, fname=None):
        with self.app.server.updates_paused():
            if fname is None:
                fname = QFileDialog.getSaveFileName(
                    self,
                    "Save Live Data As...", "", "Data File (*.h5)", "")[0]
                if not fname.endswith(".h5"):
                    fname = fname + ".h5"
            if not fname:
                logger.info("No file provided, not saving live data")
                return
            logger.info("Saving live data to '%s'", fname)
            self.app.server.live_data.save_data(fname)

    def view_channels(self):
        if self.app.server.channels_table:
            self.channels_dialog = ChannelListDialog()
            self.channels_dialog.show()
        else:
            error = QErrorMessage(self)
            error.setModal(True)
            error.showMessage('Could not load channel list. Try reconnecting.')

    def view_browser(self):
        if self.app.server.host:
            webbrowser.open("http://{}".format(self.app.server.host))
        else:
            error = QErrorMessage(self)
            error.setModal(True)
            error.showMessage('Could not find server URL. Try reconnecting.')

    def init_status_bar(self):
        self.server_status = QLabel("Disconnected", self.statusBar())
        self.app.server.connected.connect(self.update_server_status)
        self.statusBar().insertPermanentWidget(0, self.server_status)
        self.server_time = QLabel("", self.statusBar())
        self.last_server_time = None
        self.app.server.time_update.connect(self.update_server_time)
        self.statusBar().insertPermanentWidget(0, self.server_time)
        self.statusBar().showMessage("Ready")

    def update_server_status(self, connected):
        if connected:
            self.server_status.setText("Connected")
        else:
            self.server_status.setText("Disconnected")
            self.server_time.setText("")

    def update_server_time(self, time):
        try:
            time = int(time)
        except ValueError:
            return
        if time != self.last_server_time:
            text = "Server Time: {}s".format(time)
            offset = self.app.server.live_data.t_offset
            if offset is not None:
                text += " (time offset: -{}s)".format(offset)
            self.server_time.setText(text)
            self.last_server_time = time

    def init_sequencing_menu(self):
        seq_menu = self.menuBar().addMenu('Sequencing')

        tpl_edit = QAction('&Template Editor...', seq_menu)
        tpl_edit.setEnabled(False)
        seq_menu.addAction(tpl_edit)

        seq_gen = QAction('&Sequence Generator...', seq_menu)
        seq_gen.setEnabled(True)
        seq_gen.setShortcut(QKeySequence("Ctrl+G"))
        seq_gen.triggered.connect(self.show_seq_gen)
        seq_menu.addAction(seq_gen)

        self.seq_menu = seq_menu

    def show_seq_gen(self):
        seq_gen = SequenceGeneratorDialog(self)
        seq_gen.open()

    def init_help_menu(self):
        help_menu = self.menuBar().addMenu('&Help')

        about = QAction('&About...', help_menu)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

        self.help_menu = help_menu

    def show_about(self):
        about = AboutDialog(self)
        about.show()

    def init_tabs(self):
        self.tabs = QTabWidget(self)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.live_tab = LiveTab()
        self.tabs.addTab(self.live_tab, self.live_tab.name)
        self.setCentralWidget(self.tabs)

    def tab_changed(self, _index):
        current_tab = self.tabs.currentWidget()

        if isinstance(current_tab, LiveTab):
            self.server_menu.setEnabled(True)
            self.file_menu_close_local.setEnabled(False)
            self.file_menu_meta_local.setEnabled(False)
            self.add_channel_readout_menu.setEnabled(True)
            self.copy_layout_menu.setEnabled(False)
        else:
            self.server_menu.setEnabled(False)
            self.file_menu_close_local.setEnabled(True)
            self.file_menu_meta_local.setEnabled(True)
            self.copy_layout_menu.setEnabled(True)
            self.add_channel_readout_menu.setEnabled(False)

    def set_add_channel_chart_menu(self):
        """
        Populate the "Add Channel Chart" menu with all the channel groups
        from the currently selected tab.
        """
        self.add_channel_chart_menu.clear()
        current_tab = self.tabs.currentWidget()
        current_tab.set_channel_chart_menus(self.add_channel_chart_menu)

    def set_add_channel_readout_menu(self):
        """
        Populate the "Add Channel Readout" menu with all the channel groups
        from the currently selected tab.
        """
        self.add_channel_readout_menu.clear()
        current_tab = self.tabs.currentWidget()
        current_tab.set_channel_readout_menus(self.add_channel_readout_menu)

    def dragEnterEvent(self, e):
        logger.info("Drag event")
        for url in e.mimeData().urls():
            fname = url.toLocalFile()
            if any(fname.endswith(x) for x in (".h5", ".yaml", ".yml")):
                logger.info("Accepting file %s", fname)
                e.accept()
                return

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            fname = url.toLocalFile()
            logger.info("Processing dropped URL %s", fname)
            self.generic_open(fname)

    def generic_open(self, fname):
        if fname.endswith(".h5"):
            self.open_dataset(fname=fname)
        elif fname.endswith(".yml") or fname.endswith(".yaml"):
            self.open_layout(fname=fname)
        else:
            logger.warning("Unknown file type for %s", fname)

    def raise_to_front(self):
        self.setWindowState(
            self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
