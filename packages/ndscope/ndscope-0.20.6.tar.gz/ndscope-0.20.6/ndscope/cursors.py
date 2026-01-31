# -*- coding: utf-8 -*-
from __future__ import division
from typing import Optional
from weakref import WeakSet, ref

import numpy as np
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtCore import Signal  # type: ignore
import pyqtgraph as pg

from . import util
from .const import COLOR_MODE, LABEL_ALPHA


def _calc_reset_values(r):
    return (
        (3 * r[0] + r[1]) / 4,
        (r[0] + 3 * r[1]) / 4,
    )


class Cursors(QtCore.QObject):
    """cursor base class"""

    cursor_moved = Signal("PyQt_PyObject")

    cursors: WeakSet["Cursors"] = WeakSet()

    def __init__(self, plot, axis, labels, label_anchors, diff_label_anchors):
        """initialize Cursor object"""
        super().__init__()
        self.plot = ref(plot)
        self.axis = axis
        angle = {
            "T": 90,
            "Y": 0,
        }[axis]
        pen = {
            "style": Qt.DashLine,  # type: ignore
            "width": 2,
        }
        label_opts = {
            "position": 0,
            "anchors": label_anchors,
            "fill": (0, 0, 0, LABEL_ALPHA),
        }
        # HACK:  to get type checking to work
        # because there are lots of static references to C1 and C2
        # Cursors should probably be dynamically created,
        # in which case the static names would need to be removed.
        self.C1: pg.InfiniteLine = None  # type: ignore
        self.C2: pg.InfiniteLine = None  # type: ignore
        for i, label in enumerate(labels, start=1):
            index = f"C{i}"
            line = pg.InfiniteLine(
                angle=angle,
                pen=pen,
                movable=True,
                label=label,
                labelOpts=label_opts,
            )
            line._index = index  # type: ignore
            line._name = label
            line.setZValue(1)
            line.sigPositionChanged.connect(self._cursor_moved_slot)
            setattr(self, index, line)
        self.diff = pg.InfiniteLine(
            angle=angle,
            pen=pg.mkPen(None),
            label="diff",
            labelOpts={
                "position": 1,
                "anchors": diff_label_anchors,
                "fill": (0, 0, 0, LABEL_ALPHA),
            },
        )
        self.c1_value = self.pos_to_val(self.C1.value())
        self.c2_value = self.pos_to_val(self.C2.value())
        self.diff.setZValue(1)
        self.set_visible(False, False)
        self.set_labels_visible(True)

        self.cursors.add(self)

    @property
    def _lines(self):
        """list of Cursor line objects"""
        return [self.C1, self.C2, self.diff]

    def set_font(self, font):
        """set text label font"""
        for line in self._lines:
            line.label.textItem.setFont(font)

    def set_color_mode(self, mode):
        """set color mode"""
        fg = COLOR_MODE[mode]["fg"]
        bg = COLOR_MODE[mode]["bg"]
        for line in self._lines:
            fill_color = bg.color()
            fill_color.setAlpha(LABEL_ALPHA)
            line.label.fill.setColor(fill_color)
            line.label.setColor(fg)
            line.pen.setColor(fg)

    def format_value(self, val):
        """format cursor label value"""
        return f"{val:g}"

    def format_diff_label(self, val):
        """format diff cursor label"""
        return "Δ{}={}".format(
            self.axis,
            self.format_value(val),
        )

    def _update_label(self, line):
        """update individual cursor line label"""
        if line == self.C1:
            value = self.c1_value
        elif line == self.C2:
            value = self.c2_value
        else:
            value = self.pos_to_val(line.value)
        label = "{}={}".format(
            line._name,
            self.format_value(value),
        )
        line.label.setText(label)

    def _update_labels(self):
        self._update_label(self.C1)
        self._update_label(self.C2)
        c1, c2 = self.get_values()
        pos1 = self.val_to_pos(c1)
        pos2 = self.val_to_pos(c2)
        if pos1 is not None and pos2 is not None:
            self.diff.setValue((pos1 + pos2) / 2)
            vdiff = np.abs(c2 - c1)
            # self.diff.label.setText(label)
            self.diff.label.setHtml(self.format_diff_label(vdiff))

    def _cursor_moved_slot(self, line):
        if line == self.C1:
            self.c1_value = self.pos_to_val(self.C1.value())
        elif line == self.C2:
            self.c2_value = self.pos_to_val(self.C2.value())
        self.cursor_moved.emit((line._index, line.value()))
        self._update_labels()

    def set_labels_visible(self, val=True):
        """set label visibility for both cursors

        Value should be True or False.

        """
        assert isinstance(val, bool), val
        self._labels_visible = val
        self.C1.label.setVisible(val)
        self.C2.label.setVisible(val)
        self.diff.label.setVisible(val)
        self._update_labels()

    def labels_are_visible(self):
        """return True if labels are visible"""
        return self._labels_visible

    def set_visible(self, C1=None, C2=None):
        """set cursor visibility

        Value should be True or False, or None to not change.

        """
        if C1 is not None:
            self.C1.setVisible(C1)
        if C2 is not None:
            self.C2.setVisible(C2)
        self.diff.setVisible(self.C1.isVisible() and self.C2.isVisible())

    def are_visible(self):
        """True if either cursor is visible"""
        return self.C1.isVisible() or self.C2.isVisible()

    def val_to_pos(self, val):
        """convert line value to position"""
        return val

    def pos_to_val(self, pos):
        """current line position to value"""
        return pos

    def get_values(self):
        """get cursor values as a tuple"""
        return (self.c1_value, self.c2_value)

    def set_values(self, C1=None, C2=None):
        """set cursor values

        Values should be floats.

        """
        if C1:
            self.c1_value = C1
            pos = self.val_to_pos(C1)
            if pos is not None:
                self.C1.setValue(pos)
                # self.set_visible(C1=True)
            else:
                self.set_visible(C1=False)
        if C2:
            self.c2_value = C2
            pos = self.val_to_pos(C2)
            if pos is not None:
                self.C2.setValue(pos)
                # self.set_visible(C2=True)
            else:
                self.set_visible(C2=False)

    @classmethod
    def _is_component_visible(cls, attrib: str, axis: int) -> Optional["Cursors"]:
        for cursor in cls.cursors:
            if axis == cursor.axis and cursor.__getattribute__(attrib).isVisible():
                return cursor
        return None

    def reset_if_invisible_everywhere(self):
        """
        Reset each individual cursor only if it isn't visible on any plot.
        Needed for the case where a cursor is being added to the plot
        we don't want to change the current position if it's already
        in use on another plot
        """
        plot = self.plot()
        if plot is not None:
            t, y = plot.viewRange()
            val = {
                "T": t,
                "Y": y,
            }[self.axis]
            c1_reset, c2_reset = _calc_reset_values(val)

            c1_source = self._is_component_visible("C1", self.axis)
            if c1_source is not None:
                c1_reset = c1_source.get_values()[0]
            c2_source = self._is_component_visible("C2", self.axis)
            if c2_source is not None:
                c2_reset = c2_source.get_values()[1]
            self.set_values(c1_reset, c2_reset)

    def reset_if_invisible(self):
        """Reset cursor position only if the cursor is invisibile,
        preservering the position otherwise
        """
        plot = self.plot()
        if plot is not None:
            t, y = plot.viewRange()
            val = {
                "T": t,
                "Y": y,
            }[self.axis]
            c1_reset, c2_reset = _calc_reset_values(val)
            if self.C1.isVisible():
                c1_reset = self.get_values()[0]
            if self.C2.isVisible():
                c2_reset = self.get_values()[1]
            self.set_values(c1_reset, c2_reset)

    def reset(self):
        """reset cursor values"""
        plot = self.plot()
        if plot is not None:
            t, y = plot.viewRange()
            val = {
                "T": t,
                "Y": y,
            }[self.axis]
            self.set_values(*_calc_reset_values(val))

    def redraw(self):
        """redraw the cursor lines

        Used when there are axis scale changes.

        """
        self.set_values(*self.get_values())

    def export(self):
        """export cursor state as dict

        Values will be None or absent if the cursor is not visible.
        Use load_values() to load generated dict.

        """
        cursors = {}
        if self.C1.isVisible():
            if self.C2.isVisible():
                cursors["values"] = (self.c1_value, self.c2_value)
            else:
                cursors["values"] = (self.c1_value,)
        elif self.C2.isVisible():
            cursors["values"] = (None, self.c2_value)
        cursors["labels"] = self.labels_are_visible()
        return cursors

    def load(self, cursors):
        """load cursor state from dict

        If the value tuple only includes one value, only C1 will be
        turned on, if the tuple includes two values, both C1 and C2
        will be turned on.

        """
        if isinstance(cursors, list):
            values = cursors
            labels = True
        elif isinstance(cursors, dict):
            values = cursors["values"]
            labels = cursors["labels"]
        else:
            raise ValueError(
                f"Cursor description must be list or dict, not {type(cursors)}."
            )
        assert isinstance(values, list)
        assert isinstance(labels, bool)
        c1 = None
        c2 = None
        if len(values) == 1:
            c1 = values[0]
        elif len(values) == 2:
            c1, c2 = values
        else:
            raise ValueError("Currently only two T cursors supported.")
        self.set_values(c1, c2)
        self.set_visible(c1 is not None, c2 is not None)
        self.set_labels_visible(labels)


