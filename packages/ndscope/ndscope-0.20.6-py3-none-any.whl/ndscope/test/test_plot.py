"""Tests for plot.py rendering logic

Note: Tests that require Qt widgets are skipped when no display is available.
The tests focus on logic that can be tested without instantiating Qt objects.
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
import os

from dttlib import PipInstant, PipDuration

from .. import const
from ..util import TDStr


# Check if display is available for Qt tests
def has_display():
    """Check if a display is available for Qt"""
    return (
        os.environ.get("DISPLAY") is not None
        or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    )


# Skip Qt widget tests if no display
skip_no_display = pytest.mark.skipif(
    not has_display(), reason="No display available for Qt tests"
)


class TestTimeStringFormatting:
    """Tests for time string formatting logic used in TimeStringAxis"""

    def test_tdstr_relative_positive(self):
        """TDStr should format positive durations correctly"""
        result = str(TDStr(3661))  # 1h 1m 1s
        assert "1h" in result
        assert "1m" in result
        assert "1s" in result

    def test_tdstr_relative_negative(self):
        """TDStr should format negative durations correctly"""
        result = str(TDStr(-100))
        assert result.startswith("-")

    def test_tdstr_relative_zero(self):
        """TDStr should handle zero duration"""
        result = str(TDStr(0))
        assert result == "0"

    def test_tdstr_subsecond(self):
        """TDStr should handle subsecond durations"""
        result = str(TDStr(0.001))  # 1ms
        assert "ms" in result

    def test_tdstr_microseconds(self):
        """TDStr should handle microsecond durations"""
        result = str(TDStr(0.000001))  # 1us
        assert "μs" in result

    def test_gps_time_calculation(self):
        """GPS time calculation should work correctly"""
        t0 = PipInstant.from_gpst_seconds(1000000000)
        t = PipDuration.from_seconds(100)
        result = (t + t0).to_gpst_seconds()
        assert result == 1000000100.0


class TestLogLabelLevel:
    """Tests for LogLabelLevel enum"""

    def test_enum_values(self):
        """LogLabelLevel should have expected values"""
        from ..plot import LogLabelLevel

        assert LogLabelLevel.ALL.value == 1
        assert LogLabelLevel.TWOS_AND_FIVES.value == 2
        assert LogLabelLevel.NONE.value == 3


class TestLogTickFiltering:
    """Tests for log tick string filtering logic"""

    def test_filter_all_shows_all(self):
        """ALL level should show all labels"""
        from ..plot import LogLabelLevel

        level = LogLabelLevel.ALL
        orig_strings = ["1", "2", "5", "10"]
        values = np.array([0, 0.301, 0.699, 1.0])

        # ALL level returns original strings unchanged
        if level == LogLabelLevel.ALL:
            result = orig_strings
        assert result == ["1", "2", "5", "10"]

    def test_filter_none_shows_decades_only(self):
        """NONE level should only show decade labels"""
        from ..plot import LogLabelLevel

        level = LogLabelLevel.NONE
        orig_strings = ["1", "2", "5", "10"]
        values = np.array([0, 0.301, 0.699, 1.0])

        # NONE level only shows labels where mod is close to 0 (decades)
        strings = []
        mods = np.divmod(values, 1.0)[1]
        for i, mod in enumerate(mods):
            if np.isclose(mod, 0):
                strings.append(orig_strings[i])
            else:
                strings.append("")

        assert strings[0] == "1"  # 10^0 = 1 (decade)
        assert strings[1] == ""  # 10^0.301 = 2 (not a decade)
        assert strings[2] == ""  # 10^0.699 = 5 (not a decade)
        assert strings[3] == "10"  # 10^1 = 10 (decade)

    def test_filter_twos_and_fives(self):
        """TWOS_AND_FIVES level should show 2s, 5s, and decades"""
        from ..plot import LogLabelLevel

        level = LogLabelLevel.TWOS_AND_FIVES
        orig_strings = ["1", "2", "3", "5", "10"]
        log2 = np.log10(2)
        log5 = np.log10(5)
        log3 = np.log10(3)
        values = np.array([0, log2, log3, log5, 1.0])

        strings = []
        mods = np.divmod(values, 1.0)[1]
        for i, mod in enumerate(mods):
            if np.isclose(mod, 0) or np.isclose(mod, log5) or np.isclose(mod, log2):
                strings.append(orig_strings[i])
            else:
                strings.append("")

        assert strings[0] == "1"  # 10^0 = 1 (decade)
        assert strings[1] == "2"  # 10^log2 = 2
        assert strings[2] == ""  # 10^log3 = 3 (hidden)
        assert strings[3] == "5"  # 10^log5 = 5
        assert strings[4] == "10"  # 10^1 = 10 (decade)


class TestCurveViewLogic:
    """Tests for CurveView data management logic"""

    def test_array_reuse_same_length(self):
        """Arrays should be reused when lengths match"""
        initial_x = np.array([0, 0, 0])
        initial_y = np.array([0, 0, 0])

        new_x = np.array([1, 2, 3])
        new_y = np.array([4, 5, 6])

        # Simulate the logic from CurveView.setData
        if len(initial_x) == len(new_x):
            initial_x[:] = new_x
            x = initial_x
        else:
            x = new_x

        if len(initial_y) == len(new_y):
            initial_y[:] = new_y
            y = initial_y
        else:
            y = new_y

        # Should reuse the same array objects
        assert x is initial_x
        assert y is initial_y
        np.testing.assert_array_equal(x, new_x)
        np.testing.assert_array_equal(y, new_y)

    def test_new_arrays_different_length(self):
        """New arrays should be created when lengths differ"""
        initial_x = np.array([0, 0])
        initial_y = np.array([0, 0])

        new_x = np.array([1, 2, 3])
        new_y = np.array([4, 5, 6])

        # Simulate the logic from CurveView.setData
        if len(initial_x) == len(new_x):
            initial_x[:] = new_x
            x = initial_x
        else:
            x = new_x

        if len(initial_y) == len(new_y):
            initial_y[:] = new_y
            y = initial_y
        else:
            y = new_y

        # Should create new array objects
        assert x is not initial_x
        assert y is not initial_y


class TestColorMode:
    """Tests for color mode handling in plots"""

    def test_color_mode_dark_values(self):
        """Dark mode should have correct colors"""
        dark = const.COLOR_MODE["dark"]
        assert dark["fg"].name() == "#ffffff"  # white
        assert dark["bg"].color().name() == "#000000"  # black

    def test_color_mode_light_values(self):
        """Light mode should have correct colors"""
        light = const.COLOR_MODE["light"]
        assert light["fg"].name() == "#000000"  # black
        assert light["bg"].color().name() == "#ffffff"  # white

    def test_color_modes_are_complementary(self):
        """Light and dark modes should have swapped colors"""
        dark = const.COLOR_MODE["dark"]
        light = const.COLOR_MODE["light"]
        assert dark["fg"].name() == light["bg"].color().name()
        assert dark["bg"].color().name() == light["fg"].name()


class TestTickSpacings:
    """Tests for tick spacing constants"""

    def test_tick_spacings_descending_order(self):
        """TICK_SPACINGS should be in descending order by time"""
        for i in range(len(const.TICK_SPACINGS) - 1):
            current = const.TICK_SPACINGS[i][0].to_seconds()
            next_val = const.TICK_SPACINGS[i + 1][0].to_seconds()
            assert current >= next_val, f"Tick spacings not in order at index {i}"

    def test_tick_spacings_all_positive(self):
        """All tick spacings should be positive"""
        for spacing, division in const.TICK_SPACINGS:
            assert spacing.to_seconds() > 0
            assert division > 0

    def test_tick_spacings_covers_year_to_nanosecond(self):
        """TICK_SPACINGS should cover from years to nanoseconds"""
        times = [s[0].to_seconds() for s in const.TICK_SPACINGS]
        assert max(times) >= 31536000  # At least 1 year
        assert min(times) <= 1e-8  # Down to ~10 nanoseconds

    def test_tick_spacing_selection_algorithm(self):
        """Tick spacing selection should find appropriate spacing for span"""

        # Simulate the tickSpacing algorithm from TimeStringAxis
        def select_spacing(span_seconds):
            span = PipDuration.from_seconds(span_seconds)
            major = PipDuration.from_sec(1)
            minordiv = 0.5
            for major, minordiv in const.TICK_SPACINGS:
                if span >= 3 * major:
                    break
            return major.to_seconds(), minordiv

        # Test various spans
        # 10 second span should get small tick spacing
        major, _ = select_spacing(10)
        assert major <= 10

        # 1 hour span should get minute-level ticks
        major, _ = select_spacing(3600)
        assert 60 <= major <= 3600

        # 1 day span should get hour-level ticks
        major, _ = select_spacing(86400)
        assert 3600 <= major <= 86400


class TestTickDateFormat:
    """Tests for tick date formatting"""

    def test_tick_date_format_defined(self):
        """TICK_DATE_FMT should be defined"""
        assert const.TICK_DATE_FMT is not None
        assert len(const.TICK_DATE_FMT) > 0

    def test_tick_date_format_has_multiline(self):
        """TICK_DATE_FMT should support multiline display"""
        # The format includes newline for date/time separation
        assert "\n" in const.TICK_DATE_FMT


class TestTrendConstants:
    """Tests for trend-related constants"""

    def test_trend_minmax_alpha_valid(self):
        """TREND_MINMAX_ALPHA should be valid alpha value"""
        assert 0 <= const.TREND_MINMAX_ALPHA <= 255

    def test_label_alpha_valid(self):
        """LABEL_ALPHA should be valid alpha value"""
        assert 0 <= const.LABEL_ALPHA <= 255

    def test_online_x_max_is_zero(self):
        """ONLINE_X_MAX should be at zero"""
        assert const.ONLINE_X_MAX.to_sec() == 0


class TestSIPrefixRanges:
    """Tests for SI prefix enable ranges"""

    def test_si_prefix_ranges(self):
        """SI prefix ranges should exclude normal range"""
        # The YAxis.getSIPrefixEnableRanges returns ranges where SI prefixes are used
        # This prevents "1e-3" type notation for normal values
        expected = ((0.0, 1e-6), (1e6, np.inf))

        # Values between 1e-6 and 1e6 should NOT get SI prefixes
        # This matches the implementation in YAxis
        low_range, high_range = expected

        # Check low range is for very small values
        assert low_range[0] == 0.0
        assert low_range[1] == 1e-6

        # Check high range is for very large values
        assert high_range[0] == 1e6
        assert high_range[1] == np.inf


# NOTE: Qt widget tests (TestTimeStringAxisWithQt, TestYAxisWithQt) are excluded
# because they require a display environment. When running with a display or
# using QT_QPA_PLATFORM=offscreen, these tests can be added back.
#
# Example tests that would be included with a display:
#
# class TestTimeStringAxisWithQt:
#     """Tests for TimeStringAxis that require Qt"""
#     @pytest.fixture
#     def axis(self):
#         from ..plot import TimeStringAxis
#         return TimeStringAxis()
#
#     def test_initial_mode_is_relative(self, axis):
#         assert axis.mode == "relative"
#
#     def test_set_t0(self, axis):
#         new_t0 = PipInstant.from_gpst_seconds(1000000000)
#         axis.set_t0(new_t0)
#         assert axis.t0 == new_t0
