"""Integration tests for data flow through the ndscope system"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from dttlib import (
    PipInstant,
    PipDuration,
    TrendType,
    TrendStat,
    AnalysisRequestId,
    ChannelType,
)

from ..data import DataBuffer, DataBufferDict
from ..dtt.channel_trend_id import ChannelTrendId
from .. import template


class TestDataBuffer:
    """Tests for DataBuffer data handling"""

    @pytest.fixture
    def mock_time_domain_array(self):
        """Create a mock TimeDomainArray"""
        mock = MagicMock()
        mock.id = MagicMock()
        mock.id.first_channel.return_value = MagicMock(
            channel_type=ChannelType.Raw,
            trend_type=TrendType.Raw,
            trend_stat=TrendStat.Raw,
        )
        mock.rate_hz = 16.0
        mock.period_pip = PipDuration.from_seconds(1.0 / 16.0)
        mock.unit = "counts"
        mock.data = np.array([1.0, 2.0, 3.0, 4.0])
        mock.start_gps_pip = PipInstant.from_gpst_seconds(1000000000)
        mock.real_end_gps_pip = PipInstant.from_gpst_seconds(1000000000.25)
        mock.end_gps_pip.return_value = PipInstant.from_gpst_seconds(1000000000.25)
        mock.delta_t_seconds = MagicMock(
            return_value=np.array([0.0, 0.0625, 0.125, 0.1875])
        )
        return mock

    def test_data_buffer_from_time_domain_array(self, mock_time_domain_array):
        """DataBuffer should correctly initialize from TimeDomainArray"""
        buf = DataBuffer(mock_time_domain_array)

        assert buf.sample_rate == 16.0
        assert buf.unit == "counts"
        assert len(buf) == 4
        np.testing.assert_array_equal(buf.data, np.array([1.0, 2.0, 3.0, 4.0]))

    def test_data_buffer_clone(self, mock_time_domain_array):
        """DataBuffer should correctly clone from another DataBuffer"""
        original = DataBuffer(mock_time_domain_array)
        cloned = DataBuffer(buf=None, clone_from=original)

        assert cloned.sample_rate == original.sample_rate
        assert cloned.unit == original.unit
        assert cloned.trend == original.trend
        assert len(cloned.data) == 0  # Cloned buffer starts empty

    def test_data_buffer_requires_buf_or_clone(self):
        """DataBuffer should raise error if neither buf nor clone_from provided"""
        with pytest.raises(ValueError, match="One of buf or clone_from"):
            DataBuffer(buf=None, clone_from=None)

    def test_data_buffer_step_property(self, mock_time_domain_array):
        """step property should return sample period"""
        buf = DataBuffer(mock_time_domain_array)
        assert buf.step == pytest.approx(1.0 / 16.0)

    def test_data_buffer_is_trend_raw(self, mock_time_domain_array):
        """is_trend should return False for raw data"""
        buf = DataBuffer(mock_time_domain_array)
        assert buf.is_trend is False

    def test_data_buffer_is_trend_minute(self, mock_time_domain_array):
        """is_trend should return True for minute trend data"""
        mock_time_domain_array.id.first_channel.return_value.trend_type = (
            TrendType.Minute
        )
        buf = DataBuffer(mock_time_domain_array)
        assert buf.is_trend is True

    def test_data_buffer_is_trend_second(self, mock_time_domain_array):
        """is_trend should return True for second trend data"""
        mock_time_domain_array.id.first_channel.return_value.trend_type = (
            TrendType.Second
        )
        buf = DataBuffer(mock_time_domain_array)
        assert buf.is_trend is True

    def test_data_buffer_range_property(self, mock_time_domain_array):
        """range property should return start and end times"""
        buf = DataBuffer(mock_time_domain_array)
        start, end = buf.range
        assert start == buf.gps_start
        assert end == buf.gps_end

    def test_data_buffer_span_property(self, mock_time_domain_array):
        """span property should return duration"""
        buf = DataBuffer(mock_time_domain_array)
        span = buf.span
        assert isinstance(span, PipDuration)


class TestDataBufferDict:
    """Tests for DataBufferDict collection handling"""

    def test_empty_buffer_dict(self):
        """Empty DataBufferDict should have length 0"""
        dbd = DataBufferDict()
        assert len(dbd) == 0

    def test_buffer_dict_copy(self):
        """DataBufferDict copy should be independent"""
        dbd1 = DataBufferDict()
        # Manually add a mock buffer
        mock_channel = MagicMock()
        mock_buffer = MagicMock()
        dbd1.buffers[mock_channel] = mock_buffer

        dbd2 = DataBufferDict(copy_from=dbd1)

        assert len(dbd2) == 1
        assert mock_channel in dbd2.buffers
        # Modifying one shouldn't affect the other
        dbd1.clear()
        assert len(dbd2) == 1

    def test_buffer_dict_clear(self):
        """clear() should remove all buffers"""
        dbd = DataBufferDict()
        mock_channel = MagicMock()
        dbd.buffers[mock_channel] = MagicMock()

        dbd.clear()

        assert len(dbd) == 0

    def test_buffer_dict_contains(self):
        """__contains__ should check for channel presence"""
        dbd = DataBufferDict()
        mock_channel = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        dbd.buffers[mock_channel] = MagicMock()

        assert mock_channel in dbd
        assert ChannelTrendId(name="OTHER", trend_stat=TrendStat.Raw) not in dbd

    def test_buffer_dict_getitem(self):
        """__getitem__ should return buffer for channel"""
        dbd = DataBufferDict()
        mock_channel = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        mock_buffer = MagicMock()
        dbd.buffers[mock_channel] = mock_buffer

        assert dbd[mock_channel] is mock_buffer

    def test_buffer_dict_delitem(self):
        """__delitem__ should remove buffer for channel"""
        dbd = DataBufferDict()
        mock_channel = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        dbd.buffers[mock_channel] = MagicMock()

        del dbd[mock_channel]

        assert mock_channel not in dbd

    def test_buffer_dict_trend_property_empty(self):
        """trend property should return Raw for empty dict"""
        dbd = DataBufferDict()
        assert dbd.trend == TrendType.Raw

    def test_buffer_dict_is_trend_property_empty(self):
        """is_trend property should return False for empty dict"""
        dbd = DataBufferDict()
        assert dbd.is_trend is False

    def test_buffer_dict_range_raises_on_empty(self):
        """range property should raise ValueError on empty dict"""
        dbd = DataBufferDict()
        with pytest.raises(ValueError, match="can't get range of an empty buffer"):
            _ = dbd.range

    def test_buffer_dict_items(self):
        """items() should return buffer items"""
        dbd = DataBufferDict()
        mock_channel = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        mock_buffer = MagicMock()
        dbd.buffers[mock_channel] = mock_buffer

        items = list(dbd.items())
        assert len(items) == 1
        assert items[0] == (mock_channel, mock_buffer)

    def test_buffer_dict_values(self):
        """values() should return buffer values"""
        dbd = DataBufferDict()
        mock_buffer = MagicMock()
        dbd.buffers[ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)] = mock_buffer

        values = list(dbd.values())
        assert len(values) == 1
        assert values[0] is mock_buffer


class TestChannelTrendId:
    """Tests for ChannelTrendId identification"""

    def test_channel_trend_id_from_name(self):
        """ChannelTrendId should create from name and trend_stat"""
        ctid = ChannelTrendId(name="L1:TEST-CHANNEL", trend_stat=TrendStat.Mean)
        assert ctid.name == "L1:TEST-CHANNEL"
        assert ctid.trend_stat == TrendStat.Mean

    def test_channel_trend_id_equality(self):
        """ChannelTrendIds with same values should be equal"""
        ctid1 = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        ctid2 = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        assert ctid1 == ctid2

    def test_channel_trend_id_inequality_name(self):
        """ChannelTrendIds with different names should not be equal"""
        ctid1 = ChannelTrendId(name="TEST1", trend_stat=TrendStat.Raw)
        ctid2 = ChannelTrendId(name="TEST2", trend_stat=TrendStat.Raw)
        assert ctid1 != ctid2

    def test_channel_trend_id_inequality_trend_stat(self):
        """ChannelTrendIds with different trend_stats should not be equal"""
        ctid1 = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        ctid2 = ChannelTrendId(name="TEST", trend_stat=TrendStat.Mean)
        assert ctid1 != ctid2

    def test_channel_trend_id_hashable(self):
        """ChannelTrendId should be hashable for use as dict key"""
        ctid = ChannelTrendId(name="TEST", trend_stat=TrendStat.Raw)
        # Should not raise
        d = {ctid: "value"}
        assert d[ctid] == "value"


class TestTemplateDataFlow:
    """Tests for template to data flow"""

    def test_template_extract_channels_single_plot(self):
        """template_extract_channels should extract all channel names"""
        template._CHANNEL_COLORS = {}
        t = template._new_template(
            plots=[
                {"channels": {"CHAN1": {}, "CHAN2": {}}},
            ]
        )

        channels = template.template_extract_channels(t)

        assert channels == {"CHAN1", "CHAN2"}

    def test_template_extract_channels_multiple_plots(self):
        """template_extract_channels should extract from all plots"""
        template._CHANNEL_COLORS = {}
        t = template._new_template(
            plots=[
                {"channels": {"CHAN1": {}}},
                {"channels": {"CHAN2": {}, "CHAN3": {}}},
            ]
        )

        channels = template.template_extract_channels(t)

        assert channels == {"CHAN1", "CHAN2", "CHAN3"}

    def test_template_extract_channels_empty(self):
        """template_extract_channels should handle empty template"""
        template._CHANNEL_COLORS = {}
        t = template._new_template(plots=[])

        channels = template.template_extract_channels(t)

        assert channels == set()

    def test_get_channel_color_assigns_unique_colors(self):
        """get_channel_color should assign unique colors to different channels"""
        template._CHANNEL_COLORS = {}

        color1 = template.get_channel_color("CHAN1")
        color2 = template.get_channel_color("CHAN2")
        color3 = template.get_channel_color("CHAN3")

        assert color1 != color2
        assert color2 != color3
        assert color1 != color3

    def test_get_channel_color_preserves_assigned(self):
        """get_channel_color should return same color for same channel"""
        template._CHANNEL_COLORS = {}

        color1 = template.get_channel_color("CHAN1")
        color2 = template.get_channel_color("CHAN1")

        assert color1 == color2

    def test_get_channel_color_respects_explicit(self):
        """get_channel_color should use explicit color when provided"""
        template._CHANNEL_COLORS = {}

        color = template.get_channel_color("CHAN1", color="#ff0000")

        assert color == "#ff0000"


class TestTrendTransitions:
    """Tests for trend type transitions based on time window"""

    def test_trend_thresholds_defined(self):
        """Trend transition thresholds should be defined"""
        from .. import const

        assert "raw/sec" in const.TREND_TRANS_THRESHOLD
        assert "sec/min" in const.TREND_TRANS_THRESHOLD

    def test_raw_sec_threshold(self):
        """raw/sec threshold should be 120 seconds"""
        from .. import const

        threshold = const.TREND_TRANS_THRESHOLD["raw/sec"]
        assert threshold.to_sec() == 120

    def test_sec_min_threshold(self):
        """sec/min threshold should be 3600 seconds (1 hour)"""
        from .. import const

        threshold = const.TREND_TRANS_THRESHOLD["sec/min"]
        assert threshold.to_sec() == 3600

    def test_trend_max_seconds_increasing(self):
        """Max seconds should increase: raw < second < minute"""
        from .. import const

        assert (
            const.TREND_MAX_SECONDS[TrendType.Raw]
            < const.TREND_MAX_SECONDS[TrendType.Second]
        )
        assert (
            const.TREND_MAX_SECONDS[TrendType.Second]
            < const.TREND_MAX_SECONDS[TrendType.Minute]
        )


class TestNDSChannelParsing:
    """Tests for NDS channel string parsing"""

    def test_parse_simple_channel(self):
        """Should parse simple channel name"""
        from ..nds import _parse_channel_string

        name, ctype, mod = _parse_channel_string("L1:TEST-CHANNEL")

        assert name == "L1:TEST-CHANNEL"
        assert ctype == "raw"
        assert mod == "raw"

    def test_parse_channel_with_mod(self):
        """Should parse channel with trend modifier"""
        from ..nds import _parse_channel_string

        name, ctype, mod = _parse_channel_string("L1:TEST-CHANNEL.mean")

        assert name == "L1:TEST-CHANNEL"
        assert ctype == "raw"
        assert mod == "mean"

    def test_parse_channel_with_ctype(self):
        """Should parse channel with channel type"""
        from ..nds import _parse_channel_string

        name, ctype, mod = _parse_channel_string("L1:TEST-CHANNEL,s-trend")

        assert name == "L1:TEST-CHANNEL"
        assert ctype == "s-trend"
        assert mod == "raw"

    def test_parse_channel_with_mod_and_ctype(self):
        """Should parse channel with both modifier and type"""
        from ..nds import _parse_channel_string

        name, ctype, mod = _parse_channel_string("L1:TEST-CHANNEL.mean,s-trend")

        assert name == "L1:TEST-CHANNEL"
        assert ctype == "s-trend"
        assert mod == "mean"


class TestFakeDataSource:
    """Tests for the fake data source used in testing"""

    def test_fake_channel_source_generates_data(self):
        """FakeChannelSource should generate reproducible data"""
        from ..nds import FakeChannelSource

        source = FakeChannelSource("TEST", sample_rate=16, unit="counts")

        assert source.name == "TEST"
        assert source.sample_rate == 16
        assert source.unit == "counts"

    def test_fake_source_gen_bufs(self):
        """FakeSource should generate buffer list"""
        from ..nds import FAKE_SOURCE

        bufs = FAKE_SOURCE.gen_bufs(["T1:A-B"], start=1000000000, stride=1)

        assert len(bufs) == 1
        assert bufs[0].channel.name == "T1:A-B"

    def test_fake_fetch(self):
        """fake_fetch should return buffers for requested channels"""
        from ..nds import fake_fetch

        bufs = fake_fetch(
            channels=["T1:A-B", "T1:B-C"], gps_start=1000000000, gps_stop=1000000001
        )

        assert len(bufs) == 2

    def test_fake_find_channels(self):
        """fake_find_channels should return channel list"""
        from ..nds import fake_find_channels

        channels = fake_find_channels()

        assert len(channels) > 0
        assert all(hasattr(c, "name") for c in channels)
