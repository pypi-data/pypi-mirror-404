# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import copy
import traceback
import subprocess
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from qtpy import QtGui, QtWidgets
from qtpy import QtCore
from qtpy.QtCore import Signal  # type: ignore
from qtpy.QtCore import Qt, QRegularExpression, QTimer
from qtpy.QtWidgets import QStyle, QFileDialog, QFontDialog
from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QFont
import pyqtgraph as pg
from pyqtgraph import exporters
from dttlib import (
    PipInstant,
    PipDuration,
    TrendType,
    AnalysisRequestId,
    AnalysisNameId,
    AnalysisId,
)

# NOTE: must be imported after pyqt or else config is reset
import logging

from ndscope.math_config import MathConfigDialog


from . import __version__
from ._qt import load_ui
from . import const
from . import util
from .plot import NDScopePlot, NDScopePlotChannel
from .trigger import Trigger
from .crosshair import Crosshair
from . import export
from . import dialog
from . import channel_select
from .dtt.channel_trend_id import ChannelTrendId
from .primary_view import PrimaryView
from .cache import PrimedCache
import traceback
from .cache import DataCache
from .dtt import AnalysisResult
from .data import DataBufferDict


if TYPE_CHECKING:
    from nds import Channel
    from .result import Result

logger = logging.getLogger("SCOPE")

##################################################
# CONFIG


if os.getenv("ANTIALIAS"):
    pg.setConfigOption("antialias", True)
    logger.info("Anti-aliasing ENABLED")
# pg.setConfigOption('leftButtonPan', False)
# see also ViewBox.setMouseMode(ViewBox.RectMode)
# file:///usr/share/doc/python-pyqtgraph-doc/html/graphicsItems/viewbox.html#pyqtgraph.ViewBox.setMouseMode


STATUS_STYLES = {
    "data": "background: rgba(0,100,0,100);",
    "msg": "background: rgba(0,0,100,100);",
    "error": "background: rgba(255,0,0,255); color: white; font-weight: bold;",
}

URL_MAIN = "https://git.ligo.org/cds/software/ndscope"
URL_RELEASE = (
    "https://git.ligo.org/cds/software/ndscope/-/blob/master/NEWS.md?ref_type=heads"
)
URL_ISSUE = "https://git.ligo.org/cds/software/ndscope/issues"

TREND_OPTIONS = [
    "auto",
    "raw",
    "sec",
    "min",
]


class BuildChannelModelsThread(QtCore.QThread):
    done_signal = Signal("PyQt_PyObject")

    def __init__(self, channels: Dict[str, "Channel"]):
        super().__init__()
        self.channels = channels

    def run(self):
        channel_list = list(sorted(self.channels.values(), key=lambda c: c.name))
        tree_model = channel_select.AvailableChannelTreeModel(channel_list)
        table_model = channel_select.AvailableChannelTableModel(channel_list)
        self.done_signal.emit((tree_model, table_model))


##################################################


class Transaction(object):
    """
    Context object used to delay requests for data until the context is exited.
    Reduces wasteful data requests on incomplete configurations.
    with Transaction(scope):
        scope.set_trend()
        scope.set_window()
        scope.set_online()
    """

    def __init__(self, scope: "NDScope", single_shot=False):
        self.scope = scope
        self.request_data = False
        self.real_request_data = None
        self.force = False
        self.single_shot = single_shot

        # hold a datacachecontext so that other processes can't route around
        # the transaction by directly setting the data cache
        self.cache_context = self.scope.data.update_context(self.force)

    def __enter__(self):
        self.cache_context.__enter__()
        self.real_request_data = self.scope._data_request
        self.scope._data_request = self.data_request_dummy
        return self

    def data_request_dummy(self, force=False):
        self.request_data = True
        self.force = self.force or force

    def __exit__(self, exc_Type, exc_value, traceback):
        self.scope._data_request = self.real_request_data
        if self.request_data:
            self.scope._data_request(self.force, singleshot=self.single_shot)
        self.cache_context.__exit__(None, None, None)


