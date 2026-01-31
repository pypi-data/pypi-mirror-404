"""Python helper class for the rust dttlib library.

This class improves on the python interface exported by dttlib.
"""

from __future__ import annotations

import logging
from queue import SimpleQueue
import traceback
from typing import Callable, List, Optional, Union

import dttlib

AnalysisResult = Union[dttlib.TimeDomainArray, dttlib.FreqDomainArray]

ChannelDict = dict[str, dttlib.Channel]
ScopeDataHandler = Callable[[int, AnalysisResult], None]
ChannelsHandler = Callable[[ChannelDict], None]
MessageHandler = Callable[[dttlib.MessageJob], None]
ScopeViewDoneHandler = Callable[[int], None]

logger = logging.getLogger("DTT")


def _channel_priority(a: dttlib.Channel, b: dttlib.Channel) -> dttlib.Channel:
    """
    return the channel that should be kept in the channel list
    useful if there are two with the same name
    """
    if a.channel_type == dttlib.ChannelType.TestPoint:
        return a
    if b.channel_type == dttlib.ChannelType.TestPoint:
        return b
    if a.channel_type == dttlib.ChannelType.Online:
        return a
    if b.channel_type == dttlib.ChannelType.Online:
        return b
    return a


class DTT:
    """A wrapper around the dttlib raw PyO3 interface."""

    def __init__(
        self,
        cache_size_bytes: int = (1 << 30),
        cache_file_path: str = "",
        scope_data_handler: Optional[ScopeDataHandler] = None,
        message_handler: Optional[MessageHandler] = None,
        scope_view_done_handler: Optional[ScopeViewDoneHandler] = None,
    ) -> None:
        """Initialize the object.

        :param cache_size_bytes: The size of the in-memory cache for data bufffers.
        """
        self.dtt = dttlib.DTT(self._callback)
        if scope_data_handler is None:
            # do nothing if no handler
            self.scope_data_handler: ScopeDataHandler = lambda _id, _result: None
        else:
            self.scope_data_handler = scope_data_handler

        if message_handler is None:
            self.message_handler = self._handle_message_job
        else:
            self.message_handler = message_handler

        if scope_view_done_handler is None:
            self.scope_view_done_handler = self._handle_scope_view_done
        else:
            self.scope_view_done_handler = scope_view_done_handler

        self.channel_handler: ChannelsHandler = lambda _channels_dict: None

        cache = dttlib.NDS2Cache(cache_size_bytes, cache_file_path).as_ref()
        self.dtt.set_data_source(cache)

    def _callback(self, msg: dttlib.ResponseToUser) -> None:
        """Handle a callback from dtt lib for any user messages."""
        logger.debug("new msg = %s", msg)
        if isinstance(msg, dttlib.ResponseToUser.ScopeViewResult):
            self.scope_data_handler(msg.id, msg.result)
        elif isinstance(msg, dttlib.ResponseToUser.ChannelQueryResult):
            self._handle_channel_results(msg.channels)
        elif isinstance(msg, dttlib.ResponseToUser.UpdateMessages):
            self.message_handler(msg.message_job)
        elif isinstance(msg, dttlib.ResponseToUser.AllMessages):
            self._handle_all_messages(msg._0)
        elif isinstance(msg, dttlib.ResponseToUser.ScopeViewDone):
            self.scope_view_done_handler(msg.id)
        elif isinstance(msg, Exception):
            self._handle_exception(msg)
        else:
            logger.warning(f"Unknown message: {msg} ({repr(msg)}) [{type(msg)}]")

    def _handle_channel_results(self, channels: List[dttlib.Channel]):
        channels_dict = {}
        for c in channels:
            if c.name in channels_dict:
                channels_dict[c.name] = _channel_priority(channels_dict[c.name], c)
            else:
                channels_dict[c.name] = c
        self.channel_handler(channels_dict)

    def find_channels_blocking(
        self,
        pattern: str,
        channel_types: List[dttlib.ChannelType],
        timeout_sec: float,
    ) -> ChannelDict:
        """Get channels of the given type, filtered by the given pattern.

        :return: A dictionary of channel names mapped to channel objects.
        """
        queue = SimpleQueue()

        def callback(channels: ChannelDict) -> None:
            queue.put(channels)

        self.find_channels_with_callback(pattern, channel_types, callback)
        return queue.get(timeout=timeout_sec)

    def find_channels_with_callback(
        self,
        pattern: str,
        channel_types: list[dttlib.ChannelType],
        callback: ChannelsHandler,
    ) -> None:
        """Find channels from the given channel types that match the pattern.

        Returns immediately, but calls the callback with the found channels.
        Callback argument is a dictionary of channel names as strings mapped to channel objects.
        """
        query = dttlib.ChannelQuery(pattern, channel_types)
        self.channel_handler = callback
        self.dtt.find_channels(query)

    def __getattr__(self, name):
        """Publish any attribute of the DTT object"""
        return getattr(self.dtt, name)

    def set_view_fft_params(
        self,
        view: dttlib.ScopeViewHandle,
        start_pip: dttlib.PipInstant,
        end_pip: dttlib.PipInstant,
        overlap: float,
        bandwidth_hz: float,
        window: Optional[dttlib.FFTWindow] = None,
    ) -> None:
        params = dttlib.InlineFFTParams()
        params.start_pip = start_pip
        params.end_pip = end_pip
        params.overlap = overlap
        params.bandwidth_hz = bandwidth_hz
        if window is not None:
            params.window = window
        try:
            view.set_fft_params(params)
        except RuntimeError as e:
            logger.exception(
                "Failed to set fft params. Probably the view is closed: %s", str(e)
            )

    def _handle_message_job(self, message_job: dttlib.MessageJob) -> None:
        if isinstance(message_job, dttlib.MessageJob.SetMessage):
            logger.debug(
                "set message [%s]: %s", message_job.tag, message_job.msg.message
            )
        elif isinstance(message_job, dttlib.MessageJob.ClearMessage):
            logger.debug("clear message [%s]", message_job.tag)
        else:
            logger.warning("Unknown message job %s", str(message_job))

    def _handle_all_messages(self, messages: dict[str, dttlib.UserMessage]):
        logger.debug("received all messages")

    def _handle_scope_view_done(self, id: int) -> None:
        logger.debug("scope view done (%d) was unhandled", id)

    def _handle_exception(self, msg: Exception) -> None:
        logger.error("Python callback raised an exception into dttlib: %s", msg)

        logger.debug("%s", "\n".join(traceback.format_tb(msg.__traceback__)))
