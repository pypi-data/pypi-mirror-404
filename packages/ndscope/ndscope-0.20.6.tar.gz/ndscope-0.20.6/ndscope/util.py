import os
from collections import namedtuple
import logging
from urllib.parse import urlparse

from gpstime import gpstime, GPSTimeException

from . import const

logger = logging.getLogger("UTIL")


def resolve_data_source(ndsserver=None, url=None):
    # prefer url to ndsserver, because url support arrakis
    if not ndsserver:
        ndsserver = os.getenv("NDSSERVER", const.NDSSERVER).split(",")[0]
    ndsserver = ndsserver.lower()

    # get some short-hand names for nds server
    ndsserver = const.NDSSERVER_ALIAS_MAP.get(ndsserver, ndsserver)

    # transform into url
    ndsserver = f"nds://{ndsserver}"

    if not url:
        url = os.getenv("LIGO_DATA_URL", ndsserver).split(",")[0]
    url = url.lower()
    return url


def format_nds_server_string():
    server = os.getenv("LIGO_DATA_URL")
    try:
        url = urlparse(server)
    except ValueError:
        logger.error(
            "data source must be a valid url, such as 'nds://nds.ligo.caltech.edu:31200'"
        )
        return ""

    scheme = url.scheme

    if scheme == "":
        scheme = "nds"

    recognized_schemes = "grpc html nds file".split()
    if scheme not in recognized_schemes:
        logger.warning(
            f"Unrecognized url scheme '%s'. The following schemes are recognized: [ %s ]",
            scheme,
            " ".join(recognized_schemes),
        )

    host = url.hostname
    try:
        # converts to int.
        # can return None if port not specified
        port = url.port
    except ValueError:
        logger.warning("Could not convert data source port to a number.")
        port = None
    if port is None:
        port = 31200
        logger.info("Using default port [%d]", port)
    if host is not None:
        formatted = f"{scheme}://{host}"
        # formatted = f'<span style="color:blue">{host}</span>'
        if port != 31200:
            formatted += f":{port}"
    else:
        formatted = f"{scheme}://"
    formatted += str(url.path)
    return server, formatted


def gpstime_parse(time):
    if time is None:
        return None
    try:
        return gpstime.parse(time)
    except GPSTimeException:
        return None
    except ValueError:
        return None


def gpstime_str_gps(gt):
    if gt:
        return str(gt.gps())


def gpstime_str_greg(gt, fmt=const.DATETIME_FMT_OFFLINE):
    if gt is None:
        return
    return gt.astimezone(const.DATETIME_TZ).strftime(fmt)


TD_UNIT_MAP = [
    ("years", 31536000, "{td.years}y"),
    # ('weeks', 7*86400, '{td.weeks}w'),
    ("days", 86400, "{td.days}d"),
    ("hours", 3600, "{td.hours}h"),
    ("minutes", 60, "{td.minutes}m"),
    ("seconds", 1, "{td.seconds}s"),
    ("msecs", 0.001, "{td.msecs}ms"),
    ("usecs", 0.000001, "{td.usecs}μs"),
    # ('nsecs', 0.000000001, '{td.nsecs}ns'),
]


TDUnits = namedtuple("TUnits", [t[0] for t in TD_UNIT_MAP])


class TDStr:
    """class for formatting seconds into a natural language time delta string"""

    def __init__(self, seconds):
        self.total_seconds = seconds
        if seconds < 0:
            self.prefix = "-"
        else:
            self.prefix = ""
        seconds, subsec = divmod(abs(seconds), 1)
        seconds = int(seconds)
        # nsecs = int(subsec * 1e9)
        # usecs, nsecs = divmod(nsecs, 1000)
        usecs = round(subsec * 1e6)
        msecs, usecs = divmod(usecs, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        years, days = divmod(days, 365)
        # weeks, days = divmod(days, 7)
        self.td = TDUnits(
            int(years),
            # int(weeks),
            int(days),
            int(hours),
            int(minutes),
            int(seconds),
            int(msecs),
            int(usecs),
            # int(nsecs),
        )

    def __getitem__(self, item):
        return getattr(self.td, item)

    def __repr__(self):
        """format object string"""
        ofl = []
        for u in self.td._fields:
            ofl.append("{}={}".format(u, self[u]))
        return "{}({}{})".format(
            self.__class__.__name__,
            self.prefix,
            ", ".join(ofl),
        )

    def _fmt_list(self, fl):
        fmt = ",".join(fl)
        return self.prefix + fmt.format(td=self.td)

    def __str__(self):
        """format duration into simplest string representation"""
        if self.total_seconds == 0:
            return "0"
        ofl = [f for u, s, f in TD_UNIT_MAP if self[u] != 0]
        return self._fmt_list(ofl)


def cells_to_tabspec(cells):
    """for a set of occupied cells, return a tabspec dict

    tabspec is keyed by [row, col, rowspan, colspan]

    """
    rows = [x[0] for x in cells]
    cols = [x[1] for x in cells]
    row = min(rows)
    col = min(cols)
    rowspan = len(set(rows))
    colspan = len(set(cols))
    return dict(
        row=row,
        col=col,
        rowspan=rowspan,
        colspan=colspan,
    )