class NDScope(*load_ui("scope.ui")):
    _channel_models_ready = Signal()
    _plots_updated = Signal()
    _export_complete = Signal()

    def __init__(self):
        """initilize NDScope object"""
        super().__init__(None)
        self.data = DataCache(self)
        self.setupUi(self)

        server, self.server_formatted = util.format_nds_server_string()
        logger.info(f"version {__version__}")
        logger.info(f"server {server}")
        self.labelServer = QtWidgets.QLabel(f"{self.server_formatted}")
        self.labelServer.setToolTip("NDS server")
        # add a little space
        self.statusBar.addWidget(QtWidgets.QLabel())
        self.statusBar.addWidget(self.labelServer)
        self.labelChannelCount = QtWidgets.QLabel("[waiting for channels...]")
        self.labelChannelCount.setToolTip("channel count")
        # the '1' add stretch to push the next label to the right side
        self.statusBar.addWidget(self.labelChannelCount, 1)
        labelHome = QtWidgets.QLabel(
            f"<a href={URL_MAIN}>ndscope</a> <a href={URL_RELEASE}>{__version__}</a> (<a href={URL_ISSUE}>report bug</a>)"
        )
        labelHome.setOpenExternalLinks(True)
        self.statusBar.addWidget(labelHome)
        self.statusClearButton = QtWidgets.QPushButton("clear")
        # permanent widgets are added to the right side
        self.statusBar.addPermanentWidget(self.statusClearButton)
        self.statusBar.messageChanged.connect(self.status_clear_callback)
        self.statusClearButton.clicked.connect(self.status_clear)
        self.status_clear()

        self.t0 = PipInstant.gpst_epoch()
        self._error = False
        self._dialogs = {}
        self._channel_list_widget = None
        self._channel_config_dialog = channel_select.PlotChannelConfigDialog(self)
        self._channel_config_dialog.channel_list_button.setEnabled(False)

        # hide the math button because the interface is not ready yet
        self._channel_config_dialog.math_button.hide()

        self.channelListButton.setEnabled(False)
        self.channelListButton2.setEnabled(False)
        self.primary_view = PrimaryView()
        self.primary_view.enableAutoRange(axis="x", enable=False)
        self.XRangeChanged_callback_proxy = pg.SignalProxy(
            self.primary_view.sigXRangeChanged,
            rateLimit=1,
            slot=self.XRangeChanged_callback,
        )

        # this holds a reference to the channel select menu creation
        # thread, so it's not inadvertently cleaned up
        self._bcsmt = None
        # flag to indicate that we are in a base state with no
        # channels declared
        self._base = True

        # FIXME: HACK: this is an attempt to bypass the following bug:
        #
        # Traceback (most recent call last):
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/GraphicsObject.py", line 23, in itemChange
        #     self.parentChanged()
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/GraphicsItem.py", line 440, in parentChanged
        #     self._updateView()
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/GraphicsItem.py", line 492, in _updateView
        #     self.viewRangeChanged()
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/PlotDataItem.py", line 671, in viewRangeChanged
        #     self.updateItems()
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/PlotDataItem.py", line 483, in updateItems
        #     x,y = self.getData()
        #   File "/usr/lib/python3/dist-packages/pyqtgraph/graphicsItems/PlotDataItem.py", line 561, in getData
        #     if view is None or not view.autoRangeEnabled()[0]:
        # AttributeError: 'GraphicsLayoutWidget' object has no attribute 'autoRangeEnabled'
        def autoRangeEnabled():
            return False, False

        self.graphView.autoRangeEnabled = autoRangeEnabled

        self.graphView.dragEnterEvent = lambda event: event.setAccepted(
            event.mimeData().hasFormat("text/plain")
        )

        ##########
        # data and data retrieval
        self.last_cmd = (None, {})
        self.last_data = (None, PipInstant.gpst_epoch(), PipInstant.gpst_epoch())
        self.last_results: Dict[str, Result] = {}
        self.last_request = (None, PipInstant.gpst_epoch(), PipInstant.gpst_epoch())

        self.data.signal_channel_list_ready.connect(self._channel_list_ready_callback)
        self.data.signal_channel_change.connect(self._channel_change_callback)

        self.data.signal_stream_status.connect(self._data_stream_status)
        self.data.signal_online_status.connect(self._data_online_status)
        self.data.signal_stream_error.connect(self._data_stream_error)
        self.data.signal_data.connect(self._update_plots, Qt.QueuedConnection)  # type: ignore

        self.data.signal_request_sasl.connect(self.auth_dialog)

        ##########
        # window/range entry

        def NonEmptyValidator():
            return QtGui.QRegularExpressionValidator(QRegularExpression(".+"))

        self.entryT0GPS.textEdited.connect(self.update_entryT0Greg)
        self.entryT0GPS.setValidator(QtGui.QDoubleValidator())
        self.entryT0GPS.returnPressed.connect(self.update_t0)

        self.entryT0Greg.textEdited.connect(self.update_entryT0GPS)
        self.entryT0Greg.setValidator(NonEmptyValidator())
        self.entryT0Greg.returnPressed.connect(self.update_t0)

        self.buttonT0Now.clicked.connect(self.set_entryT0)

        self.entryWindowStart.setValidator(QtGui.QDoubleValidator())
        self.entryWindowStart.returnPressed.connect(self.update_window)

        self.entryWindowEnd.setValidator(QtGui.QDoubleValidator())
        self.entryWindowEnd.returnPressed.connect(self.update_window)

        self.entryStartGPS.textEdited.connect(self.update_entryStartGreg)
        self.entryStartGPS.setValidator(QtGui.QDoubleValidator())
        self.entryStartGPS.returnPressed.connect(self.update_range)

        self.entryStartGreg.textEdited.connect(self.update_entryStartGPS)
        self.entryStartGreg.setValidator(NonEmptyValidator())
        self.entryStartGreg.returnPressed.connect(self.update_range)

        self.entryEndGPS.setValidator(QtGui.QDoubleValidator())
        self.entryEndGPS.textEdited.connect(self.update_entryEndGreg)
        self.entryEndGPS.returnPressed.connect(self.update_range)

        self.entryEndGreg.textEdited.connect(self.update_entryEndGPS)
        self.entryEndGreg.setValidator(NonEmptyValidator())
        self.entryEndGreg.returnPressed.connect(self.update_range)

        self.buttonEndNow.clicked.connect(self.set_entryEnd)

        self.fetchButton1.clicked.connect(self.update_t0)
        self.fetchButton2.clicked.connect(self.update_range)

        self.resetYAxisWidthButton.clicked.connect(self.reset_axis_width)

        ##########
        # trend

        self.trendSelectGroup = QtWidgets.QButtonGroup()
        # NOTE: the numbers correspond to indices in TREND_OPTIONS
        self.trendSelectGroup.addButton(self.trendAutoSelect, 0)
        self.trendSelectGroup.addButton(self.trendRawSelect, 1)
        self.trendSelectGroup.addButton(self.trendSecSelect, 2)
        self.trendSelectGroup.addButton(self.trendMinSelect, 3)
        self.trendSelectGroup.buttonClicked.connect(self._trend_select)

        self.trendRawSecThresh.setValidator(QtGui.QIntValidator())
        self.trendRawSecThresh.setText(str(const.TREND_TRANS_THRESHOLD["raw/sec"]))
        self.trendRawSecThresh.returnPressed.connect(self._set_trend_rawsec)

        self.trendSecMinThresh.setValidator(QtGui.QIntValidator())
        self.trendSecMinThresh.setText(str(const.TREND_TRANS_THRESHOLD["sec/min"]))
        self.trendSecMinThresh.returnPressed.connect(self._set_trend_secmin)

        self.trendMeanVisibility.stateChanged.connect(
            self.trend_mean_visibility_state_changed_slot
        )
        self.trendMinVisibility.stateChanged.connect(
            self.trend_min_visibility_state_changed_slot
        )
        self.trendMaxVisibility.stateChanged.connect(
            self.trend_max_visibility_state_changed_slot
        )
        self.trendRmsVisibility.stateChanged.connect(
            self.trend_rms_visibility_state_changed_slot
        )

        ##########
        # axis

        self.timeAxisModeButtonGroup.buttonClicked.connect(self._set_time_axis_mode)

        ##########
        # triggere data in {} - {} for {}",

        self.trigger = Trigger()
        self.trigger.level_changed_signal.connect(self._update_triggerLevel)
        self.triggerLevel.setValidator(QtGui.QDoubleValidator())
        self.triggerLevel.returnPressed.connect(self._set_trigger_level)
        self.triggerResetLevel.clicked.connect(self.reset_trigger_level)
        self.triggerSingle.clicked.connect(self.trigger.set_single)
        self.triggerInvert.clicked.connect(self.trigger.set_invert)
        self.triggerGroup.toggled.connect(self._toggle_trigger)
        self.data.signal_trend_change.connect(self.trigger.on_trend_change)

        ##########
        # crosshair

        self.crosshair = Crosshair()
        self.crosshair.signal_position.connect(self._update_crosshair_entry)
        self._crosshair_proxy = None
        self.crosshairGroup.toggled.connect(self._toggle_crosshair)

        ##########
        # style

        self.fontSizeSelect.valueChanged.connect(self.set_font_size)
        self.lineWidthSelect.valueChanged.connect(self.set_line_width)
        self.gridAlphaSelect.valueChanged.connect(self.set_grid_alpha)
        self.colorModeButtonGroup.buttonClicked.connect(self.set_color_mode)

        ##########
        # export

        self.exportButton.clicked.connect(self.export)
        self.exportPath.returnPressed.connect(self._export_save_handler)
        self.exportSaveButton.clicked.connect(self._export_save_handler)
        self.exportShowButton.clicked.connect(self._export_show_handler)
        self.exportButton2.clicked.connect(self.snapshot)

        ##########
        # controls

        self.controlBar.hide()
        self.controlExpandButton.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarShadeButton)  # type: ignore
        )
        self.controlExpandButton.setText("")
        self.controlExpandButton.clicked.connect(self.control_expand)
        self.controlCollapseButton.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton)  # type: ignore
        )
        self.controlCollapseButton.setText("")
        self.controlCollapseButton.clicked.connect(self.control_collapse)

        self.startButton.clicked.connect(self.start)
        self.startButton2.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)
        self.stopButton2.clicked.connect(self.stop)
        self.resetRangeButton.clicked.connect(self.reset)
        self.resetRangeButton2.clicked.connect(self.reset)

        self.channelListButton.clicked.connect(self.show_channel_list)
        self.channelListButton2.clicked.connect(self.show_channel_list)

        ##########
        # button icons
        # FIXME: should set this in .ui somehow

        self.startButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # type: ignore
        self.startButton2.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # type: ignore
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))  # type: ignore
        self.stopButton2.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))  # type: ignore
        # self.fetchButton1.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        # self.fetchButton2.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        # self.resetRangeButton.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        # self.resetRangeButton2.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.exportButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))  # type: ignore
        self.exportSaveButton.setIcon(
            self.style().standardIcon(QStyle.SP_DialogSaveButton)  # type: ignore
        )
        self.exportShowButton.setIcon(
            self.style().standardIcon(QStyle.SP_FileDialogContentsView)  # type: ignore
        )
        # self.exportButton2.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))

        ##########
        # initial config

        self.setWindowTitle("ndscope")
        self._base_ui()
        self.plotLayout = self.graphView.addLayout()
        self.graphView.nextRow()
        self.referenceTimeLabel = self.graphView.addLabel("t0")
        self.set_color_mode("dark")
        self.set_font_size(10)
        self.add_plot()
        gps_now = util.gpstime_parse("now")
        if gps_now is not None:
            self._set_t0(PipInstant.from_gpst_seconds(gps_now.gps()))
        self.set_online_window(PipDuration.from_sec(2))
        self.last_cmd = ("start", {"window": self.get_window()})

        # used to ignore data we've already seen
        self.last_data_id = 0

        self.first_paint = 2

    def paintEvent(self, evt):
        if self.first_paint > 0:
            self.first_paint -= 1
            self.reset_axis_width()
        return super().paintEvent(evt)

    ##########

    def single_shot_export(self, path):
        """Export scene to path then exit

        This is intended to be called before show() at app
        initialization to setup the export of the scene after an
        initial data fetch is complete.

        """
        # this prevents the data object from fetching the channel list
        self.data.available_channels = {}

        def _done_export(view_id):
            # QtCore.QTimer.singleShot(1, lambda: self.export(path))
            logger.debug("single shot export of view id %d", view_id)
            self.export(path)

        self.data.signal_view_done.connect(_done_export)
        self._export_complete.connect(QApplication.quit)

    ##########

    def set_font(self, font):
        self.setFont(font)
        self.fontSizeSelect.setValue(font.pointSize())
        referenceTimeLabelFont = QFont(font)
        referenceTimeLabelFont.setPointSize(font.pointSize() + 2)
        self.referenceTimeLabel.item.setFont(referenceTimeLabelFont)
        self.crosshair.set_font(font)
        self.trigger.set_font(font)
        for plot in self.plots:
            plot.set_font(font)
        QApplication.processEvents()
        self.reset_axis_width()

    def reset_axis_width(self):
        if len(self.plots) > 0:
            self.plots[0].update_axis_width()

    def set_font_size(self, size):
        """Set font size for plots"""
        font = self.font()
        font.setPointSize(size)
        self.set_font(font)

    @property
    def _color_mode(self):
        if self.darkModeButton.isChecked():
            return "dark"
        elif self.lightModeButton.isChecked():
            return "light"

    def set_color_mode(self, mode):
        """set color mode to "light" or "dark" """
        if isinstance(mode, QtWidgets.QRadioButton):
            mode = mode.text()
        fg = const.COLOR_MODE[mode]["fg"]
        bg = const.COLOR_MODE[mode]["bg"]
        self.graphView.setBackground(bg)
        self.referenceTimeLabel.setAttr("color", fg)
        self.referenceTimeLabel.setText(self.referenceTimeLabel.text)
        self.crosshair.set_color_mode(mode)
        self.trigger.set_color_mode(mode)
        for plot in self.plots:
            plot.set_color_mode(mode)
        if mode == "light":
            self.lightModeButton.setChecked(True)
        elif mode == "dark":
            self.darkModeButton.setChecked(True)

    def set_line_width(self, width):
        """set line width for all plots

        This overrides any individual trace settings.

        """
        assert isinstance(width, int)
        for plot in self.plots:
            for cc in plot.channels.values():
                cc.set_params(width=width)

    def set_grid_alpha(self, value):
        """set grid line alpha for all plots"""
        for plot in self.plots:
            plot.showGrid(alpha=value)

    ##########

    def _base_ui(self):
        # UI with no channels
        self.startButton.setEnabled(False)
        self.startButton2.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.stopButton2.setEnabled(False)
        self.resetRangeButton.setEnabled(False)
        self.resetRangeButton2.setEnabled(False)
        self.windowTab.setEnabled(False)
        self.rangeTab.setEnabled(False)
        self.crosshairTab.setEnabled(False)
        self.axisTab.setEnabled(True)
        self.exportTab.setEnabled(False)
        self.exportButton2.setEnabled(False)

    def _offline_ui(self):
        # UI with channels
        self.startButton.setEnabled(True)
        self.startButton2.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.stopButton2.setEnabled(False)
        self.resetRangeButton.setEnabled(True)
        self.resetRangeButton2.setEnabled(True)
        self.windowTab.setEnabled(True)
        self.rangeTab.setEnabled(True)
        self.crosshairTab.setEnabled(True)
        self.axisTab.setEnabled(True)
        self.exportTab.setEnabled(True)
        self.exportButton2.setEnabled(True)

    def _online_ui(self):
        # UI when online
        self.startButton.setEnabled(False)
        self.startButton2.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.stopButton2.setEnabled(True)
        self.resetRangeButton.setEnabled(True)
        self.resetRangeButton2.setEnabled(True)
        self.windowTab.setEnabled(True)
        self.rangeTab.setEnabled(False)
        self.crosshairTab.setEnabled(False)
        self.axisTab.setEnabled(False)
        self.exportTab.setEnabled(False)
        self.exportButton2.setEnabled(False)

    ##########
    # status bar

    def status_clear(self, text=None):
        logger.debug("Clearing status")
        self._error = False
        self.statusBar.setStyleSheet("")
        self.statusClearButton.setVisible(False)
        self.statusBar.clearMessage()

    def status_clear_callback(self, text):
        # this method is connected to the statusBar.messageChanged
        # slot, so that the status bar is reset when a temporary
        # message is cleared. but we only want to reset when it's
        # cleared (text is empty), not when a new message is added.
        logger.debug("status clear callback")
        if (not self._error) and text == "":
            self.status_clear("MSG")

    def status_message(self, msg, timeout=0, style="msg", clear_button=False, log=True):
        self._error = False
        if log:
            logger.warning(msg)
        style = STATUS_STYLES.get(style)
        if style:
            self.statusBar.setStyleSheet(f"QStatusBar{{{style}}}")
        self.statusBar.showMessage(msg, int(timeout * 1000))
        if clear_button:
            self.statusClearButton.setVisible(True)
        else:
            self.statusClearButton.setVisible(False)

    def status_error(self, msg):
        logger.error("[status error] %s", msg)
        self.statusBar.setStyleSheet(STATUS_STYLES["error"])
        self.statusBar.showMessage(msg)
        self.statusClearButton.setVisible(True)
        self._error = True

    ##########
    # dialogs

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for dlg in self._dialogs.values():
            dlg.move(0, 0)
            dlg.resize(self.width(), self.height())

    def _dialog_create(self, name, d, callback=None):
        self._dialogs[name] = dialog.DialogOverlayWidget(d, self)
        if callback:
            self._dialogs[name].done_signal.connect(callback)
        self._dialogs[name].show()

    def _dialog_cleanup(self, name):
        if name not in self._dialogs:
            return
        try:
            self._dialogs[name].done_signal.disconnect()
        except AttributeError:
            pass
        self._dialogs[name].close()
        del self._dialogs[name]

    def auth_dialog(self):
        if "auth" in self._dialogs and self._dialogs["auth"].isVisible():
            return
        d = dialog.NDSAuthDialog(self)
        self._dialog_create("auth", d, callback=self.auth_dialog_result)
        d.usernameEntry.setFocus()

    def auth_dialog_result(self, result=None):
        self._dialog_cleanup("auth")
        if not result:
            # FIXME: this is not the right place to clean this stuff
            # up, but unclear where else it should be done.
            self._dialog_cleanup("channel-wait")
            self._channel_models_ready.disconnect()
            return
        self.data.fetch_channel_list_async()
        self.reset()

    def ontape_dialog(self):
        if "tape" in self._dialogs and self._dialogs["tape"].isVisible():
            return
        d = dialog.NDSOnTapeDialog(self)
        self._dialog_create("tape", d, callback=self.ontape_dialog_result)

    def ontape_dialog_result(self, result=None):
        self._dialog_cleanup("tape")
        if not result:
            return
        os.environ["NDS2_CLIENT_ALLOW_DATA_ON_TAPE"] = "TRUE"
        self.reset()

    ##########
    # controls box

    def control_expand(self):
        self.controlBarSmall.hide()
        self.controlBar.show()

    def control_collapse(self):
        self.controlBar.hide()
        self.controlBarSmall.show()

    ##########
    # CHANNELS AND PLOTS

    @property
    def plots(self) -> List[NDScopePlot]:
        """list of scope plots"""
        return list(self.plotLayout.items.keys())

    @property
    def plot0(self):
        """base plot at (0,0) location"""
        return self.plotLayout.getItem(0, 0)

    def get_plot_locations(self):
        """iterator of plot locations as (row, col) tuples"""
        for plot, cells in self.plotLayout.items.items():
            tabspec = util.cells_to_tabspec(cells)
            yield plot, (tabspec["row"], tabspec["col"])

    def get_plot_location(self, plot):
        """return plot location as (row, col)"""
        for p, loc in self.get_plot_locations():
            if plot == p:
                return loc

    def add_plot(self, channels=None, title=None, **kwargs):
        """Add plot to the scope

        If provided `channels` should be a list of channel:property
        dicts to add to the plot on initialization.

        """
        self.status_clear()
        logger.info(f"creating plot {kwargs}...")

        # check that there's not already a plot at the requested location
        loc = (kwargs.get("row"), kwargs.get("col"))
        for plot, ploc in self.get_plot_locations():
            if loc == ploc:
                raise ValueError(f"Plot already exists at location {ploc}.")

        plot = NDScopePlot(self.data, title=title, loc=loc)
        plot.set_color_mode(self._color_mode)

        # connect plot signals
        plot.t0_reset.connect(self.reset_t0_relative)
        plot.t_cursors_enable.connect(self._t_cursors_enable)
        plot.t_cursor_moved.connect(self._update_t_cursor)
        plot.log_mode_toggled.connect(self.crosshair.redraw)
        plot.log_mode_toggled.connect(self.trigger.redraw)
        plot.channel_config_request.connect(self.config_channels)
        plot.new_plot_request.connect(self._add_plot_handler)
        plot.remove_plot_request.connect(self.remove_plot)
        plot.channels_updated.connect(self.update_all_curves_visibility)

        # filter out non-layout arguments
        log_scale = kwargs.pop("log-scale", False)
        # FIXME: deprecate the old "yrange" argument in favor of "y-range"
        y_range = kwargs.pop("y-range", kwargs.pop("yrange", None))
        # FIXME: where to add if row/col not specified?  need some
        # sort of layout policy
        self.plotLayout.addItem(
            plot,
            **kwargs,
        )

        # HACK: this is how to remove the "export" command from the
        # context menu
        plot.scene().contextMenu = None  # type: ignore

        if plot.axes is not None:
            # set time axis mode
            plot.axes["bottom"]["item"].set_t0(self.t0)
            plot.axes["bottom"]["item"].setTickStringsMode(self.active_time_axis_mode)

            logger.info("connecting to plot 0...")
            # plot.setXLink(self.plot0)  # type: ignore
            plot.setXLink(self.primary_view)  # type: ignore
        else:
            raise ValueError("Attempted to connect mouse gestures to plot with no axes")

        if channels:
            # FIXME: the plot.add_channels method takes a dictionary
            # of channel:curve items, but the template returns a list
            # of single element channel:curve dicts.  the template
            # handling should be fixed to just return a single
            # channel:curve dictionary, but i think it was implemented
            # this way so that the template yaml looked cleaner
            channels = {
                list(chan.keys())[0]: list(chan.values())[0] for chan in channels
            }
            plot.add_channels(channels)
            self.update_all_curves_visibility()

        # set Y scale first because it necessarily turns on autoscale
        if log_scale:
            plot.vb.menu.yAxisUI.logModeCheck.setChecked(True)  # type: ignore
            plot.set_log_mode(log_scale)
        if y_range:
            plot.set_y_range(y_range)

        self.set_font(self.font())

        return plot

    def _add_plot_handler(self, recv):
        """handler to add new plot based on signal from plotMenu"""
        ref_plot, new_loc, plot_kwargs = recv
        occupied_cells = set()
        tabspec = None
        for plot, cells in self.plotLayout.items.items():
            occupied_cells.update(cells)
            if plot == ref_plot:
                tabspec = util.cells_to_tabspec(cells)
        if tabspec is not None:
            rowcol = (tabspec["row"], tabspec["col"])
            row, col = rowcol
            while rowcol in occupied_cells:
                row, col = rowcol
                if new_loc == "row":
                    col += 1
                elif new_loc == "col":
                    row += 1
                rowcol = (row, col)
            plot_kwargs["row"] = row
            plot_kwargs["col"] = col
            self.add_plot(**plot_kwargs)
        else:
            logger.error("_add_plot_handler could not find plot")

    def remove_plot(self, plot, _force=False):
        """remove plot from layout"""
        self.status_clear()
        loc = self.get_plot_location(plot)
        logger.info(f"removing plot: {loc}")
        if _force is not True:
            if len(self.plots) == 1:
                self.status_error("Can not remove last plot.")
                return
            if loc == (0, 0):
                self.status_error("Can not remove (0,0) plot.")
                return
        plot.remove_channels()
        plot.log_mode_toggled.disconnect()
        # turn off timebase cursors so that cursor class doesn't use them to fix position
        # of cursors
        plot.enable_t_cursors().set_visible(C1=False, C2=False)
        self.plotLayout.removeItem(plot)

    def plots4chan(self, channel: str):
        """Return list of plots displaying channel"""
        plots = []
        for plot in self.plots:
            if channel in plot.channels:
                plots.append(plot)
        return plots

    def channels_as_names(self) -> Set[str]:
        chans: Set[str] = set()
        for plot in self.plots:
            chans = chans.union(set(plot.channels.keys()))
        return chans

    def channels_as_analysis_name_ids(self) -> Set[AnalysisNameId]:
        x = {MathConfigDialog.name_to_name_id(n) for n in self.channels_as_names()}
        return x

    def channels_as_analysis_request_ids(self) -> Set[AnalysisRequestId]:
        x = {
            i.add_trend(self.preferred_trend())
            for i in self.channels_as_analysis_name_ids()
        }
        return x

    def _channel_list_ready_callback(self):
        if self.data.available_channels is not None:
            logger.debug("building channel models...")
            t = BuildChannelModelsThread(self.data.available_channels)
            t.done_signal.connect(self._channel_models_ready_callback)
            t.start()
            # hold a reference to the thread until it's done
            self._bcsmt = t
        else:
            logger.warning(
                "_channel_list_ready_callback called when there was no channel list"
            )

    def _channel_models_ready_callback(self, recv):
        channel_tree_model, channel_table_model = recv
        if self.data.available_channels:
            nchannels = len(self.data.available_channels)
            self._channel_list_widget = channel_select.ChannelListWidget(
                channel_tree_model, channel_table_model
            )
            self._channel_list_widget.set_server_info(self.server_formatted, nchannels)
            self._channel_list_dialog = channel_select.ChannelListDialog(
                self._channel_list_widget,
                parent=self,
            )
            self._channel_list_dialog.accepted.connect(self._channel_list_accepted)
            self._channel_config_dialog.channel_list_button.clicked.connect(
                self.show_channel_list
            )
            self.channelListButton.setEnabled(True)
            self.channelListButton2.setEnabled(True)
            self._channel_config_dialog.channel_list_button.setEnabled(True)
            self._bcsmt = None
            logger.debug("channel list ready.")
            self.labelChannelCount.setText(f"[{nchannels} channels]")
            self._channel_models_ready.emit()
        else:
            logger.warning(
                "_channel_models_ready_callback called when there was no channel list"
            )

    def _channel_list_accepted(self):
        names = self._channel_list_dialog.get_channel_names()
        if self._channel_config_dialog.isVisible():
            for name in names:
                self._channel_config_dialog.add_channel(name)
        elif len(self.plots) == 1:
            chans = {n: {} for n in names}
            self.plot0.add_channels(chans)
        self.update_all_curves_visibility()

    def show_channel_list(self):
        """Show the channel list window"""
        self._channel_list_dialog.show()

    def config_channels(self, plot=None):
        """Present the channel select dialog

        If no plot is specified, assume plot0

        """
        if "config" in self._dialogs and self._dialogs["config"].isVisible():
            return
        if not plot:
            plot = self.plot0
        self._channel_config_dialog.set_plot(plot)
        self._dialog_create(
            "config",
            self._channel_config_dialog,
            callback=lambda chans: self._channel_config_dialog_result(plot, chans),
        )

    def _channel_config_dialog_result(
        self, plot: NDScopePlot, channel_list: List[NDScopePlotChannel]
    ):
        self._dialog_cleanup("config")
        if channel_list is None:
            return
        plot.set_channel_objs(channel_list)

    def _channel_change_callback(self, recv):
        """callback to update scope when channel added or removed"""
        error = recv
        if error:
            self.status_error(error)
            return
        self._update_triggerSelect()
        if self.data.empty:
            self._base = True
            self._base_ui()
            # self.select_channels()
        elif self._base:
            # if we were in the base state (no channels) start the
            # online stream when new channels are added
            self._base = False
            self.start()
        else:
            pass

    def load_template(self, template, single_shot: bool):
        """Load scope template from template dictionary"""
        logger.info("loading template...")

        with Transaction(self, single_shot):
            # remove the base state flag immediately, so that we don't
            # start online streams during template loading
            self._base = False

            # If there is more than one plot then check the layout to make sure
            # there's a (0,0) plot specified.
            # If there is only one plot then move it to (0,0).
            if len(template["plots"]) == 1:
                plot = template["plots"][0]
                plot["row"] = 0
                plot["col"] = 0
                plot0 = plot
            else:
                for plot in template["plots"]:
                    loc = (plot.get("row"), plot.get("col"))
                    if loc == (0, 0):
                        plot0 = plot
                        break
                else:
                    raise ValueError(
                        "Template plot layout with more than one plot must specify a plot at row=0, col=0."
                    )

            title = template.get("window-title")
            if title:
                self.setWindowTitle("ndscope: {}".format(title))
            font_size = template.get("font-size")
            if font_size:
                self.set_font_size(font_size)
            # FIXME: DEPRECATE
            if "black-on-white" in template:
                logger.warning(
                    "WARNING: Template key 'black-on-white' is deprecated, please use 'color-mode: light' instead."
                )
                if template.get("black-on-white"):
                    self.set_color_mode("light")
                else:
                    self.set_color_mode("dark")
            color_mode = template.get("color-mode")
            if color_mode:
                self.set_color_mode(color_mode)
            trend = template.get("trend", "auto")
            if trend == "auto":
                self.trendAutoSelect.click()
            elif trend == "raw":
                self.trendRawSelect.click()
            elif trend == "sec":
                self.trendSecSelect.click()
            elif trend == "min":
                self.trendMinSelect.click()
            QApplication.processEvents()
            trend_auto_raw_sec = template.get("trend-auto-raw-sec")
            if trend_auto_raw_sec:
                self.trendRawSecThresh.clear()
                self.trendRawSecThresh.insert(str(trend_auto_raw_sec))
            trend_auto_sec_min = template.get("trend-auto-sec-min")
            if trend_auto_sec_min:
                self.trendSecMinThresh.clear()
                self.trendSecMinThresh.insert(str(trend_auto_sec_min))

            # clear *all* plots from the scope, including the base 0,0 plot
            logger.info("clearing plots...")
            for p in self.plots:
                self.remove_plot(p, _force=True)

            def add_plot(p):
                t_cursors = p.pop("t-cursors", None)
                y_cursors = p.pop("y-cursors", None)
                plot = self.add_plot(**p)
                if t_cursors:
                    plot.enable_t_cursors().load(t_cursors)
                if y_cursors:
                    plot.enable_y_cursors().load(y_cursors)

            # add the (0, 0) plot first
            add_plot(plot0)
            # then add the rest
            for plot in template["plots"]:
                loc = (plot["row"], plot["col"])
                if loc == (0, 0):
                    continue
                add_plot(plot)

            line_width = template.get("line-width")
            if line_width:
                self.lineWidthSelect.setValue(line_width)

            grid_alpha = template.get("grid-alpha")
            if grid_alpha:
                self.gridAlphaSelect.setValue(grid_alpha)

            t_cursors = template.get("t-cursors")
            if t_cursors:
                self.load_t_cursors(t_cursors)

            time_axis_mode = template.get("time-axis-mode")
            if time_axis_mode:
                self.set_time_axis_mode(time_axis_mode)

            if self.data.empty:
                self._base = True
                return

            # save and then reload after t0 set
            t_cursors = self.get_t_cursor_values()

            t0 = template.get("t0")
            window = template.get("time-window")
            logger.info(f"t0={t0}, window={window}")
            if t0:
                self.fetch(
                    t0=PipInstant.from_gpst_seconds(t0),
                    window=(
                        PipDuration.from_seconds(window[0]),
                        PipDuration.from_seconds(window[1]),
                    ),
                )
            else:
                self.start(
                    (
                        PipDuration.from_seconds(window[0]),
                        PipDuration.from_seconds(window[1]),
                    )
                )

            if t_cursors is not None:
                self.set_t_cursor_values(*t_cursors)

    ##########
    # WINDOW/RANGE/SPAN

    def get_window(self):
        """tuple of (xmin, xmax) values"""
        (xmin, xmax), (ymin, ymax) = self.primary_view.viewRange()
        return PipDuration.from_seconds(xmin), PipDuration.from_seconds(xmax)

    def get_range(self) -> Tuple[PipInstant, PipInstant]:
        """tuple of (start, end) times"""
        xmin, xmax = self.get_window()
        start = self.t0 + xmin
        end = self.t0 + xmax
        return start, end

    def get_span(self) -> PipDuration:
        """time span in seconds"""
        start, end = self.get_range()
        return abs(end - start)

    def _set_window(self, xmin: PipDuration, xmax: PipDuration):
        logger.debug("set window: {} {}".format(xmin, xmax))
        self.primary_view.setXRange(
            xmin.to_seconds(),
            xmax.to_seconds(),
            padding=0,
            update=False,
        )

    def set_window(self, xmin: PipDuration, xmax: PipDuration):
        """set xmin/xmax values"""
        self._set_window(xmin, xmax)
        self.update_entryWindow()

    def set_online_window(self, span: Optional[PipDuration] = None):
        """set the window for online, e.g. (-abs(span), 0)

        If span not specified use current span.
        """
        if not span:
            span = self.get_span()
        self.set_window(-abs(span), const.ONLINE_X_MAX)

    def preferred_trend(self) -> TrendType:
        """preferred trend for the current time span"""
        trend = TREND_OPTIONS[self.trendSelectGroup.checkedId()]

        if trend == "auto":
            span = self.get_span()
            if span > const.TREND_TRANS_THRESHOLD["sec/min"]:
                return TrendType.Minute
            elif span > const.TREND_TRANS_THRESHOLD["raw/sec"]:
                return TrendType.Second
            else:
                return TrendType.Raw
        elif trend == "min":
            return TrendType.Minute
        elif trend == "sec":
            return TrendType.Second
        elif trend == "raw":
            return TrendType.Raw
        else:
            msg = f"unrecognized trend type {trend}"
            raise ValueError(msg)

    ##########
    # UI

    def start(
        self,
        window: Union[Tuple[PipDuration, Optional[PipDuration]], None, bool] = None,
    ):
        """Start online mode"""
        logger.info("START")
        self.status_clear()
        if (
            window is not None
            and not isinstance(window, bool)
            and window[1] is not None
        ):
            w2: Tuple[PipDuration, PipDuration] = window
            span = abs(min(w2))
        else:
            span = self.get_span()
        self.set_online_window(span)
        trend = self.preferred_trend()
        # Sets the visibility of the curves in case the trend type has changed.
        # See the comment in `update_all_curves_visibility` for the reason this is needed.
        self.update_all_curves_visibility()
        self.last_cmd = ("start", {"window": window})
        self.data.online_start(trend, span)

    def stop(self):
        """Stop online mode"""
        logger.info("STOP")
        self.data.online_stop()
        # consider a stop as fetch for the stop range
        self.last_cmd = ("fetch", {"t0": self.t0, "window": self.get_window()})

    def _data_request(self, force=False, snapshot=False, singleshot=False):
        """
        :param force: force an request even if no relevant changes are detected.
        :param snapshot: Make a request directly from the cache without querying any
        data sources.
        :param singleshot: Make a request that automatically closes when there's no more
        available data.
        """
        ltrend, lstart, lend = self.last_request
        trend = self.preferred_trend()

        # Sets the visibility of the curves in case the trend type has changed.
        # See the comment in `update_all_curves_visibility` for the reason this is needed.
        self.update_all_curves_visibility()
        start, end = self.get_range()
        if not force and trend == ltrend and start == lstart and end == lend:
            return

        self.last_request = (trend, start, end)
        # extend the range a bit so we don't have to fetch data on-screen for small moves
        if singleshot or snapshot:
            # no extra data needed for snapshots
            # extra data can also confuse export functions
            extend = PipDuration.from_sec(0)
        elif self.data.online:
            extend = PipDuration.from_sec(1)
        else:
            extend = (end - start) / 2

        self.data.request(
            trend, (start - extend, end + extend), force, snapshot, singleshot
        )

    def fetch(self, **kwargs):
        """Fetch data offline

        May specify `t0` and `window`, or `start` and `end`.

        """
        logger.info(f"FETCH: {kwargs}")
        self.data.online_stop()
        if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:  # type: ignore
            self.data.reset()
        if "t0" in kwargs:
            t0 = kwargs["t0"]
            window = kwargs["window"]
            start = t0 + window[0]
            end = t0 + window[1]
        else:
            start = kwargs["start"]
            end = kwargs["end"]
            t0 = max(start, end)
            window = (-abs(start - end), PipDuration.from_sec(0))
        self.triggerGroup.setChecked(False)

        t_cursors = self.get_t_cursor_values()
        if t_cursors is not None:
            t1, t2 = t_cursors
            diff_sec = (t0 - self.t0).to_seconds()
            t1 -= diff_sec
            t2 -= diff_sec
            self.set_t_cursor_values(t1, t2)

        self._set_t0(t0)
        self.set_window(window[0], window[1])
        self.last_cmd = ("fetch", {"t0": self.t0, "window": self.get_window()})
        self._data_request(force=True)

    def reset(self):
        """Reset to last fetch range"""
        logger.info(f"RESET: {self.last_cmd}")
        if not self.last_cmd[0]:
            return
        for plot in self.plots:
            plot.enableAutoRange(axis="y")  # type: ignore
        if self.last_cmd[0] == "start":
            self.start(**self.last_cmd[1])
        elif self.last_cmd[0] == "fetch":
            self.fetch(**self.last_cmd[1])

    def XRangeChanged_callback(self, *args):
        """update time range info on X range change

        includes both mouse pan/zoom, but also interal X range
        changes.

        """
        self.updateGPS()
        self.update_entryWindow()
        self.update_tlabel()
        self._data_request()

    def get_entryWindow(self) -> Optional[tuple[PipDuration, Optional[PipDuration]]]:
        try:
            window = (
                float(self.entryWindowStart.text()),
                float(self.entryWindowEnd.text()),
            )
        except ValueError:
            return
        return PipDuration.from_seconds(window[0]), PipDuration.from_seconds(window[1])

    def update_t0(self):
        self.update_entryT0GPS()
        try:
            t0 = PipInstant.from_gpst_seconds(float(self.entryT0GPS.text()))
            window = self.get_entryWindow()
        except ValueError:
            return
        if window is None:
            return
        self.fetch(t0=t0, window=window)

    def update_window(self):
        if self.data.online:
            window = self.get_entryWindow()
            if window is not None:
                # break it down to make the type system happy
                xmin, xmax = window
                if xmax is not None:
                    self._set_window(xmin, xmax)
                    self.last_cmd = ("start", {"window": window})
        else:
            self.update_t0()

    def update_range(self):
        self.update_entryStartGPS()
        self.update_entryEndGPS()
        try:
            start = PipInstant.from_gpst_seconds(float(self.entryStartGPS.text()))
            end = PipInstant.from_gpst_seconds(float(self.entryEndGPS.text()))
        except ValueError:
            return
        self.fetch(start=start, end=end)

    ##########

    # SLOT
    def _data_online_status(self, msg: str):
        if msg == "":
            self._data_online_done(msg)
        else:
            self._data_online_start(msg)

    def _data_stream_status(self, msg: str):
        if msg == "":
            self._data_retrieve_done((False, False))
        else:
            self._data_retrieve_start(msg)

    def _data_stream_error(self, msg: str):
        if msg == "":
            self.status_clear()
        else:
            self._data_retrieve_done((msg, True))

    def _data_online_start(self, msg: str):
        self._online_ui()
        if self.triggerGroup.isChecked():
            self._enable_trigger()
        self._disable_crosshair()
        self._set_time_axis_mode("relative")

    def _data_online_done(self, signal: str):
        if self.crosshairGroup.isChecked():
            self._enable_crosshair()
        self._reset_time_axis_mode()

    # SLOT
    def _data_retrieve_start(self, msg):
        self.status_message(msg, style="data", log=False)
        self.entryT0GPS.setEnabled(False)
        self.entryT0Greg.setEnabled(False)
        self.buttonT0Now.setEnabled(False)
        self.fetchButton1.setEnabled(False)
        self.fetchButton2.setEnabled(False)

    # SLOT
    def _data_retrieve_done(self, signal):
        if self.data.empty:
            self._base_ui()
        elif self.data.online:
            self._online_ui()
        else:
            self._offline_ui()
        error, active = signal
        if error:
            self.status_error(error)
            if "SASL authentication protocol" in error:
                self.auth_dialog()
            if "Requested data is on tape" in error:
                self.ontape_dialog()
        if active:
            return
        if not error and not self._error:
            self.status_clear()
        self.entryT0GPS.setEnabled(True)
        self.entryT0Greg.setEnabled(True)
        self.buttonT0Now.setEnabled(True)
        self.fetchButton1.setEnabled(True)
        self.fetchButton2.setEnabled(True)

    ##########
    # PLOTTING

    # SLOT

    def _update_plots(self, recv: str):
        logger.log(5, f"PLOT: {recv}")

        if recv == "clear":
            logger.log(5, "CLEAR")
            for plot in self.plots:
                plot.clear_data()
            return

        with PrimedCache(self.data):
            if recv == "done":
                self.data.signal_view_done.emit(0)
                return

            data, online = self.data.get_data()
            if len(data) == 0:
                return

            # if this isn't the trend we need then drop the packet
            trend = data.trend
            preferred_trend = self.preferred_trend()
            if trend != preferred_trend:
                logger.debug(f"DROP {trend} trend packet ({preferred_trend} preferred)")
                return

            if data is not None:
                self.last_data = (trend,) + data.range
            else:
                self.last_data = (trend, None, None)

            trigger = None

            if data is not None:
                if online:
                    # if we're online, check for triggers
                    if self.trigger.active:
                        trigger = self.trigger.check(self.plot0, data)
                        if trigger:
                            self._update_triggerTime(trigger)
                            self._set_t0(trigger)

                    else:
                        try:
                            self._set_t0(data.real_range[1])
                        except ValueError:
                            logging.warning(
                                "An empty data buffer does not have a range"
                            )

                if (
                    online
                    and self.trigger.active
                    and not trigger
                    and (data.range[1] - self.t0 > self.t0 - data.range[0])
                ):
                    # don't update the plot if there was no trigger
                    pass
                else:
                    for plot in self.plots:
                        plot.update(data, self.t0)

            if (
                trigger
                and self.trigger.single
                and (data.range[1] - self.t0 > self.t0 - data.range[0])
            ):
                # reset single trigger so it'll trigger again if online is started
                self.trigger.set_single(True)
                self.stop()
            # objgraph.show_growth()
            self._plots_updated.emit()

    def update_tlabel(self):
        # span = self.get_span()
        # mod = ''
        # try:
        #     prec = int(np.round(np.log10(span))) - 2
        # except OverflowError:
        #     span = 2.385e-07
        #     prec = -9
        #     mod = '<'
        # sstr = '{mod}{span}'.format(
        #     mod=mod,
        #     span=util.seconds_time_str(span, prec),
        # )
        self.referenceTimeLabel.setText(
            #'t0 = {greg} [{gps:0.4f}], {span} span'.format(
            "t0 = {greg} [{gps:0.4f}]".format(
                greg=util.gpstime_str_greg(
                    util.gpstime_parse(self.t0.to_gpst_seconds()),
                    fmt=const.DATETIME_FMT,
                ),
                gps=self.t0.to_gpst_seconds(),
                # span=sstr,
            )
        )

    def _set_t0(self, t0: PipInstant):
        dt = self.t0 - t0
        self.t0 = t0
        logger.log(5, f"t0 = {t0}")
        self.update_tlabel()
        self.updateGPS()
        self.crosshair.update_t(dt.to_seconds())
        self.data.set_t0(t0)

    def reset_t0(self):
        start, end = self.get_range()
        t0 = start + (end - start) / 2
        xd = (end - start) / 2
        self.fetch(t0=t0, window=(-xd, xd))

    # SLOT used when reseting t0
    def reset_t0_relative(self, val_sec: float):
        if self.data.online:
            return
        val = PipDuration.from_seconds(val_sec)
        start, end = self.get_window()
        t0 = self.t0 + val
        start -= val
        end -= val
        self.fetch(t0=t0, window=(start, end))
        # t_cursors = self.get_t_cursor_values()
        # if t_cursors:
        #     t1, t2 = t_cursors
        #     t1 -= val_sec
        #     t2 -= val_sec
        #     self.set_t_cursor_values(t1, t2)

    ##########
    # TIMES

    def updateGPS(self):
        start, end = self.get_range()
        self.set_entryT0(self.t0.to_gpst_seconds())
        self.set_entryStart(start)
        self.set_entryEnd(end)

    def set_entryT0(self, time=None):
        if time:
            gt = util.gpstime_parse(time)
        else:
            gt = util.gpstime_parse("now")
        self.entryT0GPS.setText(util.gpstime_str_gps(gt))
        self.entryT0Greg.setText(util.gpstime_str_greg(gt))

    def update_entryT0GPS(self):
        gt = util.gpstime_parse(self.entryT0Greg.text())
        if not gt:
            return
        self.entryT0GPS.setText(util.gpstime_str_gps(gt))

    def update_entryT0Greg(self):
        gt = util.gpstime_parse(self.entryT0GPS.text())
        if not gt:
            return
        self.entryT0Greg.setText(util.gpstime_str_greg(gt))

    def update_entryWindow(self):
        xmin, xmax = self.get_window()
        self.entryWindowStart.setText(f"{xmin.to_seconds():.6f}")
        self.entryWindowEnd.setText(f"{xmax.to_seconds():.6f}")

    def set_entryStart(self, time: PipInstant):
        gt = util.gpstime_parse(time.to_gpst_seconds())
        self.entryStartGPS.setText(util.gpstime_str_gps(gt))
        self.entryStartGreg.setText(util.gpstime_str_greg(gt))

    def set_entryEnd(self, time: Optional[PipInstant] = None):
        if time:
            gt = util.gpstime_parse(time.to_gpst_seconds())
        else:
            gt = util.gpstime_parse("now")
        self.entryEndGPS.setText(util.gpstime_str_gps(gt))
        self.entryEndGreg.setText(util.gpstime_str_greg(gt))

    def update_entryStartGPS(self):
        t = self.entryStartGreg.text()
        gt = util.gpstime_parse(t)
        if not gt:
            return
        self.entryStartGPS.setText(util.gpstime_str_gps(gt))

    def update_entryStartGreg(self):
        t = self.entryStartGPS.text()
        gt = util.gpstime_parse(t)
        if not gt:
            return
        self.entryStartGreg.setText(util.gpstime_str_greg(gt))

    def update_entryEndGPS(self):
        t = self.entryEndGreg.text()
        gt = util.gpstime_parse(t)
        if not gt:
            return
        self.entryEndGPS.setText(util.gpstime_str_gps(gt))

    def update_entryEndGreg(self):
        t = self.entryEndGPS.text()
        gt = util.gpstime_parse(t)
        if not gt:
            return
        self.entryEndGreg.setText(util.gpstime_str_greg(gt))

    ##########
    # TREND

    def _trend_select(self, button):
        trend = TREND_OPTIONS[self.trendSelectGroup.checkedId()]
        logger.debug(f"trend select: {trend}")
        if button == self.trendAutoSelect:
            self.trendThreshGroup.setEnabled(True)
        else:
            self.trendThreshGroup.setEnabled(False)
        self._data_request()
        self.update_all_curves_visibility()

    def _set_trend_rawsec(self, *args):
        const.TREND_TRANS_THRESHOLD["raw/sec"] = PipDuration.from_sec(
            int(self.trendRawSecThresh.text())
        )

    def _set_trend_secmin(self, *args):
        const.TREND_TRANS_THRESHOLD["sec/min"] = PipDuration.from_sec(
            int(self.trendSecMinThresh.text())
        )

    def set_all_mean_curves_visibility(self, visible: bool):
        for plot in self.plots:
            plot.set_all_mean_curves_visibility(visible)

    def set_all_min_curves_visibility(self, visible):
        for plot in self.plots:
            plot.set_all_min_curves_visibility(visible)

    def set_all_max_curves_visibility(self, visible):
        for plot in self.plots:
            plot.set_all_max_curves_visibility(visible)

    def set_all_rms_curves_visibility(self, visible):
        for plot in self.plots:
            plot.set_all_rms_curves_visibility(visible)

    def update_all_curves_visibility(self):
        # This check for the preferred trend
        # is necessary because both the 'raw' PlotDataItem
        # and the 'mean' PlotDataItem are indexed by the same
        # key ('y') in the `curves` dictionary in the
        # NDScopePlotChannel class.
        if self.preferred_trend() == TrendType.Raw:
            self.set_all_mean_curves_visibility(True)
            self.set_all_min_curves_visibility(False)
            self.set_all_max_curves_visibility(False)
            self.set_all_rms_curves_visibility(False)
        elif self.preferred_trend() in [TrendType.Second, TrendType.Minute]:
            logger.debug("setting visibility")
            self.set_all_mean_curves_visibility(self.trendMeanVisibility.isChecked())
            self.set_all_min_curves_visibility(self.trendMinVisibility.isChecked())
            self.set_all_max_curves_visibility(self.trendMaxVisibility.isChecked())
            self.set_all_rms_curves_visibility(self.trendRmsVisibility.isChecked())

    def trend_mean_visibility_state_changed_slot(self, state):
        if self.preferred_trend() in [TrendType.Minute, TrendType.Second]:
            self.set_all_mean_curves_visibility(state)

    def trend_min_visibility_state_changed_slot(self, state):
        if self.preferred_trend() in [TrendType.Minute, TrendType.Second]:
            self.set_all_min_curves_visibility(state)

    def trend_max_visibility_state_changed_slot(self, state):
        if self.preferred_trend() in [TrendType.Minute, TrendType.Second]:
            self.set_all_max_curves_visibility(state)

    def trend_rms_visibility_state_changed_slot(self, state):
        if self.preferred_trend() in [TrendType.Minute, TrendType.Second]:
            self.set_all_rms_curves_visibility(state)

    ##########
    # AXIS

    @property
    def active_time_axis_mode(self):
        return self.plot0.axes["bottom"]["item"].mode

    def _set_time_axis_mode(self, mode):
        """set time axis mode, base method"""
        if isinstance(mode, QtWidgets.QRadioButton):
            mode = mode.text()
        logger.debug(f"time axis mode: {mode}")
        for plot in self.plots:
            if plot.axes is not None:
                plot.axes["bottom"]["item"].setTickStringsMode(mode)
        if mode == "relative":
            self.referenceTimeLabel.show()
        else:
            self.referenceTimeLabel.hide()

    def set_time_axis_mode(self, mode):
        """set the mode of the time (X) axis

        relative, or absolute GPS/UTC/local

        """
        if mode == "relative":
            self.timeAxisRelativeSelect.click()
        elif mode == "absolute GPS":
            self.timeAxisGPSSelect.click()
        elif mode == "absolute UTC":
            self.timeAxisUTCSelect.click()
        elif mode == "absolute local":
            self.timeAxisLocalSelect.click()
        else:
            raise ValueError(f"Unknown time axis mode '{mode}'.")

    def _reset_time_axis_mode(self):
        mode = self.timeAxisModeButtonGroup.checkedButton().text()
        if self.active_time_axis_mode == mode:
            return
        self._set_time_axis_mode(mode)

    ##########
    # TRIGGER

    def set_trigger_channel(self, channel: Optional[str]):
        """set the trigger channel"""
        assert channel in self.channels_as_names().union({None})
        if channel == self.trigger.channel_name:
            return
        if self.trigger.channel_name is not None:
            tplot = self.plots4chan(self.trigger.channel_name)[0]
        else:
            tplot = None
        if channel is not None:
            nplot = self.plots4chan(channel)[0]
            self.trigger.set_color(nplot.channels[channel].get_QColor())
        else:
            nplot = None
        self.trigger.set_channel(channel)
        if nplot != tplot:
            if tplot:
                tplot.removeItem(self.trigger.line)
            if nplot:
                nplot.addItem(self.trigger.line, ignoreBounds=True)
                nplot.disableAutoRange(axis="y")
            self.trigger.plot = nplot
        self.reset_trigger_level()

    def _update_trigger_channel(self):
        """update trigger channel from menu select"""
        chan = str(self.triggerSelect.currentText())
        self.set_trigger_channel(chan)
        logger.info("trigger set: {}".format(chan))

    def _update_triggerSelect(self):
        """update the trigger channel select menu"""
        try:
            self.triggerSelect.currentIndexChanged.disconnect(
                self._update_trigger_channel
            )
        except TypeError:
            pass
        self.triggerSelect.clear()
        self.triggerSelect.addItems(self.channels_as_names())
        self.triggerSelect.currentIndexChanged.connect(self._update_trigger_channel)

    def set_trigger_level(self, level):
        """set trigger level"""
        self.trigger.set_level(level)

    def _update_triggerLevel(self):
        """update trigger level text entry on mouse level change"""
        self.triggerLevel.setText("{:g}".format(self.trigger.level))

    def _set_trigger_level(self):
        """set the trigger level from text entry return press"""
        value = float(self.triggerLevel.text())
        self.set_trigger_level(value)

    def reset_trigger_level(self):
        """reset the trigger level to the midpoint of the range"""
        data = self.data.peak_data()
        value = self.trigger.guess_trigger_level(self.plot0, data)
        self.set_trigger_level(value)

    def _enable_trigger(self):
        """enable trigger, base method"""
        chan = str(self.triggerSelect.currentText())
        self.set_trigger_channel(chan)
        if not self.triggerLevel.text():
            self.reset_trigger_level()
        span = self.get_span()
        self.set_window(-span / 2, span / 2)
        logger.info("trigger enabled")

    def enable_trigger(self):
        """enable trigger"""
        if self.triggerGroup.isChecked():
            return
        self._enable_trigger()
        self.triggerGroup.setChecked(True)

    def _disable_trigger(self):
        """disable trigger, base method"""
        self.set_trigger_channel(None)
        self.set_online_window()
        logger.info("trigger disabled")

    def disable_trigger(self):
        """disable trigger"""
        if not self.triggerGroup.isChecked():
            return
        self.triggerGroup.setChecked(False)
        self._disable_trigger()

    def _toggle_trigger(self):
        """toggle trigger on/off"""
        if not self.trigger:
            return
        if self.triggerGroup.isChecked():
            self._enable_trigger()
        else:
            self._disable_trigger()

    def _update_triggerTime(self, time: PipInstant):
        """update trigger time label (from trigger)"""
        self.triggerTime.setText("{:14.6f}".format(time.to_gpst_seconds()))

    ##########
    # CROSSHAIR

    def _connect_crosshair(self):
        """connect the crosshair update signal handler"""
        self._crosshair_proxy = pg.SignalProxy(
            self.graphView.scene().sigMouseMoved,
            rateLimit=20,
            slot=self._update_crosshair,
        )

    def _enable_crosshair(self):
        """enable crosshair, base method"""
        self._connect_crosshair()
        self.graphView.scene().sigMouseClicked.connect(self._clicked_crosshair)
        self.graphView.setCursor(Qt.CrossCursor)  # type: ignore
        logger.info("crosshair enabled")

    def enable_crosshair(self):
        """enable crosshair"""
        if self.crosshairGroup.isChecked():
            return
        self._enable_crosshair()
        self.crosshairGroup.setChecked(True)

    def _disable_crosshair(self):
        """disable crosshair, base method"""
        self.crosshair.set_active_plot(None)
        self._crosshair_proxy = None
        try:
            self.graphView.scene().sigMouseClicked.disconnect(self._clicked_crosshair)
        except TypeError:
            pass
        self.graphView.setCursor(Qt.ArrowCursor)  # type: ignore
        self.crosshairGPS.setText("")
        self.crosshairUTC.setText("")
        self.crosshairLocal.setText("")
        self.crosshairYValue.setText("")
        logger.info("crosshair disabled")

    def disable_crosshair(self):
        """disable crosshair"""
        if not self.crosshairGroup.isChecked():
            return
        self.crosshairGroup.setChecked(False)
        self._disable_crosshair()

    def _toggle_crosshair(self):
        """toggle crosshair on/off"""
        if self.crosshairGroup.isChecked():
            self._enable_crosshair()
        else:
            self._disable_crosshair()

    def _update_crosshair(self, event):
        """update crosshair on mouse move"""
        # using signal proxy unfortunately turns the original
        # arguments into a tuple pos = event
        pos = event[0]
        for plot in self.plots:
            if plot.sceneBoundingRect().contains(pos):
                self.crosshair.update(plot, pos, self.t0.to_gpst_seconds())
                break

    def _update_crosshair_entry(self, recv):
        t, utc, local, y = recv
        self.crosshairGPS.setText(str(t))
        self.crosshairUTC.setText(utc)
        self.crosshairLocal.setText(local)
        self.crosshairYValue.setText(str(y))

    def _clicked_crosshair(self, event):
        """drop crosshair on click, pickup on click"""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._crosshair_proxy is None:
            self._connect_crosshair()
        else:
            self._crosshair_proxy = None

    ##########
    # CURSORS

    def _t_cursors_enable(self, val):
        assert isinstance(val, bool), val
        for plot in self.plots:
            plot.enable_t_cursors().set_visible(C1=val, C2=val)

    def _update_t_cursor(self, indval):
        index, value = indval
        for plot in self.plots:
            plot.t_cursors.set_values(**{index: value})

    def get_t_cursor_values(self):
        return self.plot0.t_cursors.get_values()

    def set_t_cursor_values(self, t1=None, t2=None):
        self.plot0.enable_t_cursors().set_values(t1, t2)

    def load_t_cursors(self, cursors):
        self.plot0.enable_t_cursors().load(cursors)

    ##########
    # STYLE

    def font_select_dialog(self):
        font, ok = QFontDialog.getFont(self.font())
        if ok:
            self.set_font(font)

    ##########
    # EXPORT

    def get_template(self):
        """Return the scope template as a dictionary"""
        template = {
            # convert to float from numpy.float64
            "t0": self.t0.to_gpst_seconds(),
            "time-window": list(map(PipDuration.to_seconds, self.get_window())),
            "color-mode": self._color_mode,
            "window-title": self.windowTitle().replace("ndscope: ", ""),
            "font-size": self.font().pointSize(),
            "grid-alpha": self.gridAlphaSelect.value(),
        }
        plots = []
        for plot, cells in self.plotLayout.items.items():
            plot_item = {}
            plot_item["channels"] = {}
            for name, chan in plot.channels.items():
                params = copy.deepcopy(chan.params)
                plot_item["channels"][name] = params
            tabspec = util.cells_to_tabspec(cells)
            plot_item.update(tabspec)
            if any(plot.vb.state["autoRange"]):
                plot_item["y-range"] = "auto"
            else:
                # convert to float from numpy.float64
                plot_item["y-range"] = [
                    plot.y_pos_to_val(v) for v in (map(float, plot.vb.viewRange()[1]))
                ]
            if plot.log_mode:
                plot_item["log-scale"] = True
            if plot.t_cursors.are_visible():
                plot_item["t-cursors"] = plot.t_cursors.export()
            if plot.y_cursors.are_visible():
                plot_item["y-cursors"] = plot.y_cursors.export()
            plots.append(plot_item)

        template["time-axis-mode"] = self.timeAxisModeButtonGroup.checkedButton().text()

        template["plots"] = plots
        return template

    def _export_dialog(self):
        """export save file dialog"""
        path = export.export_dialog(
            QFileDialog.getSaveFileName,
            self,
            self.exportPath.text(),
        )
        if not path:
            return
        self.exportPath.setText(path)
        return path

    def get_current_data_block(self) -> Optional[DataBufferDict]:
        """
        Fetch entire current data block from cache.
        """
        # temporary delink update plots so it doesn't read any data
        self.data.signal_data.disconnect(self._update_plots)

        data_block = None

        cache = self.data

        def _handle_data_block(cmd):
            nonlocal data_block, cache
            with PrimedCache(cache):
                if cmd == "done":
                    data_block, _ = cache.get_data()

        self.data.signal_data.connect(_handle_data_block, Qt.QueuedConnection)

        # fire of the view again
        self._data_request(force=True, snapshot=True)

        # wait for data by processing messages, with timeout
        while data_block is None:
            QApplication.processEvents()

        # reconnect _update_plots
        self.data.signal_data.disconnect(_handle_data_block)
        self.data.signal_data.connect(self._update_plots, Qt.QueuedConnection)

        return data_block

    def export(self, path=None):
        """Export plot scene, data, or template to file.

        Supports PNG, SVG, PDF image formats, HDF5 for data, and YAML
        for template.  A file select dialog will be presented if a
        path is not supplied.

        """
        if not path:
            path = self._export_dialog()
            if not path:
                return
        if not path or os.path.isdir(path):
            self.status_error("Must specify file path.")
            return
        ext = os.path.splitext(path)[1]
        if ext in [None, ""]:
            self.status_error("Must specify export file extension.")
            return
        self.status_message(f"Writing file {path}...", timeout=10)

        QApplication.processEvents()

        if ext in export.IMAGE_EXPORT_FUNCTIONS:
            obj = "scene"
            export_func = export.IMAGE_EXPORT_FUNCTIONS[ext]
            args = (
                self.graphView.scene(),
                path,
            )
            kwargs = dict()

        elif ext in export.DATA_EXPORT_FUNCS:
            obj = "data"
            data_block = self.get_current_data_block()
            window = self.get_window()
            start = self.t0 + window[0]
            end = self.t0 + window[1]
            args = (data_block, path, start, end)
            export_func = export.DATA_EXPORT_FUNCS[ext]
            kwargs = {
                "t0": self.t0.to_gpst_seconds(),
                "window": (window[0].to_seconds(), window[1].to_seconds()),
            }

        elif ext in export.TEMPLATE_EXPORT_FUNCTIONS:
            obj = "template"
            export_func = export.TEMPLATE_EXPORT_FUNCTIONS[ext]
            args = (
                self.get_template(),
                path,
            )
            kwargs = dict()

        else:
            self.status_error(f"Unsupported export file extension: {ext}")
            return

        try:
            export_func(*args, **kwargs)
        except Exception as e:
            logger.info(traceback.format_exc())
            self.status_error(str(e))
            return

        ftype = ext[1:].upper()
        self.status_message(f"Exported {obj} to {ftype}: {path}", timeout=10)
        self._export_complete.emit()

    def _export_save_handler(self, path=None):
        path = self.exportPath.text()
        self.export(path)

    def _export_show_handler(self):
        path = self.exportPath.text()
        if not path or not os.path.exists(path):
            self.status_error("No path, or no file at path.  Export first.")
            return
        ext = os.path.splitext(path)[1]
        if ext in [".hdf5", ".h5"]:
            export.matplot_h5(path)
        else:
            try:
                subprocess.Popen(["xdg-open", path])
            except FileNotFoundError:
                self.status_error(
                    "xdg-open binary not found.  Please install 'xdg-utils' package."
                )
            # FIXME: catch open errors even though process backgrounded?

    def snapshot(self):
        """Take snapshot of scene (PNG) and copy to clipboard"""
        try:
            scene = self.graphView.scene()
            if os.getenv("XDG_SESSION_TYPE") == "wayland":
                image = export.export_scene_png(scene)
                subprocess.run(["wl-copy"], input=image)
            else:
                exporters.ImageExporter(scene).export(copy=True)
        except Exception as e:
            logger.info(traceback.format_exc())
            self.status_error(str(e))
            return
        self.status_message("Copied scene snapshot to clipboard (as png)", timeout=10)
