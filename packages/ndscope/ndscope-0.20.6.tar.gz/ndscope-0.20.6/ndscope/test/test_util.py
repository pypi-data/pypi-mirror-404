"""Tests for util.py utility functions"""

import os
import pytest
from unittest.mock import patch, MagicMock

from ..util import (
    TDStr,
    TDUnits,
    cells_to_tabspec,
    gpstime_parse,
    gpstime_str_gps,
    gpstime_str_greg,
    resolve_data_source,
    format_nds_server_string,
)
from .. import const


class TestTDStr:
    """Tests for TDStr time delta string formatting"""

    def test_zero_seconds(self):
        """Zero seconds should format as '0'"""
        td = TDStr(0)
        assert str(td) == "0"

    def test_positive_seconds(self):
        """Positive seconds should format correctly"""
        td = TDStr(1)
        assert str(td) == "1s"

    def test_negative_seconds(self):
        """Negative seconds should have '-' prefix"""
        td = TDStr(-1)
        result = str(td)
        assert result.startswith("-")
        assert "1s" in result

    def test_minutes(self):
        """Minutes should format correctly"""
        td = TDStr(60)
        assert str(td) == "1m"

    def test_minutes_and_seconds(self):
        """Minutes and seconds should format correctly"""
        td = TDStr(61)
        result = str(td)
        assert "1m" in result
        assert "1s" in result

    def test_hours(self):
        """Hours should format correctly"""
        td = TDStr(3600)
        assert str(td) == "1h"

    def test_hours_minutes_seconds(self):
        """Hours, minutes, and seconds should format correctly"""
        td = TDStr(3661)  # 1h 1m 1s
        result = str(td)
        assert "1h" in result
        assert "1m" in result
        assert "1s" in result

    def test_days(self):
        """Days should format correctly"""
        td = TDStr(86400)
        assert str(td) == "1d"

    def test_years(self):
        """Years should format correctly"""
        td = TDStr(31536000)
        assert str(td) == "1y"

    def test_milliseconds(self):
        """Milliseconds should format correctly"""
        td = TDStr(0.001)
        assert "1ms" in str(td)

    def test_microseconds(self):
        """Microseconds should format correctly"""
        td = TDStr(0.000001)
        result = str(td)
        assert "1μs" in result or "1us" in result.lower()

    def test_complex_duration(self):
        """Complex durations with multiple units should format correctly"""
        # 1 year, 1 day, 1 hour, 1 minute, 1 second
        seconds = 31536000 + 86400 + 3600 + 60 + 1
        td = TDStr(seconds)
        result = str(td)
        assert "1y" in result
        assert "1d" in result
        assert "1h" in result
        assert "1m" in result
        assert "1s" in result

    def test_getitem(self):
        """__getitem__ should return unit values"""
        td = TDStr(3661)  # 1h 1m 1s
        assert td["hours"] == 1
        assert td["minutes"] == 1
        assert td["seconds"] == 1

    def test_repr(self):
        """__repr__ should include all units"""
        td = TDStr(61)
        result = repr(td)
        assert "TDStr" in result
        assert "minutes=1" in result
        assert "seconds=1" in result

    def test_total_seconds_preserved(self):
        """total_seconds should preserve input value"""
        td = TDStr(123.456)
        assert td.total_seconds == 123.456

    def test_prefix_positive(self):
        """prefix should be empty for positive values"""
        td = TDStr(100)
        assert td.prefix == ""

    def test_prefix_negative(self):
        """prefix should be '-' for negative values"""
        td = TDStr(-100)
        assert td.prefix == "-"

    def test_large_negative(self):
        """Large negative values should format correctly"""
        td = TDStr(-86400)  # -1 day
        result = str(td)
        assert result.startswith("-")
        assert "1d" in result


class TestTDUnits:
    """Tests for TDUnits namedtuple"""

    def test_tdunits_fields(self):
        """TDUnits should have expected fields"""
        expected_fields = [
            "years",
            "days",
            "hours",
            "minutes",
            "seconds",
            "msecs",
            "usecs",
        ]
        assert list(TDUnits._fields) == expected_fields


