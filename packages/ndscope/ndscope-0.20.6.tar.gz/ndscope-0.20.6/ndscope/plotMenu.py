import weakref
from contextlib import contextmanager

from qtpy import QtCore, QtGui, QtWidgets

from ._qt import load_ui
from .const import CHANNEL_REGEXP, CHANNEL_RE

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyqtgraph as pg
    from .plot import NDScopePlot


AxisCtrlTemplate, __ = load_ui("axisCtrlTemplate.ui")


class AxisCtrlMenuItem(QtWidgets.QMenu, AxisCtrlTemplate):
    def __init__(self, title, mainmenu):
        super().__init__(title, mainmenu)
        self.setupUi(self)
        self.minText.setValidator(QtGui.QDoubleValidator())
        self.maxText.setValidator(QtGui.QDoubleValidator())

    @property
    def _controls(self):
        return [
            self.manualRadio,
            self.minText,
            self.maxText,
            self.autoRadio,
            self.autoPercentSpin,
            self.logModeCheck,
        ]

    def blockSignals(self, b):
        for c in self._controls:
            c.blockSignals(b)
        # returning bool to keep same return type as overridden function
        return False

    @contextmanager
    def signal_blocker(self):
        self.blockSignals(True)
        try:
            yield
        finally:
            self.blockSignals(False)


class MouseModeMenuItem(QtWidgets.QMenu):
    def __init__(self, title, mainmenu):
        super().__init__(title, mainmenu)
        group = QtWidgets.QActionGroup(self)  # type: ignore
        self.pan = QtWidgets.QAction("pan/zoom", self)  # type: ignore
        self.rect_mode = QtWidgets.QAction("zoom box", self)  # type: ignore
        self.addAction(self.pan)
        self.addAction(self.rect_mode)  # type: ignore
        self.pan.setCheckable(True)
        self.rect_mode.setCheckable(True)  # type: ignore
        self.pan.setActionGroup(group)
        self.rect_mode.setActionGroup(group)  # type: ignore


class CursorWidget(QtWidgets.QWidget):
    def __init__(self, check1, check2):
        super().__init__()
        self._c1 = QtWidgets.QCheckBox(check1)
        self._c1.setToolTip(f"enable {check1} cursor")
        self._c2 = QtWidgets.QCheckBox(check2)
        self._c2.setToolTip(f"enable {check2} cursor")
        self.labels = QtWidgets.QCheckBox("labels")
        self.labels.setToolTip("show cursor labels")
        self.labels.setChecked(True)
        setattr(self, check1, self._c1)
        setattr(self, check2, self._c2)
        self.reset = QtWidgets.QPushButton("reset")
        self.reset.setToolTip("reset cursor positions")
        self.layout = QtWidgets.QHBoxLayout()  # type: ignore
        self.layout.addWidget(self._c1)  # type: ignore
        self.layout.addWidget(self._c2)  # type: ignore
        self.layout.addWidget(self.labels)  # type: ignore
        self.layout.addWidget(self.reset)  # type: ignore
        self.layout.setContentsMargins(0, 5, 0, 5)  # type: ignore
        self.setLayout(self.layout)  # type: ignore


