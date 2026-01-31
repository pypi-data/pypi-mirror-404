from enum import Enum
import logging
import collections
import traceback
import dttlib
from threading import Lock
import asyncio

from qtpy import QtCore
from qtpy.QtCore import Signal, Slot, QTimer  # type: ignore

from rapidfuzz import process, fuzz

from .dtt.channel_trend_id import ChannelTrendId  # type: ignore

from . import nds
from .data import DataBuffer, DataBufferDict
from .exceptions import UnknownChannelError
from .dtt import DTT, AnalysisResult

from typing import TYPE_CHECKING, Set, Union, Optional, Tuple, Dict, List

if TYPE_CHECKING:
    from .result import Result
    from .scope import NDScope

logger = logging.getLogger("CACHE")


class AtomicViewId(object):
    """
    Hold a scope view id
    and allow it to be incremented atomically.
    """

    def __init__(self) -> None:
        self._id = 0
        self._lock = Lock()

    def get(self) -> int:
        return self._id

    def increment(self) -> int:
        with self._lock:
            old_val = self._id
            self._id += 1
        return old_val


class PrimedCache(object):
    """Use with PrimedCache(DataCache):
    to ensure a DataCache is primed at the end of a block.
    """

    def __init__(self, cache: "DataCache"):
        self.cache = cache

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.cache.prime()


class CacheReadyState(Enum):
    Unprimed = 0
    Wait = 3
    Primed = 4


class CacheReady(QtCore.QObject):
    """A statemachine that attempts to meter data flow into the Qt main thread"""

    def __init__(self, delay_ms: int, cache: "DataCache"):
        """
        param delay_sec: delay to introduce between re-priming and actually priing the cache to send data
        """
        self.delay_ms = delay_ms
        self.cache = cache
        self.state = CacheReadyState.Primed
        self.state_lock = Lock()
        self.commands: List[str] = []

    def _add_command(self, command: str):
        if len(self.commands) == 0:
            self.commands = [command]
        elif self.commands[0] != command:
            self.commands = [command] + self.commands

    def request_fire(self, command):
        """
        Request when there's new data that needs to be sent to the scope
        """
        with self.state_lock:
            self._add_command(command)
            if self.state == CacheReadyState.Unprimed:
                pass
            elif self.state == CacheReadyState.Wait:
                pass
            elif self.state == CacheReadyState.Primed:
                self._fire()
                self.state = CacheReadyState.Unprimed
            else:
                raise ValueError(f"unrecognized CacheReadyState {self.state}")
        # print(f"request fire: {self.state}")

    def prime(self):
        """
        Called by the scope when done with some data.
        """
        with self.state_lock:
            if self.state == CacheReadyState.Unprimed:
                self.state = CacheReadyState.Wait
                self._start_delay()
            elif self.state == CacheReadyState.Wait:
                pass
            elif self.state == CacheReadyState.Primed:
                pass
            else:
                raise ValueError(f"unrecognized CacheReadyState {self.state}")
        # print(f"prime: {self.state}")

    def _delay_done(self):
        """
        Called when delay timer is finished
        """
        with self.state_lock:
            if self.state == CacheReadyState.Unprimed:
                pass
            elif self.state == CacheReadyState.Wait:
                if len(self.commands) > 0:
                    self._fire()
                    self.state = CacheReadyState.Unprimed
                else:
                    self.state = CacheReadyState.Primed
            elif self.state == CacheReadyState.Primed:
                pass
            else:
                raise ValueError(f"unrecognized CacheReadyState {self.state}")
        # print(f"delayed: {self.state}")

    def _fire(self):
        """
        Fire a data emit for the associated cache
        """
        if len(self.commands) > 0:
            c = self.commands.pop()
            self.cache.signal_data.emit(c)

    def _start_delay(self):
        QTimer.singleShot(self.delay_ms, lambda: self._delay_done())


