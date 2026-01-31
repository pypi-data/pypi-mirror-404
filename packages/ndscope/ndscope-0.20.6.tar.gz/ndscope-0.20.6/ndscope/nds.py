import os
import time
import logging
from typing import Tuple, List, Optional, Dict, Union

import numpy as np
from dttlib import Channel, ChannelQuery, ChannelType
from gpstime import gpsnow

from qtpy import QtCore
from qtpy.QtCore import Signal

from .dtt import DTT

logger = logging.getLogger("NDS  ")


##########

# ctypes: 'online', 's-trend', 'm-trend'
# mods: 'raw', 'min', 'max', 'mean'

CHANNEL_TYPE_MASK = [
    ChannelType.Online,
    ChannelType.Raw,
    ChannelType.RDS,
    ChannelType.TestPoint,
]

TREND_CTYPE_MAP = {
    "raw": ChannelType.Raw,
    "s-trend": ChannelType.STrend,
    "m-trend": ChannelType.MTrend,
}

TREND_RATE_MAP = {
    "s-trend": 1,
    "m-trend": 1 / 60,
}

##########


def _parse_channel_string(channel):
    """parse channel string into (name, ctype, mod)"""
    ct = channel.split(",")
    try:
        name, mod = ct[0].split(".")
    except ValueError:
        name = ct[0]
        mod = "raw"
    try:
        ctype = ct[1]
    except IndexError:
        ctype = "raw"
    return name, ctype, mod


class FakeChannel:
    def __init__(self, name, ctype, sample_rate, unit):
        self.name = name
        self.ctype = ctype
        self.sample_rate = sample_rate
        self.unit = unit

    @property
    def channel_type(self):
        return TREND_CTYPE_MAP[self.ctype]

    def Units(self):
        return self.unit

    def DataTypeSize(self):
        return 8

    def __str__(self):
        return f"<{self.__class__.__name__}: '{self.name}' {self.ctype} {self.sample_rate} {self.unit}>"


class FakeBuffer:
    def __init__(self, channel, seconds, nanoseconds, data):
        self.channel = channel
        assert isinstance(seconds, int)
        assert isinstance(nanoseconds, int)
        self.gps_seconds = seconds
        self.gps_nanoseconds = nanoseconds
        self.data = data

    def __repr__(self):
        return "<{} {} {}.{} {}>".format(
            self.__class__.__name__,
            self.channel.name,
            self.gps_seconds,
            self.gps_nanoseconds,
            len(self.data),
        )


class FakeChannelSource:
    def __init__(self, name, sample_rate, unit):
        self.name = name
        self.sample_rate = sample_rate
        self.unit = unit
        self.amp = np.random.normal(10, 5, 1)
        self.freq = 2 * np.pi * np.random.normal(1, 1 / 2, 1)
        self.phase = 2 * np.pi * np.random.random()
        self.offset = np.random.normal(0, 20, 1)

    def get_channel(self, ctype="raw", mod="raw"):
        if ctype == "raw":
            sample_rate = self.sample_rate
            name = f"{self.name}"
        else:
            sample_rate = TREND_RATE_MAP[ctype]
            name = f"{self.name}.{mod}"
        return FakeChannel(name, ctype, sample_rate or self.sample_rate, self.unit)

    def sampler(self, t, mod):
        # FIXME: use mod appropriately
        # signal
        data = self.amp * np.sin(t * self.freq + self.phase)
        # add offset
        data += self.offset
        # add noise
        # data += np.random.normal(0, 1, len(t))
        data += np.random.exponential(3, len(t))
        # add glitches
        # data += 20 * np.random.power(0.1, len(t)) * np.random.choice([-1,1])
        # add a gap
        if np.random.randint(0, 100) == 0:
            data *= np.nan
        return data

    def gen_buf(self, ctype, mod, start, stride) -> FakeBuffer:
        channel = self.get_channel(ctype, mod)
        sample_rate = channel.sample_rate
        seconds = int(start)
        nanoseconds = int((start % 1) * 1e9)
        nsamples = int(sample_rate * stride)
        t = np.arange(nsamples) / sample_rate + seconds + nanoseconds * 1e-9
        data = self.sampler(t, mod)
        data = np.where(t < gpsnow(), data, np.nan)
        return FakeBuffer(
            channel,
            seconds,
            nanoseconds,
            data,
        )


