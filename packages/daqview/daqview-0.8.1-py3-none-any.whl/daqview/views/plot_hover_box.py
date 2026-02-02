import pyqtgraph as pg


class PlotHoverBox(pg.LegendItem):
    """
    Custom LegendItem which becomes more opaque when the mouse hovers over it.

    Inherited from by PlotLegend and PlotRegionLabel.
    """
    PEN_IDLE = (255, 255, 255, 100)
    BRUSH_IDLE = (100, 100, 100, 50)
    PEN_HOVER = (255, 255, 255, 200)
    BRUSH_HOVER = (50, 50, 50, 200)

    def __init__(self, **kwargs):
        kwargs['pen'] = self.PEN_IDLE
        kwargs['brush'] = self.BRUSH_IDLE
        super().__init__(**kwargs)

    def hoverEvent(self, ev):
        """Go more opaque when hovered."""
        super().hoverEvent(ev)
        if not ev.exit:
            self.setPen(self.PEN_HOVER)
            self.setBrush(self.BRUSH_HOVER)
        else:
            self.setPen(self.PEN_IDLE)
            self.setBrush(self.BRUSH_IDLE)
