import logging
import re
import fnmatch
import functools
import time
from queue import LifoQueue
from threading import Thread


from qtpy import QtGui, QtWidgets, QtCore
from qtpy.QtCore import Signal  # type: ignore

from ndscope.math_config import MathConfigDialog

from ._qt import load_ui
from .plot import NDScopePlotChannel

from typing import TYPE_CHECKING, Set, List

if TYPE_CHECKING:
    from .nds import Channel

logger = logging.getLogger("CHANNEL_SELECT")

# ------------------------------------------------------------------------------

COLOR_TESTPOINT = "blue"
COLOR_ONLINE = "green"


def brush_for_channel(channel):
    if channel.testpoint:
        return QtGui.QBrush(QtGui.QColor(COLOR_TESTPOINT))
    elif channel.online:
        return QtGui.QBrush(QtGui.QColor(COLOR_ONLINE))
    else:
        return QtGui.QBrush()


# ------------------------------------------------------------------------------


def is_slow(sample_rate):
    return sample_rate <= 16


def is_fast(sample_rate):
    return not is_slow(sample_rate)


# ------------------------------------------------------------------------------


def filter_channel(channel, show_slow, show_fast, show_online_only):
    if show_online_only and not channel.online:
        return False
    else:
        if show_slow and is_slow(channel.rate_hz):
            return True
        elif show_fast and is_fast(channel.rate_hz):
            return True
        else:
            return False


def char_to_case_insensitive(char: str) -> str:
    """return a single char in a case insensitive format

    does nothing to chars that aren't cased alphabetical
    """
    if char.isupper() or char.islower():
        return f"[{char.lower()}{char.upper()}]"
    return char


def case_insensitive_pattern(pattern: str) -> str:
    """
    Return a glob pattern suitable for fnmatch that's case insensitive
    """

    # states 0 = read, 1 = escape, 2 = in brackets, 3 = escape-in-brackets
    state = 0
    new_pattern = ""
    for c in pattern:
        if state == 0:
            # read
            if c == "\\":
                state = 1
                new_pattern += c
            elif c == "[":
                state = 2
                new_pattern += c
            else:
                new_pattern += char_to_case_insensitive(c)
        elif state == 1:
            new_pattern += c
            state = 0
        elif state == 3:
            new_pattern += c
            state = 2
        elif state == 2:
            if c == "]":
                state = 0
            elif c == "\\":
                state = 3
            else:
                state = 2
            new_pattern += c
        else:
            raise Exception(f"Unknown case-insensitive state {state}")
    return new_pattern


# ------------------------------------------------------------------------------


class AvailableChannelTreeItem:
    def __init__(self, parent=None, data=None, is_leaf=False):
        self.parent = parent
        self.data = data
        self.is_leaf = is_leaf
        if not is_leaf:
            self.branch_dict = {}
            self.leaf_dict = {}

            self.has_slow = False
            self.has_slow_online = False
            self.has_fast = False
            self.has_fast_online = False

    def child_list(self):
        if not self.is_leaf:
            return list(self.branch_dict.values()) + list(self.leaf_dict.values())
        return []

    def row(self):
        if self.parent:
            return self.parent.child_list().index(self)
        else:
            return 0


class AvailableChannelTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, channel_list, max_depth=4):
        super().__init__()
        self.header_role_data = {QtCore.Qt.DisplayRole: ("name", "rate")}  # type: ignore
        self.root = AvailableChannelTreeItem()
        self.max_depth = max_depth
        self.insert(channel_list)

    def insert(self, channel_list):
        # HACK: there's something weird about the matching of this
        # character set.  If the underscore is at the end of the set,
        # e.g. '[:-_]', then the matches are wrong.  Is this a bug in
        # python???
        split_re = re.compile(r"[_:-]")
        for channel in channel_list:
            current = self.root
            slow = is_slow(channel.rate_hz)
            online = channel.online
            name_part_list = split_re.split(channel.name, self.max_depth)
            for name_part in name_part_list[:-1]:
                if name_part not in current.branch_dict:
                    current.branch_dict[name_part] = AvailableChannelTreeItem(
                        current, name_part
                    )
                current = current.branch_dict[name_part]
                if slow:
                    current.has_slow = True
                    if online:
                        current.has_slow_online = True
                else:
                    current.has_fast = True
                    if online:
                        current.has_fast_online = True
            current.leaf_dict[channel.name] = AvailableChannelTreeItem(
                current, channel, is_leaf=True
            )

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.header_role_data[QtCore.Qt.DisplayRole])  # type: ignore

    def data(self, index, role=QtCore.Qt.DisplayRole):  # type: ignore
        if not index.isValid():
            return QtCore.QVariant()

        item = index.internalPointer()
        if item.is_leaf:
            channel = item.data
            brush = brush_for_channel(channel)
            sample_rate = f"{float(channel.rate_hz):g}"
            role_data = {
                QtCore.Qt.DisplayRole: (channel.name, sample_rate),  # type: ignore
                QtCore.Qt.ForegroundRole: (brush, brush),  # type: ignore
            }
        else:
            name_part = item.data
            role_data = {QtCore.Qt.DisplayRole: (name_part, "")}  # type: ignore

        try:
            return role_data[role][index.column()]
        except KeyError:
            return QtCore.QVariant()
        except IndexError:
            return QtCore.QVariant()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags  # type: ignore

        item = index.internalPointer()
        if item.is_leaf:
            flags = (
                QtCore.Qt.ItemIsEnabled  # type: ignore
                | QtCore.Qt.ItemIsSelectable  # type: ignore
                | QtCore.Qt.ItemIsDragEnabled  # type: ignore
                | QtCore.Qt.ItemNeverHasChildren,  # type: ignore
                QtCore.Qt.ItemIsEnabled,  # type: ignore
            )
        else:
            flags = (QtCore.Qt.ItemIsEnabled, QtCore.Qt.ItemIsEnabled)  # type: ignore

        try:
            return flags[index.column()]
        except IndexError:
            return QtCore.Qt.NoItemFlags  # type: ignore

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):  # type: ignore
        if orientation == QtCore.Qt.Horizontal:  # type: ignore
            try:
                return self.header_role_data[role][section]
            except KeyError:
                return QtCore.QVariant()
            except IndexError:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()

        try:
            child_item = parent_item.child_list()[row]
            return self.createIndex(row, column, child_item)
        except IndexError:
            return QtCore.QModelIndex()

    def mimeData(self, indexes):
        text_list = [
            self.data(index, QtCore.Qt.DisplayRole)  # type: ignore
            for index in indexes
            if index.isValid()
        ]
        text = "\n".join(text_list)
        mime_data = QtCore.QMimeData()
        mime_data.setText(text)
        return mime_data

    def mimeTypes(self):
        return ["text/plain"]

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent
        if parent_item == self.root:
            return QtCore.QModelIndex()

        row = parent_item.row()
        return self.createIndex(row, 0, parent_item)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()

        return len(parent_item.child_list())


# Filters the branch and leaf items based on the sample rate and online status
# of the channels that they contain.
class AvailableChannelTreeSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.show_slow = True
        self.show_fast = True
        self.show_online_only = False

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        item = index.internalPointer()
        if item.is_leaf:
            channel = item.data
            return filter_channel(
                channel, self.show_slow, self.show_fast, self.show_online_only
            )
        else:
            if self.show_online_only:
                if self.show_slow and item.has_slow_online:
                    return True
                elif self.show_fast and item.has_fast_online:
                    return True
                else:
                    return False
            else:
                if self.show_slow and item.has_slow:
                    return True
                elif self.show_fast and item.has_fast:
                    return True
                else:
                    return False


class AvailableChannelTreeView(QtWidgets.QTreeView):
    def __init__(self, parent):
        super().__init__(parent)


