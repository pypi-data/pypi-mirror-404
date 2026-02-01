# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025-2026 Maurice Garcia

from __future__ import annotations

import math
from enum import IntEnum

from pypnm.lib.types import FloatSeries


class ChannelPower:

    @staticmethod
    def calculate_channel_power(dB_values: FloatSeries) -> float:
        """
        Calculate the total channel power.

        Args:
            dB_values (FloatSeries): Series of dB values.

        Returns:
            float: Total channel power in dB.
        """
        d_total_antilog = 0.0

        # Convert to Anti-Log and summation
        for d in dB_values:
            d_total_antilog += ChannelPower.to_antilog(d)

        return ChannelPower.to_log_10(d_total_antilog)

    @staticmethod
    def to_antilog(log: float) -> float:
        """
        Convert a logarithmic value to its anti-logarithmic equivalent.

        Args:
            log (float): Logarithmic value.

        Returns:
            float: Anti-logarithmic value.
        """
        return 10 ** (log / 10.0)

    @staticmethod
    def to_log_10(anti_log: float) -> float:
        """
        Convert an anti-logarithmic value to its logarithmic equivalent.

        Args:
            anti_log (float): Anti-logarithmic value.

        Returns:
            float: Logarithmic value.
        """
        return math.log10(anti_log)


class ChannelPowerDbmv:

    class ImpedanceOhm(IntEnum):
        FIFTY = 50
        SEVENTY_FIVE = 75

    _DBMV_TO_DBMW_OFFSET_75_OHM = 48.75
    _DBMV_TO_DBMW_OFFSET_50_OHM = 47.0

    @staticmethod
    def calculate_channel_power_dbmv(
        dBmv_values: FloatSeries,
        impedance_ohm: ImpedanceOhm = ImpedanceOhm.SEVENTY_FIVE,
    ) -> float:
        """
        Calculate total channel power from per-bin dBmV values.

        Args:
            dBmv_values (FloatSeries): Per-bin power values in dBmV.
            impedance_ohm (int): Reference impedance for dBmV conversion.

        Returns:
            float: Total channel power in dBmV.
        """
        offset = ChannelPowerDbmv._get_dbmv_offset(impedance_ohm)
        total_mw = 0.0

        for d_bmv in dBmv_values:
            total_mw += 10 ** ((d_bmv - offset) / 10.0)

        if total_mw <= 0.0:
            return float("-inf")

        return (10.0 * math.log10(total_mw)) + offset

    @staticmethod
    def _get_dbmv_offset(impedance_ohm: ImpedanceOhm) -> float:
        """
        Get the dBmV to dBm offset based on impedance.

        Args:
            impedance_ohm (int): Reference impedance for dBmV conversion.

        Returns:
            float: Offset applied to convert between dBmV and dBm.
        """
        match impedance_ohm:
            case ChannelPowerDbmv.ImpedanceOhm.SEVENTY_FIVE:
                return ChannelPowerDbmv._DBMV_TO_DBMW_OFFSET_75_OHM
            case ChannelPowerDbmv.ImpedanceOhm.FIFTY:
                return ChannelPowerDbmv._DBMV_TO_DBMW_OFFSET_50_OHM
            case _:
                raise ValueError(f"Unsupported impedance: {impedance_ohm}")