class ViewParams:
    def __init__(
        self,
        force: bool,
        online: bool,
        trend: dttlib.TrendType,
        snapshot: bool,
        singleshot: bool,
        channels: Set[dttlib.AnalysisRequestId],
        start: dttlib.PipInstant,
        end: dttlib.PipInstant,
    ):
        # force new view regardless of other checks that might skip it
        self.force = False
        self.online = online
        self.trend = trend

        # snap-shot requests get only cache data and
        # don't try to download remote data
        # useful for fast re-retrieval of data
        self.snapshot = snapshot
        self.singleshot = singleshot
        self.channels = channels
        self.start = start
        self.end = end

    def copy(self) -> "ViewParams":
        return ViewParams(
            self.force,
            self.online,
            self.trend,
            self.snapshot,
            self.singleshot,
            self.channels.copy(),
            self.start,
            self.end,
        )

    def __eq__(self, other: "ViewParams") -> bool:
        return (
            (not self.force)
            and self.online == other.online
            and self.trend == other.trend
            and self.snapshot == other.snapshot
            and self.singleshot == other.singleshot
            and self.channels == other.channels
            and self.start == other.start
            and self.end == other.end
        )

    def needs_new_view(self, other: "ViewParams") -> bool:
        """Return true if the difference between the two paramter objects

        requires a new view, as opposed to just a reset view.
        """
        return (
            self.force
            or self.singleshot
            or self.snapshot
            or self.trend != other.trend
            or self.online != other.online
            or self.snapshot != other.snapshot
            or self.singleshot != other.singleshot
            or self.channels != other.channels
        )

    def __str__(self):
        return f"force={self.force}, singleshot={self.singleshot}, snapshot={self.snapshot}, trend={self.trend}, online={self.online}, #channels = {len(self.channels)}"


class DataCacheContext(object):
    def __init__(self, cache: "DataCache", force=False):
        """

        :param cache: The cache to lock for the context lifespan
        :param force: Force update at the end of the context (or all contexts if nested)
        """
        self.cache = cache
        self._force = force
        self.orig_params: Set[str] = set()

    def force(self, f=True):
        """Force the cache context to update the view on exit"""
        self._force = f

    def __exit__(self, exc_type, exc_val, exc_tb):
        # if the new set of channels matches the previous set then
        # we're done
        if self._force:
            self.cache.next_view_params.force = True
        self.cache.context_nest_level -= 1
        if self.cache.context_nest_level > 0:
            return
        if self.cache.context_nest_level < 0:
            raise ValueError("cache context exited more times than it entered.")
        if self.cache.next_view_params == self.cache.prev_view_params:
            return
        if self.cache.next_view_params.needs_new_view(self.cache.prev_view_params):
            self.cache._new_scope_view()
        else:
            self.cache._set_scope_view()
        self.cache.signal_channel_change.emit(None)

    def __getattr__(self, name):
        return self.cache.__getattribute__(name)

    ##########
    # context manager for adding/removing channels
    # remote_recv_channels
    # This helps coordinating restarts of online streams in case of
    # channel list changes.  once all channel adds/removes are done,
    # any online streams hierarchical task decompositionwill be restarted if needed.

    def __enter__(self) -> "DataCacheContext":
        self.cache.context_nest_level += 1
        return self