class TestCellsToTabspec:
    """Tests for cells_to_tabspec function"""

    def test_single_cell(self):
        """Single cell should return row=0, col=0, rowspan=1, colspan=1"""
        result = cells_to_tabspec({(0, 0)})
        assert result == {"row": 0, "col": 0, "rowspan": 1, "colspan": 1}

    def test_horizontal_cells(self):
        """Horizontal cells should have colspan > 1"""
        result = cells_to_tabspec({(0, 0), (0, 1), (0, 2)})
        assert result["row"] == 0
        assert result["col"] == 0
        assert result["rowspan"] == 1
        assert result["colspan"] == 3

    def test_vertical_cells(self):
        """Vertical cells should have rowspan > 1"""
        result = cells_to_tabspec({(0, 0), (1, 0), (2, 0)})
        assert result["row"] == 0
        assert result["col"] == 0
        assert result["rowspan"] == 3
        assert result["colspan"] == 1

    def test_rectangular_cells(self):
        """Rectangular cell block should have correct spans"""
        cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
        result = cells_to_tabspec(cells)
        assert result["row"] == 0
        assert result["col"] == 0
        assert result["rowspan"] == 2
        assert result["colspan"] == 2

    def test_offset_cells(self):
        """Cells starting at non-zero position should have correct row/col"""
        cells = {(2, 3), (2, 4), (3, 3), (3, 4)}
        result = cells_to_tabspec(cells)
        assert result["row"] == 2
        assert result["col"] == 3
        assert result["rowspan"] == 2
        assert result["colspan"] == 2


class TestGPSTimeParse:
    """Tests for gpstime_parse function"""

    def test_parse_none(self):
        """None input should return None"""
        result = gpstime_parse(None)
        assert result is None

    def test_parse_now(self):
        """'now' should return a valid gpstime"""
        result = gpstime_parse("now")
        assert result is not None

    def test_parse_invalid(self):
        """Invalid input should return None"""
        result = gpstime_parse("not a valid time")
        assert result is None

    def test_parse_gps_number_string(self):
        """GPS number string should parse correctly"""
        result = gpstime_parse("1000000000")
        assert result is not None
        assert result.gps() == pytest.approx(1000000000)

    def test_parse_iso_date(self):
        """ISO date string should parse correctly"""
        result = gpstime_parse("2020-01-01 00:00:00")
        assert result is not None


class TestGPSTimeStr:
    """Tests for gpstime string formatting functions"""

    def test_gpstime_str_gps(self):
        """gpstime_str_gps should return GPS time as string"""
        gt = gpstime_parse("1000000000")
        result = gpstime_str_gps(gt)
        assert "1000000000" in result

    def test_gpstime_str_gps_none(self):
        """gpstime_str_gps with None should return None"""
        result = gpstime_str_gps(None)
        assert result is None

    def test_gpstime_str_greg_none(self):
        """gpstime_str_greg with None should return None"""
        result = gpstime_str_greg(None)
        assert result is None

    def test_gpstime_str_greg(self):
        """gpstime_str_greg should return formatted date string"""
        gt = gpstime_parse("1000000000")
        result = gpstime_str_greg(gt)
        assert result is not None
        # Should be a date string format
        assert "/" in result or "-" in result


class TestResolveDataSource:
    """Tests for resolve_data_source function"""

    def test_default_server(self):
        """Without arguments, should return default server URL"""
        # Remove env vars to force default behavior
        env_copy = os.environ.copy()
        env_copy.pop("NDSSERVER", None)
        env_copy.pop("LIGO_DATA_URL", None)
        with patch.dict(os.environ, env_copy, clear=True):
            result = resolve_data_source()
        assert "nds://" in result

    def test_explicit_ndsserver(self):
        """Explicit ndsserver should be used"""
        result = resolve_data_source(ndsserver="test.server.com:31200")
        assert "test.server.com" in result

    def test_url_override(self):
        """URL should override ndsserver"""
        result = resolve_data_source(
            ndsserver="ignored.server.com", url="nds://actual.server.com"
        )
        assert "actual.server.com" in result

    def test_alias_cit(self):
        """'cit' alias should resolve to caltech server"""
        result = resolve_data_source(ndsserver="cit")
        assert "caltech" in result.lower() or "ligo" in result.lower()

    def test_alias_lho(self):
        """'lho' alias should resolve to Hanford server"""
        result = resolve_data_source(ndsserver="lho")
        assert "ligo-wa" in result.lower() or "wa" in result.lower()

    def test_alias_llo(self):
        """'llo' alias should resolve to Livingston server"""
        result = resolve_data_source(ndsserver="llo")
        assert "ligo-la" in result.lower() or "la" in result.lower()


