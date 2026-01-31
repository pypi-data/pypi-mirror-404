"""Hashable Channel ID object that differentiates on name and trend statistic.

The ChannelTrendId class is a hashable class that can identify channels based on channel
name and trend stat (Mean,Max,Min,N etc)
Useful for tracking data by channel without a collision for different trend stats,
but where we don't care about the rate of the trend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dttlib import AnalysisId

from ndscope.math_config import MathConfigDialog

if TYPE_CHECKING:
    from dttlib import Channel, TrendStat
    from typing import Optional


class ChannelTrendId(object):
    """A hashable object that checks against channel name and trend stat.  Useful for plotting."""

    def __init__(
        self,
        channel: Optional[Channel] = None,
        name: Optional[str] = None,
        trend_stat: Optional[TrendStat] = None,
        id: Optional[AnalysisId] = None,
    ) -> None:
        """Initialize object.

        :param channel: Channel object to derive ID from.  If this is set, name and trend_stat must not be set.
        :param name: Channel name. If set, trend_stat must be set and channel must not be set.
        "param trend_stat: The trend statistic.  If set, name must be set and channel must not be set.
        """
        if channel is not None:
            if name is not None or trend_stat is not None or id is not None:
                msg = "Too many arguments defined."
                raise TypeError(msg)
            self.name = channel.name
            self.trend_stat = channel.trend_stat
        elif id is not None:
            if name is not None or trend_stat is not None:
                msg = "Too many arguments defined."
                raise TypeError(msg)
            if isinstance(id, AnalysisId.Simple):
                self.name = id.channel.name
                self.trend_stat = id.channel.trend_stat
            else:
                # must be compound
                name_id = id.to_analysis_name_id()
                self.name = MathConfigDialog.math_registry.reverse_lookup(name_id)
                self.trend_stat = id.first_channel().trend_stat
        elif name is not None and trend_stat is not None:
            self.name = name
            self.trend_stat = trend_stat
        else:
            msg = "Too many arguments defined."
            raise TypeError(msg)

    def __hash__(self) -> int:
        """Hash the id."""
        return hash((self.name, self.trend_stat))

    def __eq__(self, other: ChannelTrendId) -> bool:
        """Test for equality between ids."""
        return self.name == other.name and self.trend_stat == other.trend_stat

    def __str__(self) -> str:
        """Get a user friendly representation of the Id."""
        return f"({self.name}, {self.trend_stat})"

    def __repr__(self) -> str:
        """Get a code friendly representation of the id."""
        return f"ChannelTrendId('name={self.name}', trend_stat={self.trend_stat})"