class AvailableChannelTableModel(QtCore.QAbstractTableModel):
    def __init__(
        self,
        channel_list: "List[Channel]",
        parent=None,
        index=False,
        headers=("name", "rate"),
    ):
        super().__init__(parent)
        self.search_pattern = ""
        self.show_slow = True
        self.show_fast = True
        self.show_online_only = False

        self.full_channel_list = channel_list
        self.filtered_channel_list = self.full_channel_list
        self.header_data = headers

        # holds filter search queries to be processed
        self.search_query_queue = LifoQueue()

        # this value increments for every search.  Results are only applied
        # to searches indexed >= search_index
        self.search_index = 0

        self.search_thread = Thread(target=self._search_thread, daemon=True)
        self.search_thread.start()

        # get some indexes for filter buttons
        self.fast_channels: Set[int] = set()
        self.online_channels: Set[int] = set()
        for i, channel in enumerate(channel_list):
            if channel.online:
                self.online_channels.add(i)
            if is_fast(channel.rate_hz):
                self.fast_channels.add(i)

        # Delimiter regular expression used for typed-in channel queries
        self.delimiter_re = re.compile(r"[- _]+")

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.header_data)

    def data(self, index, role):
        try:
            channel = self.itemFromIndex(index)
        except IndexError:
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:  # type: ignore
            return (channel.name, str(channel.rate_hz))[index.column()]
        elif role == QtCore.Qt.ForegroundRole:  # type: ignore
            return brush_for_channel(channel)
        else:
            return QtCore.QVariant()

    def get_channel_names(self):
        """return all selected channel names"""

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags  # type: ignore
        try:
            return (
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsSelectable  # type: ignore
                    | QtCore.Qt.ItemIsDragEnabled  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsSelectable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
            )[index.column()]
        except IndexError:
            return QtCore.Qt.NoItemFlags  # type: ignore

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:  # type: ignore
            return self.header_data[section]
        elif orientation == QtCore.Qt.Vertical:  # type: ignore
            return section + 1
        else:
            return QtCore.QVariant()

    def itemFromIndex(self, index):
        return self.filtered_channel_list[index.row()]

    def mimeData(self, indexes):
        text_list = [
            self.data(index, QtCore.Qt.DisplayRole)
            for index in indexes
            if index.isValid()
        ]
        text = "\n".join(text_list)
        mime_data = QtCore.QMimeData()
        mime_data.setText(text)
        return mime_data

    def mimeTypes(self):
        return ["text/plain"]

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.filtered_channel_list)

    def _update_filter(self, search_pattern: str):
        # FIXME: this is fairly slow, how can we speed this up?
        def _match(channel):
            return filter_channel(
                channel, self.show_slow, self.show_fast, self.show_online_only
            ) and (
                # self.search_pattern in channel.name \
                # or
                fnmatch.fnmatch(channel.name, "*" + search_pattern + "*")
            )

        search_pattern = case_insensitive_pattern(search_pattern)

        # allow user to enter space, _ , or - for either - and _
        search_pattern = self.delimiter_re.sub("[-_]", search_pattern)

        # make sure we can search anywhere in a channel name
        search_pattern = "*" + search_pattern + "*"

        # these yield time to other threads
        time.sleep(0)

        filtered_channels = set()
        n = 0
        for i, chan in enumerate(self.full_channel_list):
            if n % 1000 == 0:
                time.sleep(0)
            n += 1
            if fnmatch.fnmatch(chan.name, search_pattern):
                filtered_channels.add(i)

        time.sleep(0)

        # filter by radio buttons
        if not self.show_slow:
            filtered_channels &= self.fast_channels
        time.sleep(0)
        if not self.show_fast:
            filtered_channels -= self.fast_channels
        time.sleep(0)
        if self.show_online_only:
            filtered_channels &= self.online_channels
        time.sleep(0)

        filtered_channel_list = [
            c for i, c in enumerate(self.full_channel_list) if i in filtered_channels
        ]

        self.beginResetModel()
        self.filtered_channel_list = filtered_channel_list
        self.endResetModel()

    def _search_thread(self):
        next_index = 0

        while True:
            index, pattern = self.search_query_queue.get(block=True)
            if index < next_index:
                continue
            next_index = index + 1
            self._update_filter(pattern)

    def update_filter(self):
        self.search_query_queue.put((self.search_index, self.search_pattern))
        self.search_index += 1


class AvailableChannelTableView(QtWidgets.QTableView):
    def __init__(self, parent):
        super().__init__(parent)


