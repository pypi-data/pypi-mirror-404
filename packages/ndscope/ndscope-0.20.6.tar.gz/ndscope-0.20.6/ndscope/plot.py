import copy
from enum import Enum
import logging
import collections

import numpy as np
from qtpy import QtCore
from qtpy.QtGui import QPen, QFontMetrics
from qtpy.QtCore import Signal  # type: ignore
from qtpy.QtWidgets import QApplication
import pyqtgraph as pg
from dataclasses import dataclass

from gpstime import gpstime
from dttlib import TrendType, ChannelType, TrendStat, PipInstant, PipDuration, Unit

from ndscope.exceptions import UnknownChannelError

from . import util
from . import const
from .cache import DataCache
from .data import DataBufferDict, DataBuffer
from .plotMenu import NDScopePlotMenu
from . import template
from . import legend
from . import cursors
from .dtt.channel_trend_id import ChannelTrendId
from typing import List, Tuple, Dict, TYPE_CHECKING, Optional
from weakref import WeakSet

if TYPE_CHECKING:
    from .result import Result

logger = logging.getLogger("PLOT")

pg.setConfigOptions()

##################################################


# monkey patch to add a set_color_mode method to the AxisItem class


# Copied from pyqtgraph source version 0.12.3.
def _updateLabel(self):
    """Internal method to update the label according to the text"""
    self.label.setHtml(self.labelString())
    self._adjustSize()
    self.picture = None
    self.update()


pg.AxisItem._updateLabel = _updateLabel


def _set_color_mode(self, mode):
    # Modified from pyqtgraph source version 0.12.3 for AxisItem.setTextPen.
    # https://pyqtgraph.readthedocs.io/en/pyqtgraph-0.12.3/_modules/pyqtgraph/graphicsItems/AxisItem.html#AxisItem.setTextPen
    fg = const.COLOR_MODE[mode]["fg"]
    pen = QPen(fg)
    self.picture = None
    self._textPen = pen
    self.labelStyle["color"] = self._textPen.color().name()
    self._updateLabel()


pg.AxisItem.set_color_mode = _set_color_mode  # type: ignore


##################################################


class TimeStringAxis(pg.AxisItem):
    def __init__(self, orientation="bottom", **kwargs):
        super().__init__(orientation, **kwargs)
        self.t0 = PipInstant.gpst_epoch()
        self.tick_font = self.font()
        self.setTickStringsMode("relative")

    def t_to_relative(self, t: PipDuration) -> str:
        return str(util.TDStr(t.to_seconds()))

    def t_to_gps(self, t: PipDuration) -> str:
        return str((t + self.t0).to_gpst_seconds())

    def t_to_utc(self, t: PipDuration) -> str:
        gps = gpstime.fromgps((t + self.t0).to_gpst_seconds())
        return gps.strftime(const.TICK_DATE_FMT)

    def t_to_local(self, t: PipDuration):
        gps = gpstime.fromgps((t + self.t0).to_gpst_seconds())
        local = gps.astimezone()
        return local.strftime(const.TICK_DATE_FMT)

    def setTickStringsMode(self, mode):
        self.mode = mode
        self.update_tick_mode()

    def setTickFont(self, font):
        self.tick_font = font
        self.update_tick_mode()
        return super().setTickFont(font)

    def update_tick_mode(self):
        func_map = {
            "relative": self.t_to_relative,
            "absolute GPS": self.t_to_gps,
            "absolute UTC": self.t_to_utc,
            "absolute local": self.t_to_local,
        }

        metrics = QFontMetrics(self.tick_font)
        one_line = metrics.boundingRect("Tag").height()
        height_map = {
            "relative": one_line,
            "absolute GPS": one_line,
            "absolute UTC": one_line * 2,
            "absolute local": one_line * 2,
        }
        self.setStyle(autoExpandTextSpace=True)
        self.tick_func = func_map[self.mode]
        # this is needed to clear/update the ticks on change:
        # fudge factor of 8% because the calculation isn't quite enough for
        # some fonts and font sizes
        self.setHeight(height_map[self.mode] * 1.08)
        self._redraw_ticks()

    ######

    def tickSpacing(self, minVal, maxVal, size) -> list[tuple[float, float]]:
        span = PipDuration.from_seconds(abs(maxVal - minVal))
        major = PipDuration.from_sec(1)
        minordiv = 0.5
        for major, minordiv in const.TICK_SPACINGS:
            if span >= 3 * major:
                break
        return [
            (major.to_seconds(), 0),
            ((major / minordiv).to_seconds(), 0),
        ]

    def tickStrings(self, values: list[float], scale, spacing):
        return [self.tick_func(PipDuration.from_seconds(t)) for t in values]

    def set_t0(self, t0: PipInstant):
        self.t0 = t0
        self._redraw_ticks()

    def _redraw_ticks(self):
        """Call to update the appearance of tick marks"""
        self.picture = None
        self.update()