class FakeSource:
    def __init__(self, channels):
        self.sources = {args[0]: FakeChannelSource(*args) for args in channels}

    def gen_bufs(
        self, channels: List[str], start: int, stride: int
    ) -> List[FakeBuffer]:
        bufs = []
        for chan in channels:
            name, ctype, mod = _parse_channel_string(chan)
            try:
                buf = self.sources[name].gen_buf(
                    ctype,
                    mod,
                    start,
                    stride,
                )
            except KeyError:
                # raise RuntimeError(f"Unknown channel: {chan}")
                raise
            bufs.append(buf)
        return bufs


FAKE_SOURCE = FakeSource(
    [
        ("T1:A-B", 2**14, None),
        ("T1:B-C", 2**12, "W"),
        ("T1:C_D", 2**11, "V"),
        ("T1:D-F_G", 2**10, None),
        ("T1:E-F_G_DAQ", 2**9, None),
        ("T1:F", 2**4, None),
        ("A", 2**14, None),
        ("B", 2**12, "W"),
        ("C", 2**11, "V"),
        ("D", 2**10, None),
        ("E", 2**9, None),
        ("F", 2**4, None),
    ]
)


def fake_find_channels(**kwargs):
    return [source.get_channel() for source in FAKE_SOURCE.sources.values()]


def fake_fetch(
    channels: Optional[List[str]] = None,
    gps_start: Optional[int] = None,
    gps_stop: Optional[int] = None,
    **_kwargs,
) -> List[FakeBuffer]:
    global FAKE_SOURCE
    stride = gps_stop - gps_start
    return FAKE_SOURCE.gen_bufs(channels, gps_start, stride)


def fake_iterate(channels=None, stride=None, **kwargs):
    global FAKE_SOURCE
    if stride == -1:
        stride = 1.0 / 16
    start = np.floor(gpsnow()) - stride
    while True:
        yield FAKE_SOURCE.gen_bufs(channels, start, stride)
        start += stride
        while gpsnow() <= start + stride:
            time.sleep(0.01)


##########


def get_parameters():
    params = nds2.parameters()
    params.set("GAP_HANDLER", "STATIC_HANDLER_NAN")
    return params


def find_channels(dtt: DTT, channel_glob: Optional[str] = None) -> Dict[str, Channel]:
    channel_types = CHANNEL_TYPE_MASK
    logger.debug(
        f"find_channels(**pattern={channel_glob} channel_types={channel_types})"
    )
    return dtt.find_channels_blocking(channel_glob, channel_types, 60)


def iterate(channels, start_end: Tuple[int, int], stride: int):
    kwargs = {
        "channels": channels,
        "stride": stride,
        "params": get_parameters(),
    }
    if start_end:
        kwargs["gps_start"] = start_end[0]
        kwargs["gps_stop"] = start_end[1]
    if os.getenv("NDSSERVER", "").lower() == "fake":
        func = fake_iterate
    else:
        func = nds2.iterate
    logger.debug("iterate(**{})".format(kwargs))
    for bufs in func(**kwargs):
        yield bufs


def fetch(channels: List[str], start_end: Tuple[int, int]):
    kwargs = {
        "channels": channels,
        "gps_start": start_end[0],
        "gps_stop": start_end[1],
        "params": get_parameters(),
    }
    if os.getenv("NDSSERVER", "").lower() == "fake":
        func = fake_fetch
    else:
        func = nds2.fetch
    logger.debug("fetch(**{})".format(kwargs))
    return func(**kwargs)