class ChannelListWidget(*load_ui("channel_list.ui")):
    def __init__(
        self,
        available_channel_tree_model,
        available_channel_table_model,
        parent=None,
        alternate_text=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        if alternate_text is None:
            alternate_text = {}

        if "placeholder" in alternate_text:
            self.search_line_edit.setPlaceholderText(alternate_text["placeholder"])
        if "all_button" in alternate_text:
            self.all_radio_button.setText(alternate_text["all_button"])
        if "slow_button" in alternate_text:
            self.slow_radio_button.setText(alternate_text["slow_button"])
        if "fast_button" in alternate_text:
            self.fast_radio_button.setText(alternate_text["fast_button"])
        if "online_button" in alternate_text:
            self.online_radio_button.setText(alternate_text["online_button"])
        if "search_tab" in alternate_text:
            self.available_channel_list_tab.setTitle(alternate_text["search_tab"])
        if "tree_tab" in alternate_text:
            self.available_channel_tree_tab.setTitle(alternate_text["tree_tab"])

        # available channel tree model
        self.available_channel_tree_model = available_channel_tree_model
        self.available_channel_tree_proxy_model = (
            AvailableChannelTreeSortFilterProxyModel()
        )
        self.available_channel_tree_proxy_model.setSourceModel(
            self.available_channel_tree_model
        )

        # available channel tree view
        self.available_channel_tree_view.setModel(
            self.available_channel_tree_proxy_model
        )
        self.available_channel_tree_view.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.available_channel_tree_view.header().setSectionsMovable(False)
        self.available_channel_tree_view.setDragEnabled(True)
        self.available_channel_tree_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.available_channel_tree_view.doubleClicked.connect(
            self._tree_double_clicked
        )

        # available channel table model
        self.available_channel_table_model = available_channel_table_model

        # available channel table view
        self.available_channel_table_view.setModel(self.available_channel_table_model)
        self.available_channel_table_view.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        self.available_channel_table_view.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents
        )
        self.available_channel_table_view.horizontalHeader().setHighlightSections(False)
        self.available_channel_table_view.setDragEnabled(True)
        self.available_channel_table_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.available_channel_table_view.setWordWrap(False)
        self.available_channel_table_view.doubleClicked.connect(self._double_clicked)

        self.all_radio_button.toggled.connect(self.all_radio_button_toggled_slot)
        self.slow_radio_button.toggled.connect(self.slow_radio_button_toggled_slot)
        self.fast_radio_button.toggled.connect(self.fast_radio_button_toggled_slot)

        self.online_checkbox.setStyleSheet("color: {0}".format(COLOR_ONLINE))
        self.online_checkbox.stateChanged.connect(
            self.online_checkbox_state_changed_slot
        )

        self.search_line_edit.textChanged.connect(
            self.search_line_edit_text_changed_slot
        )
        self.search_line_edit.setClearButtonEnabled(True)

        self.selected_table_indices = set()
        self.selected_tree_indices = set()

        # FIXME: this is a substitute (possibly) for logic that should
        # maybe be based on whether we're talking to an NDS1 or NDS2
        # server.  for NDS1 everything is online, and there are
        # testpoints (which are also online only), so a checkbox to
        # filter on online is superfulous.
        all_online = functools.reduce(
            lambda value, chan: value and chan.online,
            self.available_channel_table_model.full_channel_list,
            True,
        )
        if all_online:
            self.online_checkbox.hide()
            # FIXME: this should be based on the presence of test points
            self.legendLabel.setText(
                f"<span style='color: {COLOR_TESTPOINT}'>testpoints in blue</span>"
            )
        else:
            self.legendLabel.hide()

    def showEvent(self, a0):
        # grab keyboard focus
        self.search_line_edit.setFocus()

        # don't clear the selection.  with selection model now ExtendedSelection
        # manual clearing is fairly natural
        # and preserving selection might be useful
        # self.available_channel_table_view.selectionModel().clearSelection()

        super().showEvent(a0)

    def set_server_info(self, server, nchannels, glob=None):
        text = f"server: <span style='font-weight: bold'>{server}</span>"
        text += f" [{nchannels} channels]"
        if glob and glob != "*":
            text += f" (channel glob: '{glob}')"
        self.title.setText(text)

    def search_line_edit_text_changed_slot(self, text):
        self.available_channel_table_model.search_pattern = text
        self.available_channel_table_model.update_filter()

    def all_radio_button_toggled_slot(self, checked):
        if checked:
            self.available_channel_tree_proxy_model.show_slow = True
            self.available_channel_tree_proxy_model.show_fast = True
            self.available_channel_tree_proxy_model.invalidateFilter()

            self.available_channel_table_model.show_slow = True
            self.available_channel_table_model.show_fast = True
            self.available_channel_table_model.update_filter()

    def slow_radio_button_toggled_slot(self, checked):
        if checked:
            self.available_channel_tree_proxy_model.show_slow = True
            self.available_channel_tree_proxy_model.show_fast = False
            self.available_channel_tree_proxy_model.invalidateFilter()

            self.available_channel_table_model.show_slow = True
            self.available_channel_table_model.show_fast = False
            self.available_channel_table_model.update_filter()

    def fast_radio_button_toggled_slot(self, checked):
        if checked:
            self.available_channel_tree_proxy_model.show_slow = False
            self.available_channel_tree_proxy_model.show_fast = True
            self.available_channel_tree_proxy_model.invalidateFilter()

            self.available_channel_table_model.show_slow = False
            self.available_channel_table_model.show_fast = True
            self.available_channel_table_model.update_filter()

    def online_checkbox_state_changed_slot(self, state):
        if not state:
            self.available_channel_tree_proxy_model.show_online_only = False
            self.available_channel_tree_proxy_model.invalidateFilter()

            self.available_channel_table_model.show_online_only = False
            self.available_channel_table_model.update_filter()
        else:
            self.available_channel_tree_proxy_model.show_online_only = True
            self.available_channel_tree_proxy_model.invalidateFilter()

            self.available_channel_table_model.show_online_only = True
            self.available_channel_table_model.update_filter()

    def _double_clicked(self, index):
        self.selected_table_indices = set(
            self.available_channel_table_view.selectedIndexes()
        )
        self.selected_table_indices.add(index)
        self.parent().accept()

    def _tree_double_clicked(self, index):
        has_children = self.available_channel_tree_proxy_model.hasChildren(index)
        if not has_children:
            self.selected_tree_indices = set(
                self.available_channel_tree_view.selectedIndexes()
            )
            self.selected_tree_indices.add(index)
            self.parent().accept()

    def get_channel_names(self) -> List[str]:
        """return a list of the names of all selected channels"""
        table_chan_names = [
            self.available_channel_table_model.data(i, QtCore.Qt.DisplayRole)  # type: ignore
            for i in self.selected_table_indices
        ]
        tree_chan_names = [
            self.available_channel_tree_proxy_model.data(i, QtCore.Qt.DisplayRole)  # type: ignore
            for i in self.selected_tree_indices
        ]
        return table_chan_names + tree_chan_names