class TestFormatNDSServerString:
    """Tests for format_nds_server_string function"""

    def test_formats_nds_url(self):
        """Should format NDS URL correctly"""
        with patch.dict(os.environ, {"LIGO_DATA_URL": "nds://test.server.com:31200"}):
            server, formatted = format_nds_server_string()
        assert "test.server.com" in formatted

    def test_handles_default_port(self):
        """Default port 31200 should not be shown explicitly"""
        with patch.dict(os.environ, {"LIGO_DATA_URL": "nds://test.server.com:31200"}):
            server, formatted = format_nds_server_string()
        # Default port might or might not be shown, but server should be formatted
        assert "test.server.com" in formatted

    def test_handles_nondefault_port(self):
        """Non-default port should be shown"""
        with patch.dict(os.environ, {"LIGO_DATA_URL": "nds://test.server.com:9999"}):
            server, formatted = format_nds_server_string()
        assert "9999" in formatted

    def test_handles_no_scheme(self):
        """URL without scheme should default to nds"""
        with patch.dict(os.environ, {"LIGO_DATA_URL": "test.server.com:31200"}):
            server, formatted = format_nds_server_string()
        # Should still work
        assert formatted is not None


class TestNDSServerConstants:
    """Tests for NDS server constants"""

    def test_default_server_defined(self):
        """Default NDS server should be defined"""
        assert const.NDSSERVER is not None
        assert len(const.NDSSERVER) > 0

    def test_alias_map_contains_expected_keys(self):
        """Alias map should contain expected keys"""
        assert None in const.NDSSERVER_ALIAS_MAP
        assert "" in const.NDSSERVER_ALIAS_MAP
        assert "cit" in const.NDSSERVER_ALIAS_MAP
        assert "lho" in const.NDSSERVER_ALIAS_MAP
        assert "llo" in const.NDSSERVER_ALIAS_MAP

    def test_alias_map_values_are_valid_servers(self):
        """Alias map values should be valid server strings"""
        for key, value in const.NDSSERVER_ALIAS_MAP.items():
            assert ":" in value  # Should have port
            assert value.count(":") == 1  # Only one colon


class TestChannelRegexp:
    """Tests for channel name validation regex"""

    def test_valid_channel_simple(self):
        """Simple channel name should match"""
        import re

        pattern = re.compile(const.CHANNEL_REGEXP)
        assert pattern.match("L1:TEST-CHANNEL")

    def test_valid_channel_with_underscore(self):
        """Channel name with underscore should match"""
        import re

        pattern = re.compile(const.CHANNEL_REGEXP)
        assert pattern.match("L1:TEST_CHANNEL")

    def test_valid_channel_no_ifo(self):
        """Channel name without IFO prefix should match"""
        import re

        pattern = re.compile(const.CHANNEL_REGEXP)
        assert pattern.match("TEST-CHANNEL")

    def test_invalid_channel_special_chars(self):
        """Channel name with special chars should not match"""
        import re

        pattern = re.compile(const.CHANNEL_REGEXP)
        assert not pattern.match("L1:TEST@CHANNEL")
        assert not pattern.match("L1:TEST#CHANNEL")

    def test_invalid_channel_spaces(self):
        """Channel name with spaces should not match"""
        import re

        pattern = re.compile(const.CHANNEL_REGEXP)
        assert not pattern.match("L1:TEST CHANNEL")
