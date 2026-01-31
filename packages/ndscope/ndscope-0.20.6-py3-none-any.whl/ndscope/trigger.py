from typing import Optional
import numpy as np

from qtpy import QtCore
from qtpy.QtCore import Signal
import pyqtgraph as pg
from dttlib import PipInstant, TrendStat, TrendType

from ndscope.data import DataBuffer, DataBufferDict
from ndscope.dtt.channel_trend_id import ChannelTrendId
from ndscope.plot import NDScopePlot

from .const import COLOR_MODE, LABEL_ALPHA


class Trigger(QtCore.QObject):
    __slots__ = [
        "channel",
        "line",
        "invert",
        "single",
        "single_t0",
    ]

    level_changed_signal = Signal("PyQt_PyObject")

    def __init__(self):
        super().__init__()
        self.channel_name: Optional[str] = None
        self.channel: Optional[ChannelTrendId] = None
        self.plot = None
        self.line = pg.InfiniteLine(
            angle=0,
            movable=True,
            pen={
                "style": QtCore.Qt.DotLine,
                "width": 3,
            },
            label="trigger level",
            labelOpts={
                "position": 0,
                "anchors": [(0, 0.5), (0, 0.5)],
                "fill": (0, 0, 0, LABEL_ALPHA),
            },
        )
        self.line.sigPositionChanged.connect(self._update_level_from_line)
        self.invert = False
        self.single = False
        self._level = self.line.value()
        self.latest_time_checked = PipInstant.gpst_epoch()
        self.is_trend = False
        self.single_t0: Optional[PipInstant] = None

    def set_font(self, font):
        """set text label font label"""
        self.line.label.textItem.setFont(font)

    def set_color_mode(self, mode):
        """set color mode"""
        fg = COLOR_MODE[mode]["fg"]
        bg = COLOR_MODE[mode]["bg"]
        fill_color = bg.color()
        fill_color.setAlpha(LABEL_ALPHA)
        self.line.label.fill.setColor(fill_color)
        self.line.label.setColor(fg)
        self.line.pen.setColor(fg)

    def set_color(self, color):
        """set the trigger line pen color"""
        self.line.pen.setColor(color)

    def _update_channel(self):
        if self.channel_name is not None:
            if self.is_trend:
                if self.invert:
                    trend_stat = TrendStat.Max
                else:
                    trend_stat = TrendStat.Min
            else:
                trend_stat = TrendStat.Raw
            self.channel = ChannelTrendId(name=self.channel_name, trend_stat=trend_stat)
        else:
            self.channel = None

    def set_channel(self, channel_name: Optional[str]):
        self.channel_name = channel_name
        self._update_channel()

    def set_invert(self, invert: bool):
        self.invert = invert
        self._update_channel()

    def set_is_trend(self, is_trend: bool):
        self.is_trend = is_trend
        self._update_channel()

    @property
    def active(self):
        """True if trigger is active"""
        return self.channel is not None

    def _set_level(self, level):
        self._level = level
        self.line.label.setText(f"trigger level\n{level:g}")

    def _update_level_from_line(self, line):
        pos = line.value()
        level = self.plot.y_pos_to_val(pos)
        self._set_level(level)
        self.level_changed_signal.emit(level)

    def set_level(self, value):
        """set the trigger level"""
        if not self.plot:
            return
        self._set_level(value)
        # update the line
        pos = self.plot.y_val_to_pos(value)
        if pos is None:
            self.line.setVisible(False)
        else:
            self.line.setValue(pos)
            self.line.setVisible(True)

    def _transform(
        self, plot: Optional[NDScopePlot], data: Optional[DataBufferDict]
    ) -> Optional[DataBuffer]:
        """transform trigger data according to the channel's transform for the given plot"""
        if data is not None and self.channel is not None:
            try:
                y = data[self.channel]
                if plot is not None:
                    chan = plot.get_channel(self.channel)
                    if chan is not None:
                        trans_data = chan.transform(y.data)
                        trans_buffer = DataBuffer(buf=None, clone_from=y)
                        trans_buffer.gps_start = y.gps_start
                        trans_buffer.data = trans_data
                        return trans_buffer
                    else:
                        return y
                else:
                    return y
            except KeyError:
                return None
        else:
            return None

    def guess_trigger_level(
        self, plot: Optional[NDScopePlot], data: Optional[DataBufferDict]
    ) -> float:
        """Pick a good initial value for the trigger

        This returns the guess but doesn't set it.  The caller is responsible for setting the value.
        """
        ybuf = self._transform(plot, data)
        if ybuf is not None:
            y = ybuf.data
            yn = y[np.where(np.invert(np.isnan(y)))[0]]
            mean = np.mean(yn)
            if mean > 0:
                guess = max(np.mean(yn), 0.1 * np.max(yn))
            else:
                guess = min(np.mean(yn), 0.1 * np.min(yn))
        else:
            guess = 0
        return guess

    @property
    def level(self):
        """trigger level"""
        return self._level

    def redraw(self):
        """redraw the trigger level line

        Use when plot Y axis scale changes.

        """
        self.set_level(self.level)

    def set_single(self, value):
        """set single shot mode"""
        self.single_t0 = None
        self.single = value

    def on_trend_change(self, trend: TrendType):
        self.set_is_trend(trend != TrendType.Raw)

    def check(
        self, plot: Optional[NDScopePlot], data: DataBufferDict
    ) -> Optional[PipInstant]:
        """Check for trigger in last_append of DataBufferDict

        Returns trigger time or None

        """
        if self.channel is None:
            return

        if self.single and self.single_t0 is not None:
            return self.single_t0

        # get transform, if any

        last_untrimmed = self._transform(plot, data)
        if last_untrimmed == None:
            return None
        last = last_untrimmed.trim_before(self.latest_time_checked)
        t = last.tarray_pip()
        y = last.data

        if len(t) == 0:
            range = data[self.channel].range
            return None

        # last point wasn't checked
        self.latest_time_checked = last.gps_end - 2 * last.period_pip

        level = self.level
        yp = np.roll(y, 1)
        yp[0] = y[0]
        if self.invert:
            tind = np.where((yp >= level) & (y < level))[0]
        else:
            tind = np.where((yp <= level) & (y > level))[0]

        if not np.any(tind):
            return None

        tti = tind.min()
        ttime = t[tti]
        if self.single:
            self.single_t0 = ttime

        return ttime
