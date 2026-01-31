from __future__ import annotations

import numpy as np
import traceback
from typing import Optional, Sequence, Union

from dttlib import (
    PipInstant,
    TrendType,
    PipDuration,
    Channel,
    TimeDomainArray,
    FreqDomainArray,
)

from . import const
from .dtt.channel_trend_id import ChannelTrendId


def _ctype_map(ctype):
    return {
        "online": "raw",
        "raw": "raw",
        "reduced": "raw",
        "s-trend": "sec",
        "m-trend": "min",
    }.get(ctype, "raw")


class DataBuffer(object):
    """data storage

    The data attribute here is actually a dict of sub-data arrays all
    with the same meta-data.  For trend data the keys should be
    ['mean', 'min', 'max'], and for full they would just be ['raw'].

    """

    __slots__ = [
        "__weakref__",
        "id",
        "ctype",
        "sample_rate",
        "trend",
        "trend_stat",
        "unit",
        "data",
        "size",
        "gps_start",
        "real_gps_end",
        "tarray",
        "max_samples",
        "period_pip",
        "original_struct",
        "_tarray_pip",
    ]

    def __init__(
        self,
        buf: Optional[TimeDomainArray],
        clone_from: Optional[DataBuffer] = None,
    ):
        """initialize with NDS-like Buffer object

        Or alternatively, clone the meta data from clone_from
        but leave the start time and data empty.  Useful for creating slices of a data buffer
        """

        # self.channel, self.ctype, mod = nds.parse_nds_channel(channel_name)
        if buf is not None:
            self.id = buf.id

            # self.ctype = "online"
            # self.trend = _ctype_map(self.ctype)

            # mod = "raw"
            channel = self.id.first_channel()
            self.ctype = channel.channel_type
            self.trend = channel.trend_type
            self.trend_stat = channel.trend_stat

            self.sample_rate = buf.rate_hz
            self.period_pip = buf.period_pip
            self.unit = buf.unit
            self.data: np.ndarray = buf.data
            self.gps_start: PipInstant = buf.start_gps_pip
            self.real_gps_end: PipInstant = buf.real_end_gps_pip or buf.end_gps_pip()
            self.original_struct = buf
            # self.max_samples = int(const.DATA_LOOKBACK_LIMIT_BYTES / buf.channel.DataTypeSize())
            self.max_samples = int(
                const.TREND_MAX_SECONDS[self.trend] * self.sample_rate
            )
            self._tarray_pip: Optional[np.ndarray] = None
        elif clone_from is not None:
            self.id = clone_from.id
            self.ctype = clone_from.ctype
            self.trend = clone_from.trend
            self.trend_stat = clone_from.trend_stat
            self.sample_rate = clone_from.sample_rate
            self.period_pip = clone_from.period_pip
            self.unit = clone_from.unit
            self.data = np.asarray([])
            self.gps_start = PipInstant.gpst_epoch()
            self.original_struct = clone_from.original_struct
            self.max_samples = clone_from.max_samples
            self._tarray_pip = clone_from._tarray_pip
            self.real_gps_end = clone_from.real_gps_end
        else:
            raise ValueError(
                "One of buf or clone_from must not be None when creating a DataBuffer"
            )

    def tarray_pip(self) -> np.ndarray:
        """
        Return the time array for the data buffer as a list of gps_pip timestamps
        """
        if self._tarray_pip is None:
            self._tarray_pip = self.original_struct.timestamps()
        return self._tarray_pip

    def tarray_sec(self, t0: PipInstant) -> np.ndarray:
        """
        Return the time array in seconds that maps to the data array, as an offset form t0
        """
        return self.original_struct.delta_t_seconds(t0)

    def trim_before(self, t0: PipInstant) -> DataBuffer:
        """Return a new buffer that includes all the data in in this buffer
        after the given point in time."""
        delta: PipDuration = t0 - self.gps_start
        delta.snap_up_to_step(self.period_pip)
        if delta <= PipDuration.from_sec(0):
            return self
        count = int(delta / self.period_pip)
        new_t0 = self.gps_start + delta
        cloned = DataBuffer(buf=None, clone_from=self)
        cloned.gps_start = new_t0
        cloned.data = self.data[count:]
        cloned._tarray_pip = self.tarray_pip()[count:]
        return cloned

    def __repr__(self):
        return "<DataBuffer {} {}, {} Hz, [{}, {})>".format(
            self.id,
            self.trend,
            self.sample_rate,
            self.gps_start.to_gpst_seconds(),
            self.gps_end.to_gpst_seconds(),
        )

    def __len__(self):
        return len(self.data)

    # def __getitem__(self, _):
    #     return self.data[mod]

    # def __contains__(self, mod):
    #     return mod in self.data

    # def keys(self):
    #     return self.data.keys()

    # def values(self):
    #     return self.data.values()

    # def items(self):
    #     return self.data.items()

    @property
    def is_trend(self):
        is_trend = self.trend in [TrendType.Minute, TrendType.Second]
        return is_trend

    @property
    def step(self):
        return 1.0 / self.sample_rate

    @property
    def tlen(self):
        """time length of buffer in seconds"""
        # FIXME: this, and consequently gps_end is subject to
        # round-off accumulation error.  Should have better way to
        # calculate time array and gps_end time.
        return len(self) * self.period_pip

    @property
    def gps_end(self) -> PipInstant:
        return self.gps_start + self.tlen

    @property
    def range(self) -> tuple[PipInstant, PipInstant]:
        """
        get the beginning and end of the data in seconds
        """
        return self.gps_start, self.gps_end

    @property
    def span(self) -> PipDuration:
        return self.gps_end - self.gps_start