# this is lifted from the pqtgraph.ViewBoxMenu module
class NDScopePlotMenu(QtWidgets.QMenu):
    def __init__(self, plot: "NDScopePlot"):
        super().__init__()

        # keep weakref to view to avoid circular reference (don't know
        # why, but this prevents the ViewBox from being collected)
        self.plot = weakref.ref(plot)
        self.view: weakref.ReferenceType[pg.ViewBox] = weakref.ref(plot.getViewBox())  # type: ignore
        self.viewMap = weakref.WeakValueDictionary()

        loc = self.plot().loc  # type: ignore
        title = f"plot {loc}"
        self.setTitle(title)
        self.titleLabel = self.addLabel(title)
        self.addSeparator()

        self.viewAll = QtWidgets.QAction("view all data", self)  # type: ignore
        self.viewAll.triggered.connect(self.autoRange)
        self.addAction(self.viewAll)

        self.resetT0 = QtWidgets.QAction("reset t0 to point", self)  # type: ignore
        self.resetT0.triggered.connect(self.reset_t0)
        self.addAction(self.resetT0)

        self.yAxisUI = AxisCtrlMenuItem("Y axis scale", self)
        self.yAxisUI.manualRadio.clicked.connect(self.yManualClicked)
        self.yAxisUI.minText.editingFinished.connect(self.yRangeTextChanged)
        self.yAxisUI.maxText.editingFinished.connect(self.yRangeTextChanged)
        self.yAxisUI.autoRadio.clicked.connect(self.yAutoClicked)
        self.yAxisUI.autoPercentSpin.valueChanged.connect(self.yAutoSpinChanged)
        self.yAxisUI.logModeCheck.stateChanged.connect(self.yLogModeToggled)
        self.addMenu(self.yAxisUI)

        self.mouseModeUI = MouseModeMenuItem("mouse mode", self)
        self.mouseModeUI.pan.triggered.connect(self.setMouseModePan)
        self.mouseModeUI.rect_mode.triggered.connect(self.setMouseModeRect)  # type: ignore
        self.addMenu(self.mouseModeUI)

        self.addLabel()
        self.addSection("T cursors")

        self.t_cursor_widget = CursorWidget("T1", "T2")
        self.t_cursor_widget.T1.stateChanged.connect(self.update_t1_cursor)
        self.t_cursor_widget.T2.stateChanged.connect(self.update_t2_cursor)
        self.t_cursor_widget.labels.stateChanged.connect(self.update_t_cursor_labels)
        self.t_cursor_widget.reset.clicked.connect(self.reset_t_cursors)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(self.t_cursor_widget)
        self.addAction(action)

        row = self.addButtonRow()
        button = QtWidgets.QPushButton("enable all on all plots")
        button.clicked.connect(self.enable_all_t_cursors)
        row.addWidget(button)
        button = QtWidgets.QPushButton("disable all on all plots")
        button.clicked.connect(self.disable_all_t_cursors)
        row.addWidget(button)

        self.addLabel()
        self.addSection("Y cursors")

        self.y_cursor_widget = CursorWidget("Y1", "Y2")
        self.y_cursor_widget.Y1.stateChanged.connect(self.update_y1_cursor)
        self.y_cursor_widget.Y2.stateChanged.connect(self.update_y2_cursor)
        self.y_cursor_widget.labels.stateChanged.connect(self.update_y_cursor_labels)
        self.y_cursor_widget.reset.clicked.connect(self.reset_y_cursors)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(self.y_cursor_widget)
        self.addAction(action)

        self.addLabel()
        self.addSection("add/modify/remove channels")

        row = self.addButtonRow()
        self.addChannelEntry = QtWidgets.QLineEdit()
        self.addChannelEntry.setMinimumSize(300, 24)
        self.addChannelEntry.setPlaceholderText("enter channel to add to plot")
        self.addChannelEntry.setValidator(
            QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(CHANNEL_REGEXP))
        )
        self.addChannelEntry.textChanged.connect(self.validate_add)
        self.addChannelEntry.returnPressed.connect(self.add_channel)
        self.addChannelEntry.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter  # type: ignore
        )
        row.addWidget(self.addChannelEntry)
        self.addChannelButton = QtWidgets.QPushButton("add to plot")
        self.addChannelButton.setEnabled(False)
        self.addChannelButton.clicked.connect(self.add_channel)

        row.addWidget(self.addChannelButton)

        row = self.addButtonRow()
        button = QtWidgets.QPushButton("configure channels for plot")
        button.clicked.connect(self.channel_config_dialog)
        row.addWidget(button)

        row = self.addButtonRow()
        self.removeChannelList = QtWidgets.QComboBox()
        self.removeChannelList.setMinimumSize(200, 26)
        self.removeChannelList.currentIndexChanged.connect(self.remove_channel)
        # self.removeChannelList.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        row.addWidget(self.removeChannelList)

        self.addLabel()
        self.addSection("add/remove plots")

        row = self.addButtonRow()
        button = QtWidgets.QPushButton("add plot to column")
        button.clicked.connect(self.new_plot_col)
        row.addWidget(button)
        button = QtWidgets.QPushButton("add plot to row")
        button.clicked.connect(self.new_plot_row)
        row.addWidget(button)

        row = self.addButtonRow()
        button = QtWidgets.QPushButton("remove plot")
        button.clicked.connect(self.remove_plot)
        row.addWidget(button)

        self.setContentsMargins(10, 10, 10, 10)

        # self.clicked.connect(self._on_click)

        self.view().sigStateChanged.connect(self.viewStateChanged)  # type: ignore

    ##########

    # def mousePressEvent(self, a0):
    #     """Trap mouse events so popup doesn't close on any random click

    #     must click outside the menu to close
    #     """
    #     m = a0.position().toPoint()
    #     rect = self.rect()
    #     if not rect.contains(m):
    #         return super().mousePressEvent(a0)

    def set_title(self, pos=None):
        plot = self.plot()
        if plot is not None:
            loc = plot.loc
            title = f"plot {loc}"
            if pos:
                title += f" @ ({pos.x():g}, {pos.y():g})"
            self.setTitle(title)
            self.titleLabel.setText(title)

    def addLabel(self, label=""):
        ql = QtWidgets.QLabel()
        ql.setText(label)
        ql.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)  # type: ignore
        qla = QtWidgets.QWidgetAction(self)
        qla.setDefaultWidget(ql)
        self.addAction(qla)
        return ql

    def addButtonRow(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)
        widget.setLayout(layout)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(widget)
        # FIXME: this doesn't actually set the individual buttons to
        # be "actions" such that the close the context menu when
        # clicked
        self.addAction(action)
        return layout

    ##########

    def viewStateChanged(self):
        self.updateState()

    def updateState(self):
        # something about the viewbox has changed. update the axis
        # menu GUI

        view = self.view()
        if view is not None:
            state = view.getState(copy=False)

            # update the yAxisUI
            # block signals in the widget while we update the values
            plot = self.plot()
            if plot is not None:
                with self.yAxisUI.signal_blocker():
                    # index 1 in state is y axis
                    i = 1
                    tr = tuple(map(plot.y_pos_to_val, state["targetRange"][i]))
                    self.yAxisUI.minText.setText("%0.5g" % tr[0])
                    self.yAxisUI.maxText.setText("%0.5g" % tr[1])
                    if state["autoRange"][i] is not False:
                        self.yAxisUI.autoRadio.setChecked(True)
                        if state["autoRange"][i] is not True:
                            self.yAxisUI.autoPercentSpin.setValue(
                                int(state["autoRange"][i] * 100)
                            )
                    else:
                        self.yAxisUI.manualRadio.setChecked(True)
                    # logMode state not present before PyQTGraph version 0.12
                    if "logMode" in state:
                        self.yAxisUI.logModeCheck.setChecked(state["logMode"][i])

                if state["mouseMode"] == view.PanMode:
                    self.mouseModeUI.pan.setChecked(True)
                else:
                    self.mouseModeUI.rect_mode.setChecked(True)

                self.t_cursor_widget.T1.setChecked(plot.t_cursors.C1.isVisible())
                self.t_cursor_widget.T2.setChecked(plot.t_cursors.C2.isVisible())
                self.t_cursor_widget.labels.setChecked(
                    plot.t_cursors.labels_are_visible()
                )

                self.y_cursor_widget.Y1.setChecked(plot.y_cursors.C1.isVisible())
                self.y_cursor_widget.Y2.setChecked(plot.y_cursors.C2.isVisible())
                self.y_cursor_widget.labels.setChecked(
                    plot.y_cursors.labels_are_visible()
                )

    # HACK: QMenu popups are usually passed a global position.  for
    # this ViewBox menu we have reimplemented the
    # ViewBox.raiseContextMenu() method to send the MouseClickEvent
    # instead, so that we can extract both the screen and scene
    # positions.  The screen position is passed to the underlying
    # QMenu.popup(), while the scene position is mapped to the view
    # and cached so that it can be sent up to the Scope for certain
    # actions (e.g. reset t0)
    def popup(self, p, action=None):
        self.updateState()

        pos = p.screenPos().toPoint()
        view = self.view()
        if view is not None:
            # QPointF needed for QT 6
            self.view_pos = view.mapSceneToView(QtCore.QPointF(p.scenePos().toPoint()))

            self.set_title(self.view_pos)

            plot = self.plot()
            if plot is not None:
                if plot.data_cache.online:
                    self.resetT0.setEnabled(False)
                else:
                    self.resetT0.setEnabled(True)

                # update remove channels list
                self.update_channel_list()

                # see if there's a channel in the clipboard
                clipboard = QtWidgets.QApplication.clipboard().text(  # type: ignore
                    mode=QtGui.QClipboard.Selection  # type: ignore
                )
                clipboard = clipboard.strip()
                if CHANNEL_RE.match(clipboard):
                    # if we have a channel add it to the label
                    self.addChannelEntry.setText(clipboard)
                else:
                    self.addChannelEntry.setText("")

                self.removeChannelList.setEnabled(len(plot.channels) > 0)

                super().popup(pos)

    ##########

    def autoRange(self):
        # don't let signal call this directly--it'll add an unwanted argument
        view = self.view()
        if view is not None:
            view.autoRange()

    def reset_t0(self):
        plot = self.plot()
        if plot is not None:
            plot._reset_t0(self.view_pos.x())

    ##########

    def update_channel_list(self):
        plot = self.plot()
        if plot is not None:
            channels = list(plot.channels.keys())
            self.removeChannelList.currentIndexChanged.disconnect(self.remove_channel)
            self.removeChannelList.clear()
            ls = ["remove channel"] + channels
            self.removeChannelList.addItems(ls)
            self.removeChannelList.insertSeparator(1)
            self.removeChannelList.currentIndexChanged.connect(self.remove_channel)

    def validate_add(self):
        plot = self.plot()
        if plot is not None:
            channel = str(self.addChannelEntry.text())
            if CHANNEL_RE.match(channel):
                if channel in plot.channels:
                    self.addChannelEntry.setStyleSheet("background: #87b5ff;")
                    self.addChannelButton.setEnabled(False)
                else:
                    self.addChannelEntry.setStyleSheet(
                        "font-weight: bold; background: #90ff8c;"
                    )
                    self.addChannelButton.setEnabled(True)
            else:
                self.addChannelEntry.setStyleSheet("")
                self.addChannelButton.setEnabled(False)

    def channel_config_dialog(self):
        plot = self.plot()
        if plot is not None:
            plot.open_channel_config_dialog()
            self.close()

    def get_channel_from_entry(self):
        channel = str(self.addChannelEntry.text())
        if CHANNEL_RE.match(channel):
            return channel
        return None

    def add_channel(self):
        plot = self.plot()
        if plot is not None:
            channel = self.get_channel_from_entry()
            if channel is not None:
                plot.add_channels({channel: {}})
            self.close()

    def remove_channel(self, *args):
        self.removeChannelList.currentIndexChanged.disconnect(self.remove_channel)
        channel = str(self.removeChannelList.currentText())
        plot = self.plot()
        if plot is not None:
            plot.remove_channels([channel])
            self.removeChannelList.currentIndexChanged.connect(self.remove_channel)
            self.close()

    def new_plot_row(self):
        self.new_plot("row")

    def new_plot_col(self):
        self.new_plot("col")

    def new_plot(self, rowcol):
        channel = self.get_channel_from_entry()
        if channel is not None:
            chan = [{channel: None}]
        else:
            chan = []
        plot = self.plot()
        if plot is not None:
            plot.new_plot_request.emit(
                (self.plot(), rowcol, {"channels": chan}),
            )
            self.close()

    def remove_plot(self):
        plot = self.plot()
        if plot is not None:
            plot.remove_plot_request.emit(self.plot())
            self.close()

    ##########

    def setMouseModePan(self):
        view = self.view()
        if view is not None:
            view.setLeftButtonAction("pan")

    def setMouseModeRect(self):
        view = self.view()
        if view is not None:
            view.setLeftButtonAction("rect")

    def yMouseToggled(self, b):
        view = self.view()
        if view is not None:
            view.setMouseEnabled(y=b)

    def yManualClicked(self):
        view = self.view()
        if view is not None:
            view.enableAutoRange(view.YAxis, False)

    def yRangeTextChanged(self):
        plot = self.plot()
        if plot is not None:
            self.yAxisUI.manualRadio.setChecked(True)
            range_1 = float(self.yAxisUI.minText.text())
            range_2 = float(self.yAxisUI.maxText.text())
            plot.set_y_range((range_1, range_2))

    def yAutoClicked(self):
        view = self.view()
        if view is not None:
            val = self.yAxisUI.autoPercentSpin.value() * 0.01
            view.enableAutoRange(view.YAxis, val)

    def yAutoSpinChanged(self, val):
        view = self.view()
        if view is not None:
            self.yAxisUI.autoRadio.setChecked(True)
            view.enableAutoRange(view.YAxis, val * 0.01)

    def yAutoPanToggled(self, b):
        view = self.view()
        if view is not None:
            view.setAutoPan(y=b)

    def yVisibleOnlyToggled(self, b):
        view = self.view()
        if view is not None:
            view.setAutoVisible(y=b)

    def yInvertToggled(self, b):
        view = self.view()
        if view is not None:
            view.invertY(b)

    def yLogModeToggled(self, state):
        plot = self.plot()
        if plot is not None:
            plot.set_log_mode(bool(state))  # type: ignore

    def update_t1_cursor(self):
        plot = self.plot()
        if plot is not None:
            plot.enable_t_cursors().set_visible(
                C1=bool(self.t_cursor_widget.T1.isChecked()),
            )

    def update_t2_cursor(self):
        plot = self.plot()
        if plot is not None:
            plot.enable_t_cursors().set_visible(
                C2=bool(self.t_cursor_widget.T2.isChecked()),
            )

    def update_t_cursor_labels(self):
        plot = self.plot()
        if plot is not None:
            plot.t_cursors.set_labels_visible(
                bool(self.t_cursor_widget.labels.isChecked()),
            )

    def enable_all_t_cursors(self):
        plot = self.plot()
        if plot is not None:
            plot.t_cursors_enable.emit(True)
            self.close()

    def disable_all_t_cursors(self):
        plot = self.plot()
        if plot is not None:
            plot.t_cursors_enable.emit(False)
            self.close()

    def reset_t_cursors(self):
        plot = self.plot()
        if plot is not None:
            plot.t_cursors.reset()
            self.close()

    def update_y1_cursor(self):
        plot = self.plot()
        if plot is not None:
            plot.enable_y_cursors().set_visible(
                C1=bool(self.y_cursor_widget.Y1.isChecked()),
            )

    def update_y2_cursor(self):
        plot = self.plot()
        if plot is not None:
            plot.enable_y_cursors().set_visible(
                C2=bool(self.y_cursor_widget.Y2.isChecked()),
            )

    def update_y_cursor_labels(self):
        plot = self.plot()
        if plot is not None:
            plot.y_cursors.set_labels_visible(
                bool(self.y_cursor_widget.labels.isChecked()),
            )

    def reset_y_cursors(self):
        plot = self.plot()
        if plot is not None:
            plot.y_cursors.reset()
            self.close()