class TCursors(Cursors):
    """T axis cursors"""

    def __init__(self, plot):
        super().__init__(
            plot,
            axis="T",
            labels=["T1", "T2"],
            label_anchors=[(0, 1), (1, 1)],
            diff_label_anchors=[(0.5, 0), (0.5, 0)],
        )

    def format_value(self, val):
        return util.TDStr(val)

    def format_diff_label(self, val):
        if val == 0:
            f = 0
        else:
            f = 1 / val
        return '<table><tr><td rowspan="2" valign="middle">ΔT=</td><td>{}</td></tr><tr><td>{:g} Hz</td></tr></table></nobr>'.format(
            self.format_value(val),
            f,
        )


class YCursors(Cursors):
    """Y axis cursors"""

    def __init__(self, plot):
        super().__init__(
            plot,
            axis="Y",
            labels=["Y1", "Y2"],
            label_anchors=[(0, 0), (0, 1)],
            diff_label_anchors=[(1, 0.5), (1, 0.5)],
        )

    def val_to_pos(self, val):
        plot = self.plot()
        if plot is not None:
            return plot.y_val_to_pos(val)
        return 0

    def pos_to_val(self, pos):
        plot = self.plot()
        if plot is not None:
            return plot.y_pos_to_val(pos)
        return 0
