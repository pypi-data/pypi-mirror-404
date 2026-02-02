import logging
import pyqtgraph as pg
import numpy as np

from .fft_menus import FftContextMenu

logger = logging.getLogger(__name__)


class FftViewBox(pg.ViewBox):
    """
    Custom ViewBox which uses a FftContextMenu without any parent context
    menus, and has a few patched members.
    """

    def __init__(self, fw):
        super().__init__()
        self.fw = fw

        self.x_axis = None
        self.x_mouse = False
        self.x_grid = False
        self.x_logscale = False
        self.x_manual_from = None
        self.x_manual_to = None

        self.y_axis = None
        self.y_mouse = False
        self.y_grid = False
        self.y_manual_from = None
        self.y_manual_to = None

        self.set_x_mouse(True)
        self.set_y_mouse(False)
        self.sigXRangeChanged.connect(self.x_range_changed)

        self.menu = FftContextMenu(self)

    def configure(self):
        """
        Configure the ViewBox once x-axis and y-axis have been set.
        """
        self.x_axis.setLabel("Frequency", "Hz")
        self.y_axis.setLabel("Magnitude", "dB")
        self.x_axis.enableAutoSIPrefix(True)
        self.y_axis.enableAutoSIPrefix(False)
        self.x_axis.setStyle(textFillLimits=[])
        # self.set_x_logscale(True)

    def get_manual_x_range(self):
        return (self.x_manual_from, self.x_manual_to)

    def get_x_manual_from(self):
        return self.get_manual_x_range()[0]

    def get_x_manual_to(self):
        return self.get_manual_x_range()[1]

    def set_manual_x_range(self, manual_from, manual_to):
        self.setXRange(manual_from, manual_to, padding=0)

    def update_manual_x_range(self, manual_from, manual_to):
        self.x_manual_from = manual_from
        self.x_manual_to = manual_to

    def x_range_changed(self, _linked_vb, viewrange):
        xmin, xmax = viewrange
        self.update_manual_x_range(float(xmin), float(xmax))

    def get_x_range(self):
        return self.viewRange()[0]

    def get_x_mouse(self):
        return self.x_mouse

    def set_x_mouse(self, mouse):
        self.x_mouse = mouse
        self.setMouseEnabled(x=mouse)

    def get_x_grid(self):
        return self.x_grid

    def set_x_grid(self, grid):
        self.x_grid = grid
        if self.x_axis is not None:
            self.x_axis.setGrid(255 if grid else False)

    def get_x_logscale(self):
        return self.x_logscale

    def set_x_logscale(self, logscale):
        self.x_logscale = logscale
        self.setLogMode('x', self.x_logscale)
        self.x_axis.setLogMode(x=self.x_logscale)
        self.fw.pi.setLogMode(x=self.x_logscale)
        for channel in self.fw.channels:
            channel.pdi.setLogMode(self.x_logscale, False)

    def get_manual_y_range(self):
        return (self.y_manual_from, self.y_manual_to)

    def get_y_manual_from(self):
        return self.get_manual_y_range()[0]

    def get_y_manual_to(self):
        return self.get_manual_y_range()[1]

    def set_manual_y_range(self, manual_from, manual_to):
        self.y_manual_from = manual_from
        self.y_manual_to = manual_to
        self.setYRange(manual_from, manual_to, padding=0)

    def update_manual_y_range(self, manual_from, manual_to):
        self.y_manual_from = manual_from
        self.y_manual_to = manual_to

    def get_y_mouse(self):
        return self.y_mouse

    def set_y_mouse(self, mouse):
        self.y_mouse = mouse
        self.setMouseEnabled(y=mouse)

    def get_y_grid(self):
        return self.y_grid

    def set_y_grid(self, grid):
        self.y_grid = grid
        if self.y_axis is not None:
            self.y_axis.setGrid(255 if grid else False)

    def get_y_range(self):
        return self.viewRange()[1]

    def raiseContextMenu(self, ev):
        # Overridden to just show our menu, without adding any
        # parent menus.
        self.menu.popup(ev.screenPos().toPoint())

    def updateViewLists(self):
        # Patched out to avoid calling setViewList on self.menu,
        # which doesn't have one in our case.
        pass

    def wheelEvent(self, ev, axis=None):
        # Patch ViewBox to prevent mouse wheel events disabling autorange when
        # the mouse interaction is disabled for that axis.
        # We reimplement wheelEvent to pass scales to scaleBy for each axis.
        # See pyqtgraph #439
        sf = self.state['wheelScaleFactor']
        scale = np.array((1.02, 1.02)) ** (ev.delta() * sf)
        centre = pg.functions.invertQTransform(self.childGroup.transform())
        centre = centre.map(ev.pos())
        sx, sy = scale
        en_x, en_y = self.state['mouseEnabled']
        if not en_x:
            sx = None
        if not en_y:
            sy = None
        self._resetTarget()
        self.scaleBy(center=centre, x=sx, y=sy)
        self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        ev.accept()

    def serialise(self):
        logger.info("Serialising PlotViewBox %s (%s, %s)", self.pw.name,
                    self.x_units, self.y_units)
        return {
            "x_axis": {
                "mouse": self.x_mouse,
                "grid": self.x_grid,
                "logscale": self.x_logscale,
                "manual_from": self.x_manual_from,
                "manual_to": self.x_manual_to,
            },
            "y_axis": {
                "mouse": self.y_mouse,
                "grid": self.y_grid,
                "manual_from": self.y_manual_from,
                "manual_to": self.y_manual_to,
            },
        }

    def deserialise(self, layout):
        logger.info("Deserialising PlotViewBox %s (%s, %s)", self.pw.name,
                    layout['x_axis']['units'], layout['y_axis']['units'])

        # Set x-axis options
        self.set_x_mouse(layout['x_axis']['mouse'])
        self.set_x_grid(layout['x_axis']['grid'])
        self.set_x_logscale(layout['x_axis']['logscale'])
        self.set_manual_x_range(layout['x_axis']['manual_from'],
                                layout['x_axis']['manual_to'])

        # Set y-axis options
        self.set_y_mouse(layout['y_axis']['mouse'])
        self.set_y_grid(layout['y_axis']['grid'])
        self.set_manual_y_range(layout['y_axis']['manual_from'],
                                layout['y_axis']['manual_to'])