class DataBufferDict(object):
    """

    Takes NDS-like Buffer list at initialization and organizes the
    included data into a dictionary of DataBuffer objects keyd by
    channel name and trend_stat.

    """

    __slots__ = [
        "__weakref__",
        "buffers",
    ]

    def __init__(self, copy_from: Optional["DataBufferDict"] = None):
        if copy_from is None:
            self.buffers: dict[ChannelTrendId, DataBuffer] = {}
        else:
            self.buffers = {k: v for k, v in copy_from.buffers.items()}

    def add_buffer(self, buf: TimeDomainArray):
        # buffer lists should have unique channel,ctype,mod combos
        chan = ChannelTrendId(id=buf.id)
        try:
            db = DataBuffer(buf)
        except Exception as _:
            traceback.print_exc()
        else:
            self.buffers[chan] = db

    def __repr__(self):
        return "<DataBufferDict {}>".format(list(self.buffers.keys()))

    def __getitem__(self, channel: ChannelTrendId):
        return self.buffers[channel]

    def __delitem__(self, channel: ChannelTrendId):
        del self.buffers[channel]

    def __contains__(self, channel: ChannelTrendId):
        return channel in self.buffers

    def __len__(self):
        return self.buffers.__len__()

    def items(self):
        return self.buffers.items()

    def values(self):
        return self.buffers.values()

    def clear(self):
        return self.buffers.clear()

    @property
    def is_trend(self) -> bool:
        for val in self.buffers.values():
            return val.is_trend
        return False

    @property
    def trend(self) -> TrendType:
        """Trend of first buffer.  Not guaranteed to match all buffers."""
        for val in self.buffers.values():
            return val.trend
        return TrendType.Raw

    @property
    def range(self) -> tuple[PipInstant, PipInstant]:
        """
        get the total time span of all values in seconds
        """
        gps_start: Optional[PipInstant] = None
        gps_end: Optional[PipInstant] = None

        for buf in self.buffers.values():
            if gps_start is None or gps_start > buf.gps_start:
                gps_start = buf.gps_start
            if gps_end is None or gps_end < buf.gps_end:
                gps_end = buf.gps_end

        if gps_end is None or gps_start is None:
            raise ValueError("can't get range of an empty buffer")

        return gps_start, gps_end

    @property
    def real_range(self) -> tuple[PipInstant, PipInstant]:
        """
        get the total time span of all values in seconds
        use the "real end" given by the data.
        This can be different than the calculated end for subsampled arrays
        """
        gps_start: Optional[PipInstant] = None
        gps_end: Optional[PipInstant] = None

        for buf in self.buffers.values():
            if gps_start is None or gps_start > buf.gps_start:
                gps_start = buf.gps_start
            if gps_end is None or gps_end < buf.real_gps_end:
                gps_end = buf.real_gps_end

        if gps_end is None or gps_start is None:
            raise ValueError("can't get range of an empty buffer")

        return gps_start, gps_end