# ------------------------------------------------------------------------------


class PushButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        button = QtWidgets.QStyleOptionButton()
        button.text = "-"
        button.rect = option.rect
        button.rect.setWidth(min(option.rect.width(), 30))
        button.state = QtWidgets.QStyle.State_Enabled  # type: ignore
        QtWidgets.QApplication.style().drawControl(  # type: ignore
            QtWidgets.QStyle.CE_PushButton,
            button,
            painter,  # type: ignore
        )


class ConfigChannelTableModel(QtCore.QAbstractTableModel):
    # items in table are NDScopePlotChannel items.  setItemList
    # expects a list of PlotChannel objects, but all other
    # inserts/append operations expect channel name strings.

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []
        self.header = ("", "name", "color", "width", "scale", "offset", "unit", "label")

    def __contains__(self, name):
        """check that channel name already in table or not"""
        for channel in self.item_list:
            if channel.channel == name:
                return True
        return False

    def _make_item(self, channel: str):
        """make a table item from a channel"""
        return NDScopePlotChannel(channel)

    def canDropMimeData(self, data, action, row, column, parent):
        return data.hasFormat("text/plain")

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.header)

    def data(self, index, role):
        try:
            item = self.item_list[index.row()]
        except IndexError:
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:  # type: ignore
            column_data = (
                "",
                item.channel,
                "",
                item.params["width"],
                item.params["scale"],
                item.params["offset"],
                item.params["unit"],
                item.params["label"],
            )
            return column_data[index.column()]
        elif role == QtCore.Qt.ForegroundRole:  # type: ignore
            return QtGui.QBrush()
        elif role == QtCore.Qt.BackgroundRole and index.column() == 2:  # type: ignore
            return item.get_QColor()
        elif role == QtCore.Qt.ToolTipRole and index.column() == 0:  # type: ignore
            return "remove channel"
        else:
            return QtCore.QVariant()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled  # type: ignore
        try:
            return (
                (QtCore.Qt.ItemNeverHasChildren),  # type: ignore
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
                (QtCore.Qt.ItemNeverHasChildren),  # type: ignore
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                    | QtCore.Qt.ItemIsSelectable  # type: ignore
                ),
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
                (
                    QtCore.Qt.ItemIsEnabled  # type: ignore
                    | QtCore.Qt.ItemIsEditable  # type: ignore
                    | QtCore.Qt.ItemNeverHasChildren  # type: ignore
                ),
            )[index.column()] | QtCore.Qt.ItemIsSelectable  # type: ignore
        except IndexError:
            # return QtCore.Qt.NoItemFlags
            return QtCore.Qt.ItemIsEnabled | QtCoreQt.Qt.ItemIsSelectable  # type: ignore

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:  # type: ignore
            return self.header[section]
        elif orientation == QtCore.Qt.Vertical:  # type: ignore
            return section + 1
        else:
            return QtCore.QVariant()

    def dropMimeData(self, data, action, row, column, parent):
        if data.hasFormat("text/plain"):
            text = data.text()
            text_list = text.splitlines()

            item_list = [
                self._make_item(text) for text in text_list if text not in self
            ]
            count = len(item_list)

            if count > 0:
                if row == -1 and column == -1:
                    if not parent.isValid():
                        # Drop is after last row.
                        row = len(self.item_list)
                        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
                        for i in range(count):
                            self.item_list.insert(row + i, item_list[i])
                        self.endInsertRows()
                        return True
                    else:
                        # Drop is on row.
                        row = parent.row()
                        self.item_list[row] = item_list.pop(0)
                        row = row + 1
                        count = count - 1
                        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
                        for i in range(count):
                            self.item_list.insert(row + i, item_list[i])
                        self.endInsertRows()
                        return True
                elif row >= 0 and column >= 0:
                    # Drop is before first row or between rows.
                    self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
                    for i in range(count):
                        self.item_list.insert(row + i, item_list[i])
                    self.endInsertRows()
                    return True
                else:
                    return False
            else:
                return False

    def mimeData(self, indexes):
        text_list = [
            self.data(index, QtCore.Qt.DisplayRole)  # type: ignore
            for index in indexes
            if index.isValid()
        ]
        text = "\n".join(text_list)
        mime_data = QtCore.QMimeData()
        mime_data.setText(text)
        return mime_data

    def mimeTypes(self):
        return ["text/plain"]

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.item_list)

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction  # type: ignore

    def getItemList(self):
        """get list of PlotChannel objects in the table"""
        return self.item_list

    def setItemList(self, item_list):
        """set the list of PlotChannel objects in the table"""
        self.item_list = item_list

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if count <= 0 or row < 0 or (row + count) > self.rowCount(parent):
            return False
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        for i in range(count):
            del self.item_list[row + i]
        self.endRemoveRows()
        return True

    def removeRow(self, row, parent=QtCore.QModelIndex()):
        return self.removeRows(row, 1, parent)

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole:
            if index.column() == 1:
                self.item_list[index.row()].channel = value
                return True
            elif index.column() == 3:  # width
                if value > 0:
                    self.item_list[index.row()].set_params(width=value)
                    self.dataChanged.emit(index, index, [role])
                    return True
                else:
                    return False
            elif index.column() == 4:  # scale
                self.item_list[index.row()].set_params(scale=value)
                self.dataChanged.emit(index, index, [role])
                return True
            elif index.column() == 5:  # offset
                self.item_list[index.row()].set_params(offset=value)
                self.dataChanged.emit(index, index, [role])
                return True
            elif index.column() == 6:  # unit
                self.item_list[index.row()].set_params(unit=value)
                self.dataChanged.emit(index, index, [role])
                return True
            elif index.column() == 7:  # label
                self.item_list[index.row()].set_params(label=value)
                self.dataChanged.emit(index, index, [role])
                return True
            else:
                return False
        else:
            return False

    def setItemData(self, index, roles):
        if QtCore.Qt.EditRole in roles.keys():  # type: ignore
            return self.setData(index, roles[QtCore.Qt.EditRole], QtCore.Qt.EditRole)  # type: ignore
        elif QtCore.Qt.DisplayRole in roles.keys():  # type: ignore
            return self.setData(
                index,
                roles[QtCore.Qt.DisplayRole],
                QtCore.Qt.DisplayRole,  # type: ignore
            )
        else:
            return False

    def add_channel(self, name):
        """add a channel to the table by name"""
        if name in self:
            return
        row = len(self.item_list)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.item_list.insert(row, self._make_item(name))
        self.endInsertRows()


