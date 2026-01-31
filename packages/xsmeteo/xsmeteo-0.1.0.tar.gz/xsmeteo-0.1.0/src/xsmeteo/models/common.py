from __future__ import annotations

from enum import StrEnum


class TemperatureUnit(StrEnum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WindSpeedUnit(StrEnum):
    KMH = "kmh"
    MS = "ms"
    MPH = "mph"
    KN = "kn"


class PrecipitationUnit(StrEnum):
    MM = "mm"
    INCH = "inch"


class TimeFormat(StrEnum):
    ISO8601 = "iso8601"
    UNIXTIME = "unixtime"