##################################################


class LogLabelLevel(Enum):
    ALL = 1
    """show all sub-decade lines"""

    TWOS_AND_FIVES = 2
    """reduce sub-decade lines to only twos and fives"""

    NONE = 3
    """don't show any sub-decade lines"""


class YAxis(pg.AxisItem):
    max_global_width = 0.0

    update_width_signal = Signal()

    axes: WeakSet["YAxis"] = WeakSet()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tick_font = self.font()
        self.log_label_level = LogLabelLevel.ALL
        # for axis in YAxis.axes:
        #     self.update_width_signal.connect(axis.update_width)
        YAxis.axes.add(self)
        # for axis in YAxis.axes:
        #     axis.update_width_signal.connect(self.update_width)

    def logTickValues(self, minVal, maxVal, size, stdTicks):
        """Help self.logTickStrings by determining the proper reduction mode for tick strings"""
        ticks = super().logTickValues(minVal, maxVal, size, stdTicks)

        metrics = QFontMetrics(self.tick_font)
        line_height = metrics.boundingRect("123456789E000+1").height()

        pix_per_decade = size / (maxVal - minVal)

        # number of pixels from 9EX to 1E(X+1)
        pix_after_nine = (1 - np.log10(9.0)) * pix_per_decade
        if pix_after_nine < line_height + 2:
            pix_after_five = np.log10(2.0) * pix_per_decade  # log10(2) + log10(5) = 1
            if pix_after_five < line_height + 2:
                self.log_label_level = LogLabelLevel.NONE
            else:
                self.log_label_level = LogLabelLevel.TWOS_AND_FIVES
        else:
            self.log_label_level = LogLabelLevel.ALL
        return ticks

    def logTickStrings(self, values, scale, spacing) -> List[str]:
        """Override pyqtgraph function to more aggressively
        cull overalapping tick labels"""
        orig_strings = super().logTickStrings(values, scale, spacing)

        if self.log_label_level == LogLabelLevel.ALL:
            strings = orig_strings
        elif self.log_label_level == LogLabelLevel.NONE:
            strings = []
            mods = np.divmod(values, 1.0)[1]
            for i, mod in enumerate(mods):
                if np.isclose(mod, 0):
                    strings.append(orig_strings[i])
                else:
                    strings.append("")
        elif self.log_label_level == LogLabelLevel.TWOS_AND_FIVES:
            strings = []
            mods = np.divmod(values, 1.0)[1]
            log5 = np.log10(5)
            log2 = np.log10(2)
            for i, mod in enumerate(mods):
                if np.isclose(mod, 0) or np.isclose(mod, log5) or np.isclose(mod, log2):
                    strings.append(orig_strings[i])
                else:
                    strings.append("")
        else:
            raise ValueError(f"Unhandled LogLabelLevel {self.log_label_level}")

        return strings

    # this is needed for some versions of pyqtgraph that set the auto-scaling too high.
    def getSIPrefixEnableRanges(self):
        return ((0.0, 1e-6), (1e6, np.inf))

    def setTickFont(self, font):
        logger.debug("Changing y axis tick font")
        self.tick_font = font
        super().setTickFont(font)

    def _estimate_width(self):
        """Taken from AxisItem._updateWidth() in pyqtgraph version 0.15"""
        if not self.isVisible():
            w = 0
        else:
            # if not self.style['showValues']:
            #    w = 0
            # elif self.style['autoExpandTextSpace']:
            w = self.textWidth
            # else:
            #    w = self.style['tickTextWidth']
            w += self.style["tickTextOffset"][0] if self.style["showValues"] else 0
            w += max(0, self.style["tickLength"])
            if self.label.isVisible():
                w += (
                    self.label.boundingRect().height() * 0.8
                )  ## bounding rect is usually an overestimate
        return w

    @classmethod
    def update_all_widths(cls):
        for axis in cls.axes:
            axis.setWidth(cls.max_global_width)

    def update_width(self):
        w = self._estimate_width()
        if w > YAxis.max_global_width:
            YAxis.max_global_width = w
            self.update_all_widths()
        else:
            self.setWidth(YAxis.max_global_width)

    @classmethod
    def clear_and_update_width(cls):
        max_w = 0
        for axis in cls.axes:
            w = axis._estimate_width()
            if max_w < w:
                max_w = w
        YAxis.max_global_width = max_w
        cls.update_all_widths()


print_targ = None


##################################################


