import logging
import pyqtgraph as pg
import numpy as np
from PySide6.QtCore import Signal

from ..models.units import quantity_for_unit
from .plot_menus import PlotContextMenu

logger = logging.getLogger(__name__)


class PlotViewBox(pg.ViewBox):
    """
    Custom ViewBox which uses a PlotContextMenu without any parent context
    menus, and has a few patched members.

    PlotViewBoxes are responsible for managing and serialising/deserialising
    the state of their X and Y axes, including the modes of those axes.
    The plot_menus.PlotContextXAxis and plot_menus.PlotContextYAxis interact
    with their parent PlotViewBox to get/set the axis state.

    Signals:
    scale_offset_changed: emitted when the viewbox scale/offset is changed
    """
    scale_offset_changed = Signal()

    def __init__(self, pw):
        super().__init__()
        self.pw = pw

        self.parent_x_vb = None
        self.x_axis = None
        self.x_units = None
        self.x_mode = "last_n"
        self.x_mouse = False
        self.x_grid = False
        self.x_link_idx = None
        self.x_link_vb = None
        self.x_last_n_secs = 60
        self.x_manual_from = None
        self.x_manual_to = None

        self.parent_y_vb = None
        self.y_axis = None
        self.y_units = None
        self.y_mode = "auto_vis"
        self.y_mouse = False
        self.y_grid = False
        self.y_autosi = False
        self.y_manual_from = None
        self.y_manual_to = None
        self.y_scale = 1.0
        self.y_offset = 0.0

        self.setMouseEnabled(x=False, y=False)
        self.sigXRangeChanged.connect(self.x_range_changed)

        self.menu = PlotContextMenu(self)

    def twinx(self, parent_vb, y_units):
        """
        Set this PlotViewBox up to have a new Y-axis and linked X-axis
        to the `parent_vb` PlotViewBox.
        """
        self.parent_x_vb = parent_vb
        self.setXLink(parent_vb)
        self.x_last_n_secs = parent_vb.x_last_n_secs

        # Create new y-axis
        self.y_axis = pg.AxisItem("right")
        self.y_axis.linkToView(self)
        self.pw.glw.addItem(self.y_axis, row=0, col=self.pw.y_axis_next_col)
        self.set_y_units(y_units)

        # Add dummy x-axis for alignment.
        # Without this, the new y-axis is the wrong height relative to the
        # central PlotItem, causing misalignment between axis ticks and data.
        # This isn't perfect as the dummy axis isn't precisely the same height
        # as the real x-axis, but it seems to be the best workable solution.
        self.dummy_x = pg.AxisItem("bottom")
        self.dummy_x.setPen((0, 0, 0, 0))
        self.dummy_x.setLabel("Dummy")
        self.pw.glw.addItem(self.dummy_x, row=1, col=self.pw.y_axis_next_col)

        # Increment counter for next axis
        self.pw.y_axis_next_col += 1

    def get_x_units(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_units()
        else:
            return self.x_units

    def set_x_units(self, units):
        """Update this PlotViewBox's X units and X-axis label."""
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_units(units)
            self.x_units = self.parent_x_vb.get_x_units()
        else:
            self.x_units = units
            if self.x_axis is not None:
                self.x_axis.setLabel(quantity_for_unit(units), units)

    def get_y_units(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_units()
        else:
            return self.y_units

    def set_y_units(self, units):
        """Update this PlotViewBox's Y units and Y-axis label."""
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_units(units)
            self.y_units = self.parent_y_vb.get_y_units()
        else:
            self.y_units = units
            if self.y_axis is not None:
                self.y_axis.setLabel(quantity_for_unit(units), units)

    def get_y_scale(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_scale()
        else:
            return self.y_scale

    def set_y_scale(self, scale):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_Scale(scale)
            self.y_scale = self.parent_y_vb.get_y_scale()
        else:
            self.y_scale = scale
        self.scale_offset_changed.emit()

    def get_y_offset(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_offset()
        else:
            return self.y_offset

    def set_y_offset(self, offset):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_offset(offset)
            self.y_offset = self.parent_y_vb.get_y_offset()
        else:
            self.y_offset = offset
        self.scale_offset_changed.emit()

    def get_x_mode(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_mode()
        else:
            return self.x_mode

    def set_x_mode(self, mode, link_idx=None):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_mode(mode, link_idx)
            self.x_mode = self.parent_x_vb.get_x_mode()
            self.x_mouse = self.parent_x_vb.get_x_mouse()
            self.x_link_idx = self.parent_x_vb.get_x_link_idx()
        elif mode == "last_n":
            self.x_mode = mode
            self.x_mouse = False
            self.enableAutoRange(x=False)
            self.setMouseEnabled(x=False)
        elif mode == "all":
            self.x_mode = mode
            self.x_mouse = False
            self.setAutoVisible(x=True)
            self.enableAutoRange(x=True)
            self.setMouseEnabled(x=False)
        elif mode == "link":
            self.x_mode = mode
            self.x_mouse = False
            self.setMouseEnabled(x=False)
            self.enableAutoRange(x=False)
            if link_idx is not None:
                self.x_link_idx = link_idx
                self.x_link_vb = self.pw.parent.windows[link_idx].vb
                self.x_link_vb.sigXRangeChanged.connect(
                    self.x_link_range_changed)
                linked_viewrange = self.x_link_vb.get_manual_x_range()
                self.x_link_range_changed(self.x_link_vb, linked_viewrange)
        elif mode == "manual":
            self.x_mode = mode
            self.enableAutoRange(x=False)
        else:
            logger.warning("Unknown x-mode '%s' requested, ignoring", mode)

        # Trigger an update of the channel data when the mode changes,
        # since otherwise without regular server updates live channels
        # will remain stuck displaying the last n seconds worth of data etc.
        if self.parent_x_vb is None:
            self.pw.update_channel_data()

    def get_x_last_n_secs(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_last_n_secs()
        else:
            return self.x_last_n_secs

    def set_x_last_n_secs(self, last_n):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_last_n_secs(last_n)
            self.x_last_n_secs = self.parent_x_vb.get_x_last_n_secs()
        else:
            self.x_last_n_secs = last_n
            self.pw.update_channel_data()

    def get_manual_x_range(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_manual_x_range()
        else:
            return (self.x_manual_from, self.x_manual_to)

    def get_x_manual_from(self):
        return self.get_manual_x_range()[0]

    def get_x_manual_to(self):
        return self.get_manual_x_range()[1]

    def set_manual_x_range(self, manual_from, manual_to):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_manual_x_range(manual_from, manual_to)
            self.x_manual_from = self.parent_x_vb.get_x_manual_from()
            self.x_manual_to = self.parent_x_vb.get_x_manual_to()
        elif self.x_mode == "manual":
            self.setXRange(manual_from, manual_to, padding=0)

    def update_manual_x_range(self, manual_from, manual_to):
        if self.parent_x_vb is not None:
            self.parent_x_vb.update_manual_x_range(manual_from, manual_to)
            self.x_manual_from = self.parent_x_vb.x_manual_from
            self.x_manual_to = self.parent_x_vb.x_manual_to
        else:
            self.x_manual_from = manual_from
            self.x_manual_to = manual_to

    def x_range_changed(self, _linked_vb, viewrange):
        xmin, xmax = viewrange
        self.update_manual_x_range(float(xmin), float(xmax))

    def get_x_range(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_range()
        else:
            return self.viewRange()[0]

    def x_link_is_last_n(self):
        """
        Check if the current viewbox is in last_n mode, or if its
        link is, or its link's link, etc.
        """
        if self.x_mode == "last_n":
            return True
        elif self.x_mode == "link":
            return self.x_link_vb.x_link_is_last_n()

    def x_link_range_changed(self, linked_vb, viewrange):
        """
        Called when the linked viewbox updates its own XRange,
        we manually set our XRange to match.
        """
        xmin, xmax = viewrange
        if xmin is None or xmax is None:
            return
        if (self.x_mode == "link" and self.x_link_idx is not None
                and linked_vb == self.x_link_vb):
            # If the linked VB is in 'last_n'
            if self.x_link_is_last_n():
                positions = self.pw._save_cursor_region_positions()
            self.setXRange(float(xmin), float(xmax))
            if self.x_link_is_last_n():
                self.pw._restore_cursor_region_positions(positions)
        else:
            linked_vb.sigXRangeChanged.disconnect(self.x_link_range_changed)

    def get_x_mouse(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_mouse()
        else:
            return self.x_mouse

    def set_x_mouse(self, mouse):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_mouse(mouse)
            self.x_mouse = self.parent_x_vb.get_x_mouse()
        else:
            self.x_mouse = mouse
            self.setMouseEnabled(x=mouse)

    def get_x_grid(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_grid()
        else:
            return self.x_grid

    def set_x_grid(self, grid):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_grid(grid)
            self.x_grid = self.parent_x_vb.get_x_grid()
        else:
            self.x_grid = grid
            if self.x_axis is not None:
                self.x_axis.setGrid(255 if grid else False)

    def get_x_link_idx(self):
        if self.parent_x_vb is not None:
            return self.parent_x_vb.get_x_link_idx()
        else:
            return self.x_link_idx

    def set_x_link_idx(self, link_idx=None):
        if self.parent_x_vb is not None:
            self.parent_x_vb.set_x_link_idx(link_idx)
            self.x_link_idx = self.parent_x_vb.get_x_link_idx()
        elif self.x_mode == "link" and link_idx is not None:
            self.x_link_idx = link_idx
            self.x_link_vb = self.pw.parent.windows[link_idx].vb
            self.x_link_vb.sigXRangeChanged.connect(self.x_link_range_changed)
        else:
            self.x_link_idx = None

    def get_y_mode(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_mode()
        else:
            return self.y_mode

    def set_y_mode(self, mode):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_mode(mode)
            self.y_mode = self.parent_y_vb.get_y_mode()
            self.y_mouse = self.parent_y_vb.get_y_mouse()
        elif mode == "auto_vis":
            self.y_mode = mode
            self.y_mouse = False
            self.setAutoVisible(y=True)
            self.enableAutoRange(y=True)
            self.setMouseEnabled(y=False)
        elif mode == "auto_all":
            self.y_mode = mode
            self.y_mouse = False
            self.setAutoVisible(y=False)
            self.enableAutoRange(y=True)
            self.setMouseEnabled(y=False)
        elif mode == "manual":
            self.y_mode = mode
            self.enableAutoRange(y=False)
        else:
            logger.warning("Unknown y-mode '%s' requested, ignoring", mode)

    def get_manual_y_range(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_manual_y_range()
        else:
            return (self.y_manual_from, self.y_manual_to)

    def get_y_manual_from(self):
        return self.get_manual_y_range()[0]

    def get_y_manual_to(self):
        return self.get_manual_y_range()[1]

    def set_manual_y_range(self, manual_from, manual_to):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_manual_y_range(manual_from, manual_to)
            self.y_manual_from = self.parent_y_vb.get_y_manual_from()
            self.y_manual_to = self.parent_y_vb.get_y_manual_to()
        elif self.y_mode == "manual":
            self.y_manual_from = manual_from
            self.y_manual_to = manual_to
            self.setYRange(manual_from, manual_to, padding=0)

    def update_manual_y_range(self, manual_from, manual_to):
        if self.parent_y_vb is not None:
            self.parent_y_vb.update_manual_y_range(manual_from, manual_to)
            self.y_manual_from = self.parent_y_vb.y_manual_from
            self.y_manual_to = self.parent_y_vb.y_manual_to
        else:
            self.y_manual_from = manual_from
            self.y_manual_to = manual_to

    def get_y_mouse(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_mouse()
        else:
            return self.y_mouse

    def set_y_mouse(self, mouse):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_mouse(mouse)
            self.y_mouse = self.parent_y_vb.get_y_mouse()
        else:
            self.y_mouse = mouse
            self.setMouseEnabled(y=mouse)

    def get_y_grid(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_grid()
        else:
            return self.y_grid

    def set_y_grid(self, grid):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_grid(grid)
            self.y_grid = self.parent_y_vb.get_y_grid()
        else:
            self.y_grid = grid
            if self.y_axis is not None:
                self.y_axis.setGrid(255 if grid else False)

    def get_y_autosi(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_autosi()
        else:
            return self.y_autosi

    def set_y_autosi(self, autosi):
        if self.parent_y_vb is not None:
            self.parent_y_vb.set_y_autosi(autosi)
            self.y_autosi = self.parent_y_vb.get_y_autosi()
        else:
            self.y_autosi = autosi
            if self.y_axis is not None:
                self.y_axis.enableAutoSIPrefix(self.y_autosi)

    def get_y_range(self):
        if self.parent_y_vb is not None:
            return self.parent_y_vb.get_y_range()
        else:
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
            "twinx": True if self.parent_x_vb is not None else False,
            "twiny": True if self.parent_y_vb is not None else False,
            "x_axis": {
                "units": self.x_units,
                "mode": self.x_mode,
                "mouse": self.x_mouse,
                "grid": self.x_grid,
                "link_idx": self.x_link_idx,
                "last_n_secs": self.x_last_n_secs,
                "manual_from": self.x_manual_from,
                "manual_to": self.x_manual_to,
            },
            "y_axis": {
                "units": self.y_units,
                "mode": self.y_mode,
                "mouse": self.y_mouse,
                "grid": self.y_grid,
                "autosi": self.y_autosi,
                "manual_from": self.y_manual_from,
                "manual_to": self.y_manual_to,
                "scale": self.y_scale,
                "offset": self.y_offset,
            },
        }

    def deserialise(self, layout):
        logger.info("Deserialising PlotViewBox %s (%s, %s)", self.pw.name,
                    layout['x_axis']['units'], layout['y_axis']['units'])

        # Set x-axis options
        if not layout['twinx']:
            self.set_x_units(layout['x_axis']['units'])
            self.set_x_mode(layout['x_axis']['mode'])
            self.set_x_link_idx(layout['x_axis']['link_idx'])
            self.set_x_mouse(layout['x_axis']['mouse'])
            self.set_x_grid(layout['x_axis']['grid'])
            self.set_x_last_n_secs(layout['x_axis']['last_n_secs'])
            self.set_manual_x_range(layout['x_axis']['manual_from'],
                                    layout['x_axis']['manual_to'])

        # Set y-axis options
        if not layout['twiny']:
            self.set_y_units(layout['y_axis']['units'])
            self.set_y_mode(layout['y_axis']['mode'])
            self.set_y_mouse(layout['y_axis']['mouse'])
            self.set_y_grid(layout['y_axis']['grid'])
            self.set_manual_y_range(layout['y_axis']['manual_from'],
                                    layout['y_axis']['manual_to'])
            self.set_y_scale(layout['y_axis'].get('scale', 1.0))
            self.set_y_offset(layout['y_axis'].get('offset', 0.0))
            self.set_y_autosi(layout['y_axis'].get('autosi', True))