class ConfigChannelTableView(QtWidgets.QTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self.color_dialog = QtWidgets.QColorDialog()
        self.color_dialog.setModal(True)
        self.clicked.connect(self.clicked_slot)

    def clicked_slot(self, index):
        if index.column() == 0:
            model = self.model()
            model.removeRow(index.row())
        elif index.column() == 2:
            model = self.model()
            item = model.item_list[index.row()]
            color = item.get_QColor()
            self.color_dialog.setCurrentColor(color)
            self.color_dialog.colorSelected.connect(
                lambda color: self.color_selected_slot(color, item)
            )
            self.color_dialog.show()

    def color_selected_slot(self, color, item):
        self.color_dialog.colorSelected.disconnect()
        item.set_params(color=color.name())


class ChannelConfigWidget(*load_ui("channel_config.ui")):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # selected channel table model
        self.channel_table_model = ConfigChannelTableModel()

        # selected channel table view
        self.channel_table_view.setModel(self.channel_table_model)
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            4, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            5, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setSectionResizeMode(
            6, QtWidgets.QHeaderView.ResizeToContents
        )
        self.channel_table_view.horizontalHeader().setHighlightSections(False)
        self.channel_table_view.setDragEnabled(True)
        self.channel_table_view.setAcceptDrops(True)
        self.channel_table_view.setDefaultDropAction(QtCore.Qt.MoveAction)  # type: ignore
        self.channel_table_view.setDragDropOverwriteMode(False)
        self.channel_table_view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.channel_table_view.setWordWrap(False)
        self.push_button_delegate = PushButtonDelegate()
        self.channel_table_view.setItemDelegateForColumn(0, self.push_button_delegate)

    def set_channel_list(self, channel_list):
        self.channel_table_model.setItemList(channel_list)

    def add_channel(self, channel):
        self.channel_table_model.add_channel(channel)

    def get_channel_list(self) -> List[str]:
        return self.channel_table_model.getItemList()


# ------------------------------------------------------------------------------


class ChannelListDialog(QtWidgets.QDialog):
    """modeless dialog to show the channel list"""

    def __init__(
        self,
        channel_list_widget,
        parent=None,
        title="NDS Channel List",
        drag_text="Drag channels into plot to add.",
        buttons_set=QtWidgets.QDialogButtonBox.Close,
    ):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QtWidgets.QLabel(title)
        self.title.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        self.layout.addWidget(self.title)  # type: ignore

        self.channel_list_widget = channel_list_widget
        self.channel_list_widget.setParent(self)
        self.layout.addWidget(self.channel_list_widget)

        self.foot_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.foot_layout)

        self.foot_layout.addWidget(QtWidgets.QLabel(drag_text))
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons_set)
        self.buttonBox.buttons()[0].setDefault(False)
        self.buttonBox.buttons()[0].setAutoDefault(False)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)
        self.foot_layout.addWidget(self.buttonBox)

    def get_channel_names(self) -> List[str]:
        """Return all selected channel names"""
        return self.channel_list_widget.get_channel_names()