class NDScopeViewBox(pg.ViewBox):
    def __init__(self, data_store: DataCache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_cache = data_store

    # HACK: we overload this function to pass the mouse event to the
    # context menu popup, instead of the global point position, so
    # that the menu can extract the local scene point.  See
    # NDScopePlotMenu.popup
    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        if menu is not None:
            self.scene().addParentContextMenus(self, menu, ev)  # type: ignore
            menu.popup(ev)

    def translateBy(self, t=None, x=None, y=None):
        if self.data_cache.online:
            x = None
        super().translateBy(t=t, x=x, y=y)

    def scaleBy(self, s=None, center=None, x=None, y=None):
        if self.data_cache.online:
            if center:
                center = pg.Point(0, center.y())
        super().scaleBy(s=s, center=center, x=x, y=y)


##################################################


@dataclass
class CurveView:
    """
    Enough info for a single curve to plot it from scope data
    """

    curve: pg.PlotDataItem
    chan: "NDScopePlotChannel"
    highlight_gaps: bool
    x: np.ndarray
    y: np.ndarray

    def setData(self, x: np.ndarray, y: np.ndarray, *args, **kwargs):
        if len(self.x) == len(x):
            self.x[:] = x
        else:
            self.x = x
        if len(self.y) == len(y):
            self.y[:] = y
        else:
            self.y = y
        self.curve.setData(x=x, y=y, *args, **kwargs)


##################################################


class NDScopePlot(pg.PlotItem):
    channel_config_request = Signal("PyQt_PyObject")
    new_plot_request = Signal("PyQt_PyObject")
    remove_plot_request = Signal("PyQt_PyObject")
    t0_reset = Signal(float)
    t_cursors_enable = Signal(bool)
    t_cursor_moved = Signal("PyQt_PyObject")
    log_mode_toggled = Signal("PyQt_PyObject")
    channels_updated = Signal()

    def __init__(self, data_store: DataCache, *args, title=None, loc=None):
        """Initialize NDSCope Plot object"""
        super().__init__(
            *args,
            viewBox=NDScopeViewBox(data_store),
            axisItems={"bottom": TimeStringAxis(), "left": YAxis(orientation="left")},
        )

        self.data_cache: DataCache = data_store
        self.t_cursor_moved.connect(self.data_cache.handle_cursor_moved)  # type: ignore

        self.title = title
        self.loc = loc

        self.channels: Dict[str, "NDScopePlotChannel"] = collections.OrderedDict()
        self.curve_view: Dict[ChannelTrendId, CurveView] = collections.OrderedDict()
        self.bad_curve_view: Dict[str, CurveView] = collections.OrderedDict()

        self.t_cursors = cursors.TCursors(self)
        self.t_cursors.cursor_moved.connect(self._update_t_cursor)
        self.y_cursors = cursors.YCursors(self)

        self.sigYRangeChanged.connect(self.axes["left"]["item"].update_width)

        self.addItem(self.t_cursors.C1, ignoreBounds=True)
        self.addItem(self.t_cursors.C2, ignoreBounds=True)
        self.addItem(self.t_cursors.diff, ignoreBounds=True)

        self.addItem(self.y_cursors.C1, ignoreBounds=True)
        self.addItem(self.y_cursors.C2, ignoreBounds=True)
        self.addItem(self.y_cursors.diff, ignoreBounds=True)

        # setup the custom context menu.  should be setup after
        # cursors are created above.  unclear why it needs to be
        # implemented as a ViewBox menu instead of as the "ctrlMenu"
        # for the plot.
        self.ctrlMenu = None
        self.getViewBox().menu = NDScopePlotMenu(self)  # type: ignore

        # plot options
        # use automatic downsampling and clipping to reduce the
        # drawing load
        self.setDownsampling(mode="peak")
        # clip data to only what's visible
        # FIXME: is this what we want?
        self.setClipToView(True)
        # don't auto-range x axis, since we have special handling
        self.disableAutoRange(axis="x")  # type: ignore
        # hide auto-scale buttons
        self.hideButtons()
        # add legend
        self.legend = legend.Legend()
        self.legend.setParentItem(self.getViewBox())
        self.legend.setVisible(False)
        # show grid lines
        self.showGrid(x=True, y=True, alpha=0.2)
        left_axis = self.getAxis("left")
        # left_axis.setWidth(50)
        # limit the zooming range
        self.setLimits(  # type: ignore
            minXRange=0.0001,
        )
        # accept drops
        self.setAcceptDrops(True)

        # If this option is not removed then a default font size will
        # be set in the generated html that will not overridable by
        # setting the font.
        self.titleLabel.opts.pop("size")

    def __del__(self):
        logger.info("deleting plot %s", str(self))

    def update_axis_width(self):
        """Set axis width to the global minimum needed to show all axis labels on all plots

        don't shrink the width but only grow
        """
        self.axes["left"]["item"].clear_and_update_width()

    def dropEvent(self, event):
        data = event.mimeData()  # type: ignore
        if data.hasFormat("text/plain"):  # type: ignore
            text_list = data.text().splitlines()  # type: ignore
            for text in text_list:
                self.add_channels({text: {}})

    def open_channel_config_dialog(self):
        self.channel_config_request.emit(self)

    def _add_channel_obj(self, cc: "NDScopePlotChannel"):
        channel = cc.channel
        self.channels[channel] = cc

        self.curve_view[ChannelTrendId(name=channel, trend_stat=TrendStat.Raw)] = (
            CurveView(cc.curves["y"], cc, True, np.array([]), np.array([]))
        )
        self.curve_view[ChannelTrendId(name=channel, trend_stat=TrendStat.Mean)] = (
            CurveView(cc.curves["y"], cc, True, np.array([]), np.array([]))
        )
        self.curve_view[ChannelTrendId(name=channel, trend_stat=TrendStat.Min)] = (
            CurveView(cc.curves["min"], cc, False, np.array([]), np.array([]))
        )
        self.curve_view[ChannelTrendId(name=channel, trend_stat=TrendStat.Max)] = (
            CurveView(cc.curves["max"], cc, False, np.array([]), np.array([]))
        )
        self.curve_view[ChannelTrendId(name=channel, trend_stat=TrendStat.Rms)] = (
            CurveView(cc.curves["rms"], cc, False, np.array([]), np.array([]))
        )

        self.bad_curve_view[channel] = CurveView(
            cc.curves["bad"], cc, True, np.array([]), np.array([])
        )

        self.addItem(cc.curves["y"])
        self.addItem(cc.curves["min"])
        self.addItem(cc.curves["max"])
        self.addItem(cc.curves["rms"])
        self.addItem(cc.curves["bad"])
        self.enableAutoRange(axis="y")  # type: ignore
        self._update_title_legend()
        cc.label_changed.connect(self._update_legend_item)
        cc.label_changed.connect(self._update_title_legend)
        cc.unit_changed.connect(self._update_units)
        self._update_legend_item(channel)

    def _remove_channel_obj(self, cc):
        channel = cc.channel

        curves_to_remove = [c for c in self.curve_view.keys() if c.name == channel]
        for curve in curves_to_remove:
            del self.curve_view[curve]

        self.legend.removeItem(cc.get_label())
        for curve in cc.curves.values():
            self.removeItem(curve)
        del self.channels[channel]
        self._update_title_legend()

    def set_channel_objs(self, chan_obj_list: List["NDScopePlotChannel"]):
        """set plot channels from list NDScopePlotChannel objects

        Any channels currently being plotted that are not in list will
        be removed.

        """
        channel_dict = {cc.channel: cc for cc in chan_obj_list}
        set_chans = set(channel_dict.keys())
        cur_chans = set(self.channels.keys())
        with self.data_cache.update_context(force=True) as ds:
            for chan in cur_chans - set_chans:
                cc = self.channels[chan]
                self._remove_channel_obj(cc)
            for chan in set_chans - cur_chans:
                self._add_channel_obj(channel_dict[chan])
            for chan in set_chans & cur_chans:
                self.channels[chan].set_params(**channel_dict[chan].params)
            self.data_cache.get_channels()
        self.set_y_range("auto")

    def add_channels(self, channel_dict: Dict[str, Dict]):
        """Add channels to plot

        Takes a dictionary where the keys are channel names and the
        values are channel curve keyword argument dictionaries.  The
        keyword arguments are passed directly to NDScopePlotChannel.

        """
        with self.data_cache.update_context(force=True) as ds:
            for channel, kwargs in channel_dict.items():
                if channel in self.channels:
                    continue
                kwargs = kwargs or {}
                cc = NDScopePlotChannel(channel, **kwargs)
                self._add_channel_obj(cc)
            self.data_cache.get_channels()
        self.set_y_range("auto")
        self.channels_updated.emit()

    def remove_channels(self, channel_list=None):
        """remove channels from plot

        Takes a list of channel names to remove.  If the
        `channel_list` argument is missing all channels will be
        removed.

        """
        if channel_list is None:
            channel_list = list(self.channels.keys())
        try:
            with self.data_cache.update_context() as ds:
                for channel in channel_list:
                    if channel not in self.channels:
                        continue
                    cc = self.channels[channel]
                    self._remove_channel_obj(cc)
            self.data_cache.get_channels()
        except UnknownChannelError:
            pass
        self.set_y_range("auto")
        self.channels_updated.emit()

    def get_channels(self):
        """get a channel:params dict for all channels in plot"""
        return {chan: cc.params for chan, cc in self.channels.items()}

    def set_font(self, font):
        """Set label and axis font"""
        self.titleLabel.item.setFont(font)
        self.legend.setFont(font)
        self.axes["left"]["item"].label.setFont(font)  # type: ignore
        self.axes["bottom"]["item"].setTickFont(font)  # type: ignore
        self.axes["left"]["item"].setTickFont(font)  # type: ignore
        self.t_cursors.set_font(font)
        self.y_cursors.set_font(font)

    def set_color_mode(self, mode):
        fg = const.COLOR_MODE[mode]["fg"]
        _bg = const.COLOR_MODE[mode]["bg"]
        self.titleLabel.setAttr("color", fg)
        self.titleLabel.setText(self.titleLabel.text)
        self.legend.setTextColor(fg)
        self.axes["left"]["item"].set_color_mode(mode)  # type: ignore
        self.axes["bottom"]["item"].set_color_mode(mode)  # type: ignore
        self.t_cursors.set_color_mode(mode)
        self.y_cursors.set_color_mode(mode)

    def get_channel(self, channel: ChannelTrendId) -> Optional["NDScopePlotChannel"]:
        try:
            curve_view = self.curve_view[channel]
        except KeyError:
            return None
        return curve_view.chan

    ##### y axis

    @property
    def log_mode(self):
        """current log mode state"""
        return self.getAxis("left").logMode

    def y_pos_to_val(self, y):
        """get the y coordinate position for a given value

        Takes into account logarithmic axis scaling.

        """
        if self.log_mode:
            try:
                y = 10**y
            except OverflowError:
                y = 0
        return y

    def y_val_to_pos(self, y):
        """get the y value for a given coordinate position

        Takes into account logarithmic axis scaling.  If the value
        doesn't correspond to any position on the axis, None will be
        returned.

        """
        if self.log_mode:
            if y > 0:
                # HACK: we convert to normal float because pyyaml
                # can't handle numpy objects
                return float(np.log10(y))
            else:
                return None
        else:
            return y

    def set_y_range(self, y_range):
        """set the Y axis range

        If None or "auto" then auto range will be enabled, otherwise
        range should be tuple.

        """
        logger.debug(f"plot {self.loc} Y range: {y_range}")
        if y_range in [None, "auto"]:
            self.enableAutoRange(axis="y")  # type: ignore
        else:
            self.disableAutoRange(axis="y")  # type: ignore
            y_range = tuple(map(self.y_val_to_pos, y_range))
            self.getViewBox().setYRange(*y_range, padding=0.0)  # type: ignore

    def set_log_mode(self, log=True):
        """set the Y scale to be log
        curve_view
                True turns on log mode, False turns it off.

        """
        assert isinstance(log, bool)
        # FIXME HACK: This is a hack around
        # https://github.com/pyqtgraph/pyqtgraph/issues/2307 Since we
        # can not stop it from autoscaling the range at least once
        # when we switch on log mode, we keep track of the axis state
        # and set it back after the change.
        vb: pg.ViewBox = self.getViewBox()  # type: ignore
        x_range, y_range = vb.viewRange()
        self.setLogMode(y=log)
        vb.disableAutoRange(vb.XAxis)
        vb.setXRange(min=x_range[0], max=x_range[1], padding=0.0)
        self.y_cursors.redraw()
        self.log_mode_toggled.emit(self)

    ##########

    def _reset_t0(self, val: float):
        self.t0_reset.emit(val)

    ##### cursors

    def enable_t_cursors(self):
        """enable T cursors and return cursor object"""
        self.t_cursors.reset_if_invisible_everywhere()
        return self.t_cursors

    def _update_t_cursor(self, indval):
        self.t_cursor_moved.emit(indval)

    def enable_y_cursors(self):
        """enable Y cursors and return cursor object"""
        # if self.y_cursors.C1 not in self.getViewBox().allChildren():  # type: ignore
        # self.addItem(self.y_cursors.C1, ignoreBounds=True)
        # self.addItem(self.y_cursors.C2, ignoreBounds=True)
        # self.addItem(self.y_cursors.diff, ignoreBounds=True)
        # self.y_cursors.reset()
        # logger.debug(f"plot {self.loc} Y cursor enabled")
        self.y_cursors.reset_if_invisible()
        return self.y_cursors

    ##########

    # SLOT
    def _update_legend_item(self, channel):
        cc = self.channels[channel]
        self.legend.removeItem(cc.curves["y"])
        self.legend.addItem(cc.curves["y"], cc.get_label())

    def _update_title_legend(self):
        """update plot title and legend"""
        if self.title:
            self.legend.setVisible(True)
            self.setTitle(self.title)
        elif len(self.channels) < 1:
            self.legend.setVisible(False)
            self.setTitle(None)
        elif len(self.channels) == 1:
            self.legend.setVisible(False)
            self.setTitle(list(self.channels.values())[0].get_label())
        else:
            self.legend.setVisible(True)
            self.setTitle(None)

    def _update_units(self):
        units = set([cc.get_unit() for cc in self.channels.values()])
        self.setLabel("left", "/".join(list(units)))

    def clear_data(self):
        """clear data for all channels"""
        for curve in self.channels.values():
            curve.clear_data()

    def _set_t_limits(self, t0):
        """Set the t axis limits for a given t0"""
        self.setLimits(
            xMin=const.GPS_MIN - t0,
            # xMax=gpsnow()-t0+1,
        )

    def set_all_mean_curves_visibility(self, visible: bool):
        for cc in self.channels.values():
            cc.set_mean_curve_visibility(visible)

    def set_all_min_curves_visibility(self, visible: bool):
        for cc in self.channels.values():
            cc.set_min_curve_visibility(visible)

    def set_all_max_curves_visibility(self, visible: bool):
        for cc in self.channels.values():
            cc.set_max_curve_visibility(visible)

    def set_all_rms_curves_visibility(self, visible: bool):
        for cc in self.channels.values():
            cc.set_rms_curve_visibility(visible)

    def update(self, data: DataBufferDict, t0: PipInstant):
        """update all channels

        `data` should be a DataBufferDict object, and `t0` is the GPS
        time for t=0.

        """
        if self.axes is not None:
            self.axes["bottom"]["item"].set_t0(t0)
            self._set_t_limits(t0.to_gpst_seconds())

            for chan_id, curve_view in self.curve_view.items():
                if chan_id not in data:
                    continue

                cd = data[chan_id]

                # if cd.is_trend:
                #     curve_view.chan.set_max_curve_visibility(True)
                #     curve_view.chan.set_min_curve_visibility(True)
                # else:
                #     curve_view.chan.set_max_curve_visibility(False)
                #     curve_view.chan.set_min_curve_visibility(False)

                t = cd.tarray_sec(t0)
                y = cd.data
                # FIXME: HACK: replace all +-infs with nans.  the infs
                # were causing the following exception in PlotCurveItem
                # when it tried to find the min/max of the array:
                # ValueError: zero-size array to reduction operation minimum which has no identity
                # using nan is not great, since that's also an indicator
                # of a gap, but not sure what else to use.
                try:
                    np.place(y, np.isinf(y), np.nan)
                except ValueError:
                    # this check throws a value error if y is int.  but in
                    # that case there's nothing we need to convert, so
                    # just pass
                    pass
                curve_view.chan.set_unit(cd.unit)
                y = curve_view.chan.transform(y)
                curve_view.chan.set_ctype(cd.id.first_channel().channel_type)
                curve_view.setData(
                    x=t,
                    y=y,
                    connect="finite",
                    # skipFiniteCheck=True,
                    # autoDownsample=False,
                    # clipToViewx=False,
                )
                if curve_view.highlight_gaps:
                    y = hold_over_nan(y)
                    has_gaps = not np.isnan(y).all()
                    if curve_view.chan.last_gaps == True or has_gaps:
                        if has_gaps:
                            self.bad_curve_view[chan_id.name].setData(
                                x=t,
                                y=y,
                                connect="finite",
                                # skipFiniteCheck=True,
                                # autoDownsample=False,
                                # clipToView=False,
                            )
                        else:
                            self.bad_curve_view[chan_id.name].setData([], [])
                        curve_view.chan.last_gaps = has_gaps
                    else:
                        pass
            QApplication.processEvents()
        else:
            logger.error("Attempted to update plot that has no axes")

    def update_results(self, results: Dict[str, "Result"]):
        for channel, cc in self.channels.items():
            if channel in results:
                result = results[channel]
                cc.set_result(result)


##################################################


class NDScopePlotChannel(QtCore.QObject):
    label_changed = Signal(str)
    unit_changed = Signal(str)

    def __init__(self, channel: str, **kwargs):
        """Initialize channel curve object

        Holds curves for y value, and for trend min/max/fill.

        Keyword arguments are trace style parameters, e.g. `color`,
        `width`, `unit`, `scale` and `offset`.  `color` can be a
        single letter color spec ('b', 'r', etc.), an integer, or an
        [r,g,b] list.  See the following for more info:

          http://www.pyqtgraph.org/documentation/functions.html#pyqtgraph.mkColor

        """
        super().__init__()

        self.channel = channel
        self.params = dict(template.CURVE)
        self.data: Dict[TrendStat, DataBuffer] = {}

        # store whether the last time the curve was drawn it had gaps
        # optmization that speeds up drawing
        # by not updating bad curve when there are no gaps.
        # This is the usual case for live raw data,
        # which in turn is the only case where we
        # care much about drawing optimization.
        self.last_gaps = True

        self.curves: Dict[str, pg.PlotDataItem] = {}
        self.last_ctype: Optional[ChannelType] = None
        self.curves["y"] = pg.PlotDataItem([0, 0], name="")
        self.curves["min"] = pg.PlotDataItem([0, 0], name=None)
        self.curves["max"] = pg.PlotDataItem([0, 0], name=None)
        self.curves["rms"] = pg.PlotDataItem([0, 0], name=None)
        self.curves["bad"] = pg.PlotDataItem([0, 0])

        # give the units reported by the data stream
        self.data_unit: Optional[Unit] = None

        for _n, c in self.curves.items():
            c.setDownsampling(ds=None, auto=False)
            c.setClipToView(state=False)
            connect = ("finite",)
            skipFiniteCheck = (True,)

        self.t0: PipInstant = PipInstant.gpst_epoch()
        # FIXME: fill is expensive, so we disable it until figure it out
        if False:
            self.curves["fill"] = pg.FillBetweenItem(
                self.curves["min"],
                self.curves["max"],
            )
        # else:
        #     self.curves["fill"] = None

        kwargs["color"] = template.get_channel_color(channel, kwargs.get("color"))
        self.set_params(**kwargs)

    def as_tuple(self) -> Tuple[Tuple[str, str], ...]:
        return (("channel", self.channel),) + tuple(sorted(self.params.items()))

    @property
    def is_trend(self):
        return self.last_ctype in [ChannelType.MTrend, ChannelType.STrend]
        if self.data:
            return self.data.is_trend
        return False

    def __repr__(self):
        return "<{} {} {}>".format(
            self.__class__.__name__,
            self.channel,
            self.params,
        )

    # NOTE: we override the hash and eq definitions for these objects
    # so that we can comparchannele them in sets.  hopefully this doesn't
    # cause any other problems
    def __hash__(self):
        return hash(self.as_tuple())

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def _update_transform(self):
        """update the transform function"""
        # if self.params["scale"] != 1 or self.params["offset"] != 0:

        def transform(data):
            return (data + self.params["offset"]) * self.params["scale"]

        # else:

        #    def transform(data):
        #        return data

        self.transform = transform

    def _update_label(self):
        self.label_changed.emit(self.channel)

    def set_unit(self, unit: Unit):
        if self.data_unit is None:
            logger.debug("setting unit = %s", unit)
            self.data_unit = unit
            self._update_unit()

    def _update_unit(self):
        self.unit_changed.emit(self.channel)

    def get_QColor(self):
        """Get channel color as a QColor object"""
        return pg.mkColor(self.params["color"])

    def set_params(self, **params):
        """set parameters for this channel"""
        PARAMS = ["color", "width", "scale", "offset", "unit", "label"]

        for param, value in params.items():
            if param not in PARAMS:
                raise KeyError(f"invalid parameter '{param}', options are: {PARAMS}")
            if param == "color":
                value = pg.mkColor(value).name()
            self.params[param] = value

        color = self.get_QColor()
        pen = pg.mkPen(color, width=self.params["width"])
        mmc = copy.copy(color)
        mmc.setAlpha(const.TREND_MINMAX_ALPHA)
        mmpen = pg.mkPen(mmc, width=self.params["width"], style=QtCore.Qt.DashLine)
        rmspen = pg.mkPen(mmc, width=self.params["width"], style=QtCore.Qt.DashDotLine)
        self.curves["y"].setPen(pen)
        self.curves["rms"].setPen(rmspen)
        self.curves["min"].setPen(mmpen)
        self.curves["max"].setPen(mmpen)
        self.curves["bad"].setPen(
            pg.mkPen("r", width=self.params["width"], style=QtCore.Qt.DotLine)
        )
        # if self.curves["fill"] is not None:
        #     self.curves["fill"].setBrush(mmc)
        # self.curves["y-fill"].setBrush(color)
        self._update_label()
        self._update_unit()
        if not set(["scale", "offset"]).isdisjoint(self.params):
            self._update_transform()
            self._redraw_curves()

    def get_unit(self):
        """return channel unit"""
        unit = self.params.get("unit")
        if not unit:
            if self.data_unit:
                unit = str(self.data_unit) or "counts"
            else:
                unit = "counts"
        return unit

    def get_label(self):
        if self.params.get("label"):
            return self.params["label"]
        offset = self.params["offset"]
        scale = self.params["scale"]
        label = f"{self.channel}"
        if offset != 0:
            if scale != 1:
                label = f"({self.channel} {offset:+g})"
            else:
                label += f" {offset:+g}"
        if scale != 1:
            label += f"*{scale:g}"
        if self.last_ctype == ChannelType.MTrend:
            label += " [m-trend]"
        elif self.last_ctype == ChannelType.STrend:
            label += " [s-trend]"
        return label

    def set_mean_curve_visibility(self, visible: bool):
        self.curves["y"].setVisible(visible)

    def set_min_curve_visibility(self, visible: bool):
        self.curves["min"].setVisible(visible)

    def set_max_curve_visibility(self, visible: bool):
        self.curves["max"].setVisible(visible)

    def set_rms_curve_visibility(self, visible: bool):
        self.curves["rms"].setVisible(visible)

    def clear_data(self):
        """clear data for curves"""
        self.data = {}
        for curve in self.curves.values():
            try:
                curve.setData(np.array([0, 0]))
            except Exception:
                pass

    def _update_curve_data(self, mod, t=None):
        if mod not in self.data:
            return None, None
        y = self.data[mod].data
        if t is None:
            t = self.data[mod].tarray_sec(self.t0)
        # FIXME: HACK: replace all +-infs with nans.  the infs
        # were causing the following exception in PlotCurveItem
        # when it tried to find the min/max of the array:
        # ValueError: zero-size array to reduction operation minimum which has no identity
        # using nan is not great, since that's also an indicator
        # of a gap, but not sure what else to use.
        try:
            np.place(y, np.isinf(y), np.nan)
        except ValueError:
            # this check throws a value error if y is int.  but in
            # that case there's nothing we need to convert, so
            # just pass
            pass
        y = self.transform(y)
        if mod == TrendStat.Raw:
            cid = "y"
        elif mod == TrendStat.Mean:
            cid = "y"
        elif mod == TrendStat.Min:
            cid = "min"
        elif mod == TrendStat.Max:
            cid = "max"
        else:
            raise Exception("Unknown trend stat")
        self.curves[cid].setData(
            x=t,
            y=y,
            connect="finite",
        )
        return t, y

    def _redraw_curves(self):
        """redraw all data"""
        if not self.data:
            return
        if TrendStat.Raw in self.data:
            t, y = self._update_curve_data(TrendStat.Raw)
        else:
            for mod in [TrendStat.Min, TrendStat.Max, TrendStat.Mean]:
                t, y = self._update_curve_data(mod)
        return t, y

    def set_ctype(self, ctype: ChannelType):
        if self.last_ctype != ctype:
            logger.debug("set ctype=%s", str(ctype))
            self.last_ctype = ctype
            logger.debug("updating label")
            self._update_label()

    def set_data(self, data: DataBuffer, t0: PipInstant):
        """set data for curves

        Data should be DataBuffer object.

        """
        if self.data:
            ctype_changed = data.ctype != self.last_ctype
        else:
            ctype_changed = True

        if ctype_changed:
            self.data = {}

        self.data[data.trend_stat] = data
        self.t0 = t0

        t, y = self._redraw_curves()

        if t is not None:
            self.curves["bad"].setData(
                x=t,
                y=hold_over_nan(y),
                connect="finite",
            )

        if ctype_changed:
            self.last_ctype = data.ctype
            self._update_label()

    def set_result(self, result: "Result"):
        self.data = result
        self.t0 = PipInstant.gpst_epoch()
        self._redraw_curves()


##################################################


def hold_over_nan(y: np.ndarray):
    """hold data over subsequent nans

    This function finds all nans in the input array, and produces an
    output array that is nan everywhere except where the input array
    was nan.  Where the input array was nan, the output array will be
    the value of the input array right before the nan.  If the first
    element of the input array is nan then zero will be used.
    Example:

    y   = [nan, nan,   2,   3,   4,   5, nan, nan, nan,   9,  10]
    out = [  0,   0,   0, nan, nan,   5,   5,   5,   5,   5, nan]

    We use this for indicating "bad" data regions in plots.

    """
    nani = np.where(np.isnan(y))[0]
    if nani.size == y.size:
        return np.zeros_like(y, dtype=float)
    out = np.empty_like(y, dtype=float)
    out[:] = np.nan
    if nani.size == 0:
        return out
    ti = np.where(np.diff(nani) > 1)[0]
    nstart = np.append(nani[0], nani[ti + 1])
    nend = np.append(nani[ti], nani[-1]) + 1
    for s, e in zip(nstart, nend):
        if s == 0:
            v = 0
        else:
            v = y[s - 1]
        out[s - 1 : e + 1] = v
    return out


def get_nan_spans(y: np.ndarray):
    """
    Return a list of pairs of indicies that mark the beginning and end of NaN segments
    """
