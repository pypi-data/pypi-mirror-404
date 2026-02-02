import logging
from pyqtgraph.dockarea import DockArea, Dock
from PySide6.QtWidgets import QApplication, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QObject, Signal

from .plot_window import PlotWindow
from .readout_window import ReadoutWindow
from .fft_window import FftWindow

logger = logging.getLogger(__name__)


class TabDock(QObject):
    """
    Manages a DockArea and contains many PlotWindows and ReadoutWindows.

    Signals:
    channels_changed: emitted when the displayed channels changes, due to
                      an addition or deletion.
    windows_changed: emitted when the displayed windows change
    """
    channels_changed = Signal()
    windows_changed = Signal()

    def __init__(self, is_live_tab=False):
        super().__init__()
        self.app = QApplication.instance()
        self.is_live_tab = is_live_tab
        self.dock_area = DockArea()
        self.child_name_ctrs = {"Plot": 1, "Readout": 1}

        # Store list of child dock plots
        self.windows = []

        # Ensure dock fills all available space
        self.dock_area.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                                 QSizePolicy.Expanding,
                                                 QSizePolicy.DefaultType))

        # Show the initial help text
        self.help_dock = None
        self.maybe_show_help_text()

        # When server connects we might need to update the help text
        self.app.server.connected.connect(self._server_connected)

    def maybe_show_help_text(self):
        """
        If no docks are currently being displayed, show a help text.
        Otherwise, removes the help text.
        """
        if not self.windows:
            if self.help_dock:
                self.help_dock.close()
            self.help_dock = Dock("Empty Dock")
            self.help_dock.hideTitleBar()
            connected = self.app.server.is_connected()
            if self.is_live_tab and not connected:
                help_lbl = QLabel(
                    "Connect to a server or open a local dataset "
                    "to get started.")
            else:
                help_lbl = QLabel(
                    "Use the Channels menu to add the first chart.")
            help_lbl.setAlignment(Qt.AlignCenter)
            self.help_dock.addWidget(help_lbl)
            self.dock_area.addDock(self.help_dock)
        elif self.help_dock:
            self.help_dock.close()
            self.help_dock = None

    def _server_connected(self, connected):
        self.maybe_show_help_text()

    def new_plot_window(self, name=None):
        """
        Create a new PlotWindow and add it to this TabDock.

        Returns the new PlotWindow.
        """
        if name is None:
            name = "Plot"
        name = self._unique_window_name(name)
        window = PlotWindow(name, self)
        window.closed.connect(self._window_closed)
        window.channels_changed.connect(self._window_channels_changed)
        window.name_changed.connect(self._window_name_changed)
        self.dock_area.addDock(window.dock)
        self.windows.append(window)
        self.maybe_show_help_text()
        self.windows_changed.emit()
        return window

    def new_readout_window(self, name=None):
        """
        Create a new ReadoutWindow and add it to this TabDock.

        Returns the new ReadoutWindow.
        """
        if name is None:
            name = "Readout"
        name = self._unique_window_name(name)
        window = ReadoutWindow(name, self)
        window.closed.connect(self._window_closed)
        window.channels_changed.connect(self._window_channels_changed)
        window.name_changed.connect(self._window_name_changed)
        self.dock_area.addDock(window.dock)
        self.windows.append(window)
        self.maybe_show_help_text()
        self.windows_changed.emit()
        return window

    def get_fft_window(self):
        """
        Get the FftWindow for this TabDock, or create a new one if none are
        currently being displayed.

        Returns the new FftWindow.
        """
        for window in self.windows:
            if isinstance(window, FftWindow):
                return window
        window = FftWindow("FFT", self)
        window.closed.connect(self._window_closed)
        window.channels_changed.connect(self._window_channels_changed)
        window.name_changed.connect(self._window_name_changed)
        self.dock_area.addDock(window.dock)
        self.windows.append(window)
        self.maybe_show_help_text()
        self.windows_changed.emit()
        return window

    def fft_channel_present(self, channel_id):
        """
        Returns whether a given channel ID is currently being shown in the
        FFT window. If no FFT window is active, returns False.
        """
        for window in self.windows:
            if isinstance(window, FftWindow):
                return window.channel_present(channel_id)
        return False

    def live_channels(self):
        """
        Returns a list of all live channels in all PlotWindows in this
        TabDock.
        """
        return list(set(sum((w.live_channels() for w in self.windows), [])))

    def allow_rename(self, new_name):
        """
        Check if a `new_name` is not already used.
        """
        return not any(w.name == new_name for w in self.windows)

    def serialise(self):
        logger.info("Serialising TabDock")
        return {
            "state": self.dock_area.saveState(),
            "windows": [w.serialise() for w in self.windows]
        }

    def deserialise(self, layout):
        """
        Restore windows from a saved layout.
        layout: the `dock` item from a layout.
        """
        logger.info("Deserialising TabDock")
        for w in self.windows[:]:
            w.close()
        for window in layout['windows']:
            if window['type'] == "plot":
                self.new_plot_window(name=window['name'])
            elif window['type'] == "readout":
                self.new_readout_window(name=window['name'])
        for w, window in zip(self.windows, layout['windows']):
            # We create all the windows before deserliasing any so that
            # x-axis links can be created successfully.
            w.deserialise(window)
        self.dock_area.restoreState(layout['state'])

    def _window_channels_changed(self):
        self.channels_changed.emit()

    def _window_name_changed(self):
        self.windows_changed.emit()

    def _window_closed(self, window):
        logger.info("Window closed: %s", window.name)
        for w in self.windows:
            if not isinstance(w, PlotWindow):
                continue
            if w.vb.x_mode == "link" and w.vb.x_link_vb == window.vb:
                logger.info("Window %s was linked to closing window, setting "
                            "to manual.", w.name)
                w.vb.set_x_mode("manual")
        self.windows.remove(window)
        self.maybe_show_help_text()
        self.channels_changed.emit()
        self.windows_changed.emit()

    def _unique_window_name(self, name):
        if name not in self.child_name_ctrs:
            self.child_name_ctrs[name] = 2
        else:
            ctr = self.child_name_ctrs[name]
            self.child_name_ctrs[name] += 1
            name = name + " " + str(ctr)
        return name