class PlotChannelConfigDialog(*load_ui("channel_config_dialog.ui")):
    """modal dialog to configure the channels for an NDScopePlotItem"""

    done_signal = Signal("PyQt_PyObject")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.channel_config_widget = ChannelConfigWidget()
        self.channel_config_widget.setParent(self)
        self.verticalLayout.insertWidget(1, self.channel_config_widget)

        self.dialog_button_box.accepted.connect(self._done_accepted)
        self.dialog_button_box.rejected.connect(self._done_rejected)

        self.math_button.clicked.connect(self._show_math)

    def _show_math(self):
        indices = self.channel_config_widget.channel_table_view.selectedIndexes()

        if len(indices) > 0:
            input_a = self.channel_config_widget.channel_table_view.model().data(
                indices[0],
                QtCore.Qt.DisplayRole,  # type: ignore
            )
        else:
            input_a = ""

        if len(indices) > 1:
            input_b = self.channel_config_widget.channel_table_view.model().data(
                indices[1],
                QtCore.Qt.DisplayRole,  # type: ignore
            )
        else:
            input_b = ""

        math_config = MathConfigDialog(self, self, input_a, input_b)
        if math_config.exec():
            self.channel_config_widget.add_channel(math_config.short_name_edit.text())

    def set_plot(self, plot):
        self.title.setText(f"Configure channels for plot {plot.loc}")
        channel_dict = plot.get_channels()
        self.channel_config_widget.set_channel_list(
            [
                NDScopePlotChannel(chan, **params)
                for chan, params in channel_dict.items()
            ]
        )

    def _done_accepted(self):
        self.done_signal.emit(self.channel_config_widget.get_channel_list())

    def _done_rejected(self):
        self.done_signal.emit(None)

    def add_channel(self, name: str):
        self.channel_config_widget.add_channel(name)


