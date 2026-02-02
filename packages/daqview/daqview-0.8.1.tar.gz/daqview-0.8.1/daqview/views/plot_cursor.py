import logging
import pyqtgraph as pg

logger = logging.getLogger(__name__)


class PlotCursor(pg.InfiniteLine):
    """
    Cursor class controlling an InfiniteLine which can be repositioned and
    provides a readout of the current time value and corresponding data values.
    Maintains on-screen position if the plot's x range changes.
    """
    def __init__(self, pos, label_pos, pw):
        super().__init__(pos, movable=True)
        logger.info("Creating PlotCursor at x=%s", pos)
        self.pw = pw
        self.label = PlotCursorLabel(self, movable=True)
        if label_pos is not None:
            self.label.setPosition(label_pos)
        self.pw.channels_changed.connect(self._channels_changed)
        self.sigPositionChanged.connect(self._position_changed)

    def _channels_changed(self):
        self.label.setParentItem(None)
        self.label = PlotCursorLabel(self, movable=True)

    def _position_changed(self):
        self.pw.cursor_pos = self.getXPos()


class PlotCursorLabel(pg.InfLineLabel):
    """
    Label for PlotCursor which can display the value of each channel as well
    as the current cursor position.
    """
    def __init__(self, line, *args, **kwargs):
        self.pc = line
        text = ["Time: {time:.02f}s"]
        for channel in self.pc.pw.channels:
            text.append(channel.get_name() + ": {" + channel.channel_id + "}")
        text = "\n".join(text)
        super().__init__(line, text, *args, **kwargs)

    def valueChanged(self):
        """
        Overridden valueChanged finds values for all displayed channels as
        well.
        """
        if not self.isVisible():
            return
        t = self.line.value()
        variables = {"time": t}
        for channel in self.pc.pw.channels:
            channel_id = channel.channel_id
            variables[channel_id] = channel.formatted_value_with_units(t)
        try:
            self.setText(self.format.format(**variables))
        except KeyError:
            # If some channels are deleted and valueChanged triggers before
            # the PlotCursor._channels_changed is called, we might try and
            # format with no-longer-extant channels.
            self.setText("")
        self.updatePosition()

    def updatePosition(self):
        """
        Overridden updatePosition saves the position to the parent pw.
        """
        super().updatePosition()
        self.pc.pw.cursor_label_pos = float(self.orthoPos)