class DataCache(QtCore.QObject):
    # signals
    #
    # channel list read
    signal_channel_list_ready = Signal()
    # channel add/remove attempt
    # payload: (channel, error or None)
    signal_channel_change = Signal("PyQt_PyObject")

    # payload a TrendType
    signal_trend_change = Signal("PyQt_PyObject")

    # status and error message from cache data stream
    # payload is a single string
    signal_stream_status = Signal("PyQt_PyObject")
    signal_online_status = Signal("PyQt_PyObject")
    signal_stream_error = Signal("PyQt_PyObject")

    # data buffer in response to data request
    # payload: tuple of
    #   trend type string
    #   trend data buffer
    signal_data = Signal("PyQt_PyObject")

    signal_view_done = Signal(int)

    signal_request_sasl = Signal()
    signal_request_tape = Signal()

    def __init__(self, scope: "NDScope") -> None:
        super().__init__()
        # needed to get the channel list
        self.scope = scope
        self.next_view_params = ViewParams(
            False,
            False,
            dttlib.TrendType.Raw,
            False,
            False,
            set(),
            dttlib.PipInstant.gpst_epoch(),
            dttlib.PipInstant.gpst_epoch(),
        )
        self.prev_view_params = ViewParams(
            False,
            False,
            dttlib.TrendType.Raw,
            False,
            False,
            set(),
            dttlib.PipInstant.gpst_epoch(),
            dttlib.PipInstant.gpst_epoch(),
        )
        self.restart_requested = False
        self.reset()
        self.set_lookback(dttlib.PipDuration.from_sec(2))
        self.view: Optional[dttlib.ScopeViewHandle] = None
        self.available_channels: Optional[Dict[str, dttlib.Channel]] = None
        # sets up call to fetch channel list once the main loop starts
        QtCore.QTimer.singleShot(0, self.fetch_channel_list_async)
        logger.debug("data store initialized")

        # an ever-increasing integer value
        # needs to be incremented any time a scope view changes
        self.dtt = DTT(
            scope_data_handler=self.handle_scope_result,
            message_handler=self._handle_messages,
            scope_view_done_handler=self._handle_view_done,
        )

        self.data_is_online = False
        self.data_lock = Lock()
        self.data_buffers = DataBufferDict()
        self.saved_data = DataBufferDict()
        self.results_lock = Lock()

        self.primed = CacheReady(
            20, self
        )  # when true, send new data to scope immediately

        # plot info needed to update time window for cursors
        self.t0: Optional[dttlib.PipInstant] = None
        self.cursor_pos: Dict[str, float] = {}
        self.results: Dict[str, Result] = {}

        # current state of messages from dttlib
        self.messages: Dict[str, dttlib.UserMessage] = {}

        # when true, check for invalid channels agains
        # once we get a channel list
        # needed for when we get an invalid channel error
        # before we get a channel list
        self.prime_invalid_recheck = False

        # number of context entries we're still in
        # data won't be requested until this drops to zero.
        self.context_nest_level = 0

    ##########

    def _emit_clear(self) -> None:
        self.signal_data.emit("clear")

    def _emit_data(
        self,
        new_buffer: dttlib.TimeDomainArray,
        online: bool,
    ) -> None:
        # for k, d in data.items():
        #     print(
        #         f"{k}: start = {d.gps_start} len = {len(d.data)} rate = {d.channel.rate_hz}"
        #     )

        fire = False
        with self.data_lock:
            self.data_buffers.add_buffer(new_buffer)
            self.saved_data.add_buffer(new_buffer)
            self.data_is_online = online
            self.primed.request_fire("data")

    def _clear_data(self):
        with self.data_lock:
            self.data_buffers.clear()
            self.saved_data.clear()

    def prime(self):
        """
        Tell the cache to send the next block of data
        """
        self.primed.prime()

    def get_data(
        self,
    ) -> Tuple[DataBufferDict, bool]:
        with self.data_lock:
            x = (self.data_buffers, self.data_is_online)
            self.data_buffers = DataBufferDict()
        return x

    def peak_data(self) -> DataBufferDict:
        """Get a copy of the current saved data"""
        with self.data_lock:
            x = DataBufferDict(self.saved_data)
        return x

    ##########

    def __getitem__(self, chan: ChannelTrendId) -> DataBuffer:
        with self.data_lock:
            if chan in self.saved_data:
                data = self.saved_data[chan]
            else:
                data = None
        if data is not None:
            return data
        else:
            raise KeyError

    def __contains__(self, chan: ChannelTrendId) -> bool:
        with self.data_lock:
            contains = self.saved_data.__contains__(chan)
        return contains

    ##########

    def update_context(self, force=False):
        return DataCacheContext(self, force)

    ##########

    def fetch_channel_list_async(self) -> None:
        if self.available_channels:
            return
        self.dtt.find_channels_with_callback(
            "*", nds.CHANNEL_TYPE_MASK, self.remote_recv_channels
        )

    @property
    def empty(self) -> bool:
        """True if there are no channels in the store"""
        return len(self.scope.channels_as_names()) == 0

    @property
    def online(self) -> bool:
        return self.next_view_params.online

    def get_channels(self) -> Set[dttlib.AnalysisRequestId]:
        """set channels to be used in a request

        should be run in context manager to handle online restarts

        """
        ids = self.scope.channels_as_analysis_request_ids()

        # check for misspellings
        channels = set()
        for id in ids:
            channels = channels.union({c.name for c in id.get_channels()})

        for channel in channels:
            if self.available_channels and channel not in self.available_channels:
                similar = self.get_most_similar_channel(channel)
                similar_text = (
                    similar is not None
                    and f". There's a similar channel named '{similar}'."
                    or ""
                )
                error = f"Unknown channel '{channel}'{similar_text}"
                self.signal_channel_change.emit(error)
                raise UnknownChannelError(error)

        self.next_view_params.channels = ids
        return ids

    ##########

    def set_lookback(self, lookback_pip: dttlib.PipDuration):
        start = self.next_view_params.start
        self.next_view_params.end = start + lookback_pip

    def shift_online_endpoint(self, new_end: dttlib.PipInstant):
        dt = new_end - self.next_view_params.end
        self.next_view_params.start += dt
        self.next_view_params.end += dt

    def reset(self):
        """reset the data store (clear all data)"""
        logger.debug("RESET")
        self._emit_clear()

    def online_stop(self):
        """stop online stream"""
        logger.debug("ONLINE STOP")
        with DataCacheContext(self):
            self.next_view_params.online = False

    def online_start(self, trend: dttlib.TrendType, lookback: dttlib.PipDuration):
        """start online stream"""
        logger.debug(f"ONLINE START {trend} {lookback}")

        with DataCacheContext(self):
            self.next_view_params.trend = trend
            self.set_lookback(lookback)
            self.next_view_params.online = True
            self.next_view_params.snapshot = False
            self.next_view_params.force = False
            self.next_view_params.singleshot = False

    def online_restart(self):
        """restart online stream"""
        logger.debug("ONLINE RESTART")
        start = self.next_view_params.start
        end = self.next_view_params.end
        lookback = end - start
        self.online_start(self.next_view_params.trend, lookback)

    def handle_scope_result(self, id: int, result: AnalysisResult) -> None:
        if self.view is not None and id == self.view.id:
            if isinstance(result, dttlib.TimeDomainArray):
                logger.debug("Received data for %s", result.id)
                if (
                    self.data_buffers.trend != result.id.first_channel().trend_type
                    or self.next_view_params.online != self.data_is_online
                ):
                    self._clear_data()
                self._emit_data(
                    result,
                    self.next_view_params.online,
                )
                _, end = self.data_buffers.range
                self.shift_online_endpoint(end)
            else:
                logger.warning(f"unknown result type: {type(result)}")

    def _new_scope_view(self):
        """Create a new scope view.
        This should be called if the channel list has changed.
        Or if there is no scope view (self.view is None)
        """
        assert self.context_nest_level == 0
        self.get_channels()
        if self.check_online_channels():
            if self.view is not None:
                try:
                    self.view.close()
                except RuntimeError:
                    logger.info("Closed view that was already closed.")

            if self.next_view_params.online and self.next_view_params.snapshot:
                logger.error("Cannot get a snapshot scope view while online")
            elif self.next_view_params.online and self.next_view_params.singleshot:
                logger.error("Cannot get a singleshot scope view while online")
            else:
                self.signal_trend_change.emit(self.next_view_params.trend)
                self.prev_view_params = self.next_view_params.copy()
                self.next_view_params.force = False

                start_pip = self.next_view_params.start
                end_pip = self.next_view_params.end
                span_pip = end_pip - start_pip
                self.data_buffers.clear()

                # we haven't had a scope view yet, so we'll create one from scratch.
                view_set = dttlib.ViewSet.from_analysis_request_ids(
                    self.next_view_params.channels
                )
                logger.debug(
                    "New scope view: %s %f - %f",
                    self.next_view_params.online and "online" or "fixed",
                    start_pip.to_gpst_seconds(),
                    end_pip.to_gpst_seconds(),
                )

                if self.next_view_params.online:
                    msg = f"Retrieving {self._command_description('online', self.next_view_params.trend)}..."
                    self.view = self.dtt.new_online_scope_view(view_set, span_pip)
                else:
                    msg = f"Retrieving {self._command_description('', self.next_view_params.trend)}..."
                    if self.next_view_params.snapshot:
                        self.view = self.dtt.new_snapshot_scope_view(
                            view_set, start_pip, end_pip
                        )
                    elif self.next_view_params.singleshot:
                        self.view = self.dtt.new_singleshot_scope_view(
                            view_set, start_pip, end_pip
                        )
                    else:
                        self.view = self.dtt.new_fixed_scope_view(
                            view_set, start_pip, end_pip
                        )

    def _set_scope_view(self):
        """Update the existing scope view.

        This should be called if the view has changed but not the channel list
        """
        if self.view is None:
            self._new_scope_view()
        else:
            start_pip = self.next_view_params.start
            end_pip = self.next_view_params.end
            span_pip = end_pip - start_pip

            try:
                if self.next_view_params.online:
                    self.view.update(span_pip=span_pip)
                else:
                    self.view.update(start_pip=start_pip, end_pip=end_pip)
            except RuntimeError as e:
                logger.warning(
                    f"failed to update scope view: {e} Probably the scope view is closed."
                )
                self.view = None
                self._new_scope_view()
                return

    def check_online_channels(self) -> bool:
        """return true if we're offline or if all requested channels are online

        If (we're making on online request with channels that aren't online)
        send an error to the scope window
        """
        if self.next_view_params.online:
            if self.available_channels is not None:
                offline_chans: Set[dttlib.Channel] = set()

                channels = self.channel_names()

                for channel in channels:
                    if (
                        channel in self.available_channels
                        and not self.available_channels[channel].online
                    ):
                        offline_chans.add(self.available_channels[channel])
                if len(offline_chans) > 0:
                    if len(offline_chans) > 1:
                        c = offline_chans.pop()
                        msg = f"{len(offline_chans)} channels were not availabe for online streaming, including {c.name}"
                    else:
                        c = offline_chans.pop()
                        msg = f"{c.name}, trend {c.trend_type} is not available for online streaming"
                    logger.error(msg)
                    self.signal_stream_error.emit(msg)
                    return False
        return True

    def request(
        self, trend, start_end, force_new=False, snapshot=False, singleshot=False
    ):
        """Request data of the cache

        `trend` should be one of ['raw', 'sec', 'min'], and
        `start_end` should be a tuple of (start, end) times.

        `snapshot` request data directly from the cache.  don't query any data source.
        Useful for dumping data to a file.

        `singleshot` close the ScopeView generated by the request when there's all available
        data has been sent. Useful for the --singleshot command line argument
        """

        logger.debug(
            "REQUEST: {} ({} {})".format(
                trend, start_end[0].to_gpst_seconds(), start_end[1].to_gpst_seconds()
            )
        )

        with DataCacheContext(self, force_new):
            self.next_view_params.trend = trend
            self.next_view_params.start = start_end[0]
            self.next_view_params.end = start_end[1]
            self.next_view_params.snapshot = snapshot
            self.next_view_params.singleshot = singleshot
            start, end = start_end
            assert end > start

    def _update_fft_range(self):
        """ """
        range = self._get_cursor_range_pips()
        if range is not None and self.view is not None:
            start, end = range
            self.dtt.set_view_fft_params(self.view, start, end, 0.5, 0.1)

    def handle_cursor_moved(self, cursor_info: Tuple[str, float]):
        self.cursor_pos[cursor_info[0]] = cursor_info[1]
        self._update_fft_range()

    def set_t0(self, t0: dttlib.PipInstant):
        self.t0 = t0
        self._update_fft_range()

    def _get_cursor_range_pips(
        self,
    ) -> Optional[Tuple[dttlib.PipInstant, dttlib.PipInstant]]:
        if self.t0 is not None and "C1" in self.cursor_pos and "C2" in self.cursor_pos:
            logger.debug(f"t0={self.t0.to_gpst_seconds()} cursor_pos={self.cursor_pos}")
            c1 = dttlib.PipDuration.from_seconds(self.cursor_pos["C1"])
            c2 = dttlib.PipDuration.from_seconds(self.cursor_pos["C2"])
            t0 = self.t0
            if c1 < c2:
                return t0 + c1, t0 + c2
            else:
                return t0 + c2, t0 + c1
        else:
            return None

    def get_result_store(self) -> Dict[dttlib.AnalysisId, AnalysisResult]:
        """
        Export current data to a file at path
        """
        if self.view is not None:
            return self.view.get_result_store()
        logger.warning("Tried to get result store when now scope view was configured.")
        return {}

    def _handle_view_done(self, id: int):
        self.primed.request_fire("done")

    ##########

    def _command_description(self, cmd, trend: dttlib.TrendType):
        if cmd == "online":
            desc = "online "
        else:
            desc = ""
        if trend == "sec":
            desc += "second trend data"
        elif trend == "min":
            desc += "minute trend data"
        elif trend == "raw":
            desc += "raw data"
        return desc

    def remote_cmd(self, cmd, **kwargs):
        raise Exception("no longer used")

    def remote_recv_channels(self, channels: Union[str, Dict[str, "dttlib.Channel"]]):
        if isinstance(channels, str):
            # error message
            pass
        else:
            nchannels = len(channels)
            logger.info(f"channel list received: {nchannels} channels")
            self.available_channels = channels
            self.signal_channel_list_ready.emit()
            if self.prime_invalid_recheck:
                self._post_stream_message("Invalid channel")

    @Slot()
    def remote_done(self):
        logger.debug("DONE")
        if self.view is not None:
            try:
                self.view.close()
            except RuntimeError:
                logger.info("Closed view that was already closed")

    def stop(self):
        logger.debug("STOP")
        with DataCacheContext(self):
            self.next_view_params.online = False

    async def find_bad_channels_async(self, channel_list: List[str]):
        async def worker(dtt: DTT, channel: str):
            out = await asyncio.to_thread(nds.find_channels, dtt, channel)
            if not out:
                return channel

        tasks = []
        for channel in channel_list:
            tasks.append(asyncio.create_task(worker(self.dtt, channel)))
        await asyncio.gather(*tasks, return_exceptions=True)
        return set([task.result() for task in tasks if task.result()])

    ##################################################################

    def _handle_messages(self, msg: dttlib.MessageJob) -> None:
        """
        Handle incoming user messages from dttlib
        """
        logger.debug("msg=%s", str(msg))
        if isinstance(msg, dttlib.MessageJob.SetMessage):
            self.messages[msg.tag] = msg.msg
        elif isinstance(msg, dttlib.MessageJob.ClearMessage):
            if msg.tag in self.messages:
                del self.messages[msg.tag]
        else:
            logger.info("Unknown message type %s", msg)
        tag = msg.get_tag()
        if tag == "stream_status":
            self._handle_stream_status()
        elif tag == "stream_error" or tag == "REQSIZE":
            if (
                not isinstance(msg, dttlib.MessageJob.SetMessage)
                or msg.msg.severity >= dttlib.Severity.Error
            ):
                self._handle_stream_error()
        elif tag == "online_status":
            self._handle_online_status()
        elif tag == "find_channels":
            if "Request SASL authentication protocol" in str(msg):
                self.signal_request_sasl.emit()
        else:
            logger.info("got unhandled message tag %s", tag)

    def _handle_stream_status(self):
        """ """
        if "stream_status" in self.messages:
            self._set_stream_status(self.messages["stream_status"].message)
        else:
            self._set_stream_status("")

    def _handle_online_status(self):
        """ """
        if "online_status" in self.messages:
            self._set_online_status(self.messages["online_status"].message)
        else:
            self._set_online_status("")

    def get_most_similar_channel(self, channel: str) -> Optional[str]:
        """Return the channel in available_channels that's string-wise most similar

        Or None if no similar string could be found.
        """
        best_match = None
        if self.available_channels is not None:
            result = process.extractOne(
                channel, self.available_channels.keys(), scorer=fuzz.WRatio
            )
            if result is not None:
                best_match, best_score, edit_distance = result
        return best_match

    def channel_names(self) -> Set[str]:
        names: Set[str] = set()
        for id in self.prev_view_params.channels:
            names = names.union({c.name for c in id.get_channels()})
        return names

    def guess_invalid_channel(self, msg: str) -> str:
        """Transform 'Invalid channel name' messages into something more helpful"""
        if "Invalid channel" in msg:
            channels = self.channel_names()
            suspect = None
            if len(channels) == 1:
                # only channel is natural suspect
                suspect = list(channels)[0]
            elif len(channels) > 1:
                first_not_online = None
                if self.available_channels is not None:
                    for chan in channels:
                        if (
                            len(self.available_channels) > 0
                            and chan not in self.available_channels
                        ):
                            suspect = chan
                            break
                        if (
                            first_not_online is None
                            and not self.available_channels[chan].online
                        ):
                            first_not_online = chan
                if suspect is None:
                    suspect = first_not_online
            if suspect is not None:
                if self.available_channels is not None:
                    if (
                        len(self.available_channels) > 0
                        and suspect not in self.available_channels
                    ):
                        match = self.get_most_similar_channel(suspect)
                        if match is not None:
                            similar = f" Similar to '{match}'"
                        else:
                            similar = ""
                        msg = f"'{suspect}' is not a recognized channel.{similar}"
                    elif (
                        self.next_view_params.online
                        and not self.available_channels[suspect].online
                    ):
                        msg = f"'{suspect}' is not available for online streaming"
                    else:
                        trend = str(self.next_view_params.trend)
                        online = self.next_view_params.online and " online" or ""
                        msg = f"'{suspect}' is not valid for {trend}{online}"
                else:
                    self.prime_invalid_recheck = True
                    trend = str(self.next_view_params.trend)
                    online = self.next_view_params.online and " online" or ""
                    msg = f"'{suspect}' is not valid for {trend}{online}"
        return msg

    def _post_stream_message(self, msg):
        self.prime_invalid_recheck = False
        msg = self.guess_invalid_channel(msg)
        self._set_stream_error(msg)

    def _handle_stream_error(self):
        """ """
        if "stream_error" in self.messages:
            self._post_stream_message(self.messages["stream_error"].message)
        elif "REQSIZE" in self.messages:
            self._set_stream_error(self.messages["REQSIZE"].message)
        else:
            self._set_stream_error("")

    def _set_stream_status(self, status: str) -> None:
        self.signal_stream_status.emit(status)

    def _set_online_status(self, status: str) -> None:
        self.signal_online_status.emit(status)

    def _set_stream_error(self, err: str) -> None:
        self.signal_stream_error.emit(err)
