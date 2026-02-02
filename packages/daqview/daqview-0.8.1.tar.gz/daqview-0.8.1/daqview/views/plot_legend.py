import logging
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from .plot_hover_box import PlotHoverBox

logger = logging.getLogger(__name__)


class LegendItem(pg.LabelItem):
    """
    Custom LabelItem with hover events.
    """
    def __init__(self, *args, channel=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel

    def hoverEvent(self, ev):
        if not ev.exit:
            self.channel.set_temporary_highlight(True)
        else:
            self.channel.set_temporary_highlight(False)


class PlotLegend(PlotHoverBox):
    """
    Custom LegendItem.
    """
    def __init__(self, parent, offset, show_numeric):
        super().__init__(size=None, offset=offset)
        self.pw = parent
        self.pw.channels_changed.connect(self._channels_changed)
        self.setParentItem(self.pw.pi.vb)
        self.layout.setHorizontalSpacing(20)
        self.current_val_lbls = []
        self.show_numeric = show_numeric
        self.add_all()

    def _channels_changed(self):
        self.remove_all()
        self.add_all()

    def add_all(self):
        for idx, channel in enumerate(self.pw.channels):
            self.addItem(channel)
            if self.show_numeric:
                current_val = pg.LabelItem("")
                self.layout.addItem(current_val, idx, 2)
                self.current_val_lbls.append(current_val)

    def remove_all(self):
        for sample, label in self.items:
            sample.close()
            label.close()
            self.layout.removeItem(sample)
            self.layout.removeItem(label)
        for current_val in self.current_val_lbls:
            current_val.close()
            self.layout.removeItem(current_val)
        self.items = []
        self.current_val_lbls = []
        self.updateSize()

    def update_current_values(self):
        if not self.show_numeric:
            return
        for cv, ch in zip(self.current_val_lbls, self.pw.channels):
            cv.setText(ch.formatted_value_with_units())

    def addItem(self, channel):
        """Overridden addItem to use LegendItem instead of pg.LabelItem."""
        label = LegendItem(channel.get_name(), channel=channel)
        sample = ItemSample(channel.pdi)
        row = self.layout.rowCount()
        self.items.append((sample, label))
        self.layout.addItem(sample, row, 0)
        self.layout.addItem(label, row, 1)
        self.updateSize()

    def mouseDragEvent(self, ev):
        """Save our position after being dragged."""
        super().mouseDragEvent(ev)
        self.pw.legend_offset = self.pos()