class ChannelSelectDialog(*load_ui("channel_select_dialog.ui")):
    done_signal = Signal("PyQt_PyObject")

    def __init__(self, channel_list_widget, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.channel_list_widget = channel_list_widget
        self.channel_list_widget.setParent(self)
        self.channel_list_layout.addWidget(self.channel_list_widget)
        self.channel_list_widget.available_channel_tree_view.activated.connect(
            self.available_channel_tree_view_activated_slot
        )
        self.channel_list_widget.available_channel_table_view.activated.connect(
            self.available_channel_table_view_activated_slot
        )

        self.channel_config_widget = ChannelConfigWidget()
        self.channel_config_widget.setParent(self)
        self.channel_config_layout.addWidget(self.channel_config_widget)

        self.infoLabel.setText("Double click or drag channels to select.")

        self.dialog_button_box.accepted.connect(self._done_accepted)
        self.dialog_button_box.rejected.connect(self._done_rejected)

    def setSelectedChannels(self, channel_dict):
        self.channel_config_widget.set_channel_list(
            [
                NDScopePlotChannel(chan, **params)
                for chan, params in channel_dict.items()
            ]
        )

    def getSelectedChannelList(self):
        return self.channel_config_widget.get_channel_list()

    def setTitlePlot(self, plot):
        self.title.setText(f"Select/configure channels for plot {plot}")

    # Appends the item in the available channel tree at the supplied
    # index to the end of the selected channel table.
    def available_channel_tree_view_activated_slot(self, index):
        if (
            not self.channel_list_widget.available_channel_tree_proxy_model.hasChildren(
                index
            )
            and index.column() == 0
        ):
            source_index = (
                self.channel_list_widget.available_channel_tree_proxy_model.mapToSource(
                    index
                )
            )
            item = source_index.internalPointer()
            if item.is_leaf:
                channel = item.data
                self.channel_config_widget.add_channel(channel.name)

    # Appends the item in the available channel table at the supplied
    # index to the end of the selected channel table.
    def available_channel_table_view_activated_slot(self, index):
        if index.column() == 0:
            channel = (
                self.channel_list_widget.available_channel_table_model.itemFromIndex(
                    index
                )
            )
            self.channel_config_widget.add_channel(channel.name)

    def _done_accepted(self):
        self.done_signal.emit(self.getSelectedChannelList())

    def _done_rejected(self):
        self.done_signal.emit(None)


# ------------------------------------------------------------------------------


def main():
    import os
    import sys
    import signal
    import logging
    import argparse
    import dttlib
    from queue import SimpleQueue, Empty

    from ._qt import create_app
    from . import nds
    from . import const
    from . import util

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "WARNING").upper(),
        format="%(name)s: %(message)s",
    )

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    PROG = "ndschans"
    DESCRIPTION = "NDS channel search GUI"

    parser = argparse.ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--url", metavar="URL:PORT", help=f"Data source URL")
    parser.add_argument(
        "--nds", metavar="HOST[:PORT]", help=f"NDS server [{const.NDSSERVER}]"
    )
    parser.add_argument(
        "glob",
        nargs="?",
        default=os.getenv("CHANNEL_GLOB", "*"),
        help="channel glob to filter channel list (e.g. 'H1:SUS-*')",
    )

    args = parser.parse_args()

    os.environ["LIGO_DATA_URL"] = util.resolve_data_source(args.nds, args.url)

    server, server_formatted = util.format_nds_server_string()

    channel_dict = None

    queue = SimpleQueue()

    def chans_callback(msg):
        nonlocal queue
        if isinstance(msg, dttlib.ResponseToUser.ChannelQueryResult):
            logger.debug("transform to dict")
            chans = {c.name: c for c in msg.channels}
            queue.put(chans)
        else:
            logger.debug(msg)
        logger.debug("done transform")

    dtt = dttlib.DTT(chans_callback)
    cache = dttlib.NDS2Cache(1 << 30, "").as_ref()
    dtt.set_data_source(cache)
    logger.debug(
        f"Fetching channel list from {server} (channel glob: '{args.glob}')... "
    )
    query = dttlib.ChannelQuery(
        args.glob,
        channel_types=[
            dttlib.ChannelType.Raw,
            dttlib.ChannelType.Online,
            dttlib.ChannelType.TestPoint,
        ],
    )
    dtt.find_channels(query)

    try:
        channel_dict = queue.get(block=True, timeout=30)
    except Empty:
        logger.debug("Timed out while waiting for channel list.")
        sys.exit(1)

    channel_list = list(sorted(channel_dict.values(), key=lambda c: c.name))
    nchannels = len(channel_list)
    logger.debug(f"Channel list received: {nchannels} channels")

    app = create_app()
    clw = ChannelListWidget(
        AvailableChannelTreeModel(channel_list),
        AvailableChannelTableModel(channel_list),
    )
    clw.set_server_info(server_formatted, nchannels, glob=args.glob)
    cld = ChannelListDialog(clw)
    cld.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