def parse_nds_channel(channel):
    """parse nds.channel object into (name, ctype, mod)"""
    ctype = nds2.channel.channel_type_to_string(channel.channel_type)
    if ctype in ["s-trend", "m-trend"]:
        # HACK: FIXME: work around a bug in nds2-client around 0.16.3:
        # https://git.ligo.org/nds/nds2-client/issues/85. this should
        # not be necessary (to split on ',') and should be removed
        # once the client is fixed.
        namemod = channel.name.split(",")[0]
        name, mod = namemod.split(".")
    else:
        name = channel.name
        mod = "raw"
    return name, ctype, mod


def _channels_for_trend(channels, trend):
    if trend == "raw":
        return channels
    else:
        # use first letter of trend type ('s' or 'm')
        t = trend[0]
        chans = []
        for chan in channels:
            for m in ["mean", "min", "max"]:
                chans.append("{}.{},{}-trend".format(chan, m, t))
        return chans


def _start_end_quant(start_end, trend):
    if not start_end:
        return
    start = int(start_end[0])
    end = int(np.ceil(start_end[1]))
    if trend == "min":
        start -= start % 60
        end += 60 - (end % 60)
    assert start < end, "invalid times: {} >= {}".format(start, end)
    return (start, end)


##################################################


class NDSThread(QtCore.QThread):
    new_data = Signal("PyQt_PyObject")
    done_signal = Signal("PyQt_PyObject")

    def __init__(self, tid, cmd, **kwargs):
        super(NDSThread, self).__init__()
        self.tid = tid
        self.cmd = cmd
        if self.cmd == "find_channels":
            self.method = "find_channels"
        elif self.cmd == "online":
            self.method = "iterate"
        else:
            self.method = "fetch"
        self.kwargs = kwargs
        self._run_lock = QtCore.QMutex()
        self._running = True

    @property
    def running(self):
        try:
            self._run_lock.lock()
            # FIXME: python3
            # else:
            return self._running
        finally:
            self._run_lock.unlock()

    def run(self, dtt: DTT):
        error = None

        if self.method == "fetch":
            trend = self.kwargs["trend"]
            channels = _channels_for_trend(self.kwargs["channels"], trend)
            start_end = _start_end_quant(self.kwargs["start_end"], trend)
            try:
                bufs = fetch(channels, start_end)
                if self.running:
                    self.new_data.emit((self.cmd, trend, bufs))
            except RuntimeError as e:
                error = str(e).split("\n")[0]
            # HACK: FIXME: catch TypeError here because of a bug in
            # the client that started around 0.16.3, that is actually
            # exposing a bug in the NDS1 server:
            # https://git.ligo.org/cds/ndscope/issues/109.  Quick
            # successive fetches cause the server to start returning
            # garbage, that shows up as a TypeError in the client
            except TypeError as e:
                error = str(e).split("\n")[0]

        elif self.method == "iterate":
            trend = self.kwargs["trend"]
            channels = _channels_for_trend(self.kwargs["channels"], trend)
            start_end = _start_end_quant(self.kwargs.get("start_end"), trend)
            stride = {
                "raw": nds2.connection.FAST_STRIDE,
                "sec": 1,
                "min": 60,
            }[trend]
            try:
                for bufs in iterate(channels, start_end, stride):
                    if self.running:
                        self.new_data.emit((self.cmd, trend, bufs))
                    else:
                        break
            except RuntimeError as e:
                error = str(e).split("\n")[0]

        elif self.method == "find_channels":
            try:
                channel_list = find_channels(dtt)
                if self.running:
                    self.new_data.emit(channel_list)
            except RuntimeError as e:
                error = str(e).split("\n")[0]

        self.done_signal.emit((self.tid, error))

    def stop(self):
        # disconnect any data connections
        try:
            self.new_data.disconnect()
        except TypeError:
            # diconnect throws a TypeError if there are no connections
            pass
        self._run_lock.lock()
        self._running = False
        self._run_lock.unlock()
