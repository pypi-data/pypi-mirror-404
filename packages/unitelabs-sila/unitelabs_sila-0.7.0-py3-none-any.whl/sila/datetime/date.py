import datetime

import typing_extensions as typing


class date(datetime.date):
    """Date with time zone."""

    __slots__ = "_day", "_hashcode", "_month", "_tzinfo", "_year"

    def __new__(
        cls,
        year: int | str | bytes,
        month: int | None = None,
        day: int | None = None,
        tzinfo: datetime.tzinfo | None = None,
    ):
        """
        Create a new date with the given year, month, day and timezone.

        Args:
          year: The year of the date.
          month: The month of the date.
          day: The day of the date.
          tzinfo: The timezone of the date.

        Returns:
          A new date with the given year, month, day and timezone.
        """

        if isinstance(year, bytes) and len(year) == 4 and 1 <= ord(year[2:3]) <= 12:
            self = datetime.date.__new__(cls, year)  # type: ignore
            self._setstate(year, month)
            self._hashcode = -1
            return self

        self = datetime.date.__new__(cls, year=year, month=month, day=day)  # type: ignore
        self._year = year
        self._month = month
        self._day = day
        self._hashcode = -1
        _check_tzinfo_arg(tzinfo)
        self._tzinfo = tzinfo
        return self

    def replace(
        self,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        tzinfo: None | bool | datetime.tzinfo = True,
    ) -> typing.Self:
        """
        Return a new date with new values for the specified fields.

        Args:
          year: The year of the date.
          month: The month of the date.
          day: The day of the date.
          tzinfo: The timezone of the date.

        Returns:
          A new date with the given year, month, day and timezone.
        """

        if year is None:
            year = self._year or 0
        if month is None:
            month = self._month
        if day is None:
            day = self._day

        _tzinfo: datetime.tzinfo | None = None
        if tzinfo is True:
            _tzinfo = self.tzinfo
        elif isinstance(tzinfo, datetime.tzinfo):
            _tzinfo = tzinfo

        return type(self)(year, month, day, _tzinfo)

    # Read-only field accessors

    @property
    def tzinfo(self) -> datetime.tzinfo | None:
        """Timezone info object."""

        return self._tzinfo

    def utcoffset(self) -> datetime.timedelta | None:
        """Get the timezone offset as timedelta positive east of UTC (negative west of UTC)."""

        if self._tzinfo is None:
            return None

        return self._tzinfo.utcoffset(datetime.datetime(self._year, self._month, self._day, tzinfo=self._tzinfo))

    # Comparisons of date objects with other.

    @typing.override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) == 0
        return NotImplemented

    @typing.override
    def __ne__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) != 0
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) <= 0
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) < 0
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) >= 0
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, date):
            return self._cmp(other) > 0
        return NotImplemented

    def _cmp(self, other: "date") -> int:
        assert isinstance(other, date)
        y, m, d, tz = self.year, self.month, self.day, self.tzinfo
        y2, m2, d2, tz2 = other.year, other.month, other.day, other.tzinfo

        offset1 = (tz or datetime.timezone.utc).utcoffset(None) or datetime.timedelta(0)
        offset2 = (tz2 or datetime.timezone.utc).utcoffset(None) or datetime.timedelta(0)

        return _cmp((y, m, d + offset1.days, offset1.seconds), (y2, m2, d2 + offset2.days, offset2.seconds))

    # Pickle support.

    def _getstate(self) -> tuple[bytes] | tuple[bytes, datetime.tzinfo]:
        yhi, ylo = divmod(self._year, 256)
        basestate = bytes([yhi, ylo, self._month, self._day])
        if self._tzinfo is None:
            return (basestate,)
        return (basestate, self._tzinfo)

    def _setstate(self, string: bytes, tzinfo: datetime.tzinfo | None) -> None:
        if tzinfo is not None and not isinstance(tzinfo, datetime.tzinfo):
            msg = "bad tzinfo state arg"
            raise TypeError(msg)

        yhi, ylo, self._month, self._day = string
        self._year = yhi * 256 + ylo
        self._tzinfo = tzinfo

    def __reduce__(self):
        return (self.__class__, self._getstate())

    def __repr__(self):
        """
        Convert to formal string, for repr().

        >>> dt = datetime(2010, 1, 1)
        >>> repr(dt)
        'datetime.datetime(2010, 1, 1, 0, 0)'

        >>> dt = datetime(2010, 1, 1, tzinfo=timezone.utc)
        >>> repr(dt)
        'datetime.datetime(2010, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)'
        """
        return (
            f"{self.__class__.__module__}.{self.__class__.__qualname__}"
            f"({self._year}, {self._month}, {self._day}, tzinfo={self._tzinfo!r})"
        )

    def isoformat(self) -> str:
        """Return the date formatted as a string in ISO 8601 format."""

        s = f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

        off = self.utcoffset()
        tz = _format_offset(off)
        if tz:
            s += tz

        return s

    __str__ = isoformat

    __hash__ = None


def _cmp(x: tuple[int, int, int, int], y: tuple[int, int, int, int]) -> int:
    """Compare two integers."""

    return 0 if x == y else 1 if x > y else -1


def _format_offset(off: datetime.timedelta | None = None) -> str:
    """Format a timedelta as a string."""

    s = ""
    if off is not None:
        if off.days < 0:
            sign = "-"
            off = -off
        else:
            sign = "+"
        hh, mm = divmod(off, datetime.timedelta(hours=1))
        mm, ss = divmod(mm, datetime.timedelta(minutes=1))
        s = f"{sign}{hh:02d}:{mm:02d}"
        if ss or ss.microseconds:
            s += f"{ss.seconds}:%02d"

            if ss.microseconds:
                s += f".{ss.microseconds:06d}"
    return s


def _check_tzinfo_arg(tz: datetime.tzinfo | None) -> None:
    """Check if the tzinfo argument is valid."""

    if tz is not None and not isinstance(tz, datetime.tzinfo):
        msg = "tzinfo argument must be None or of a tzinfo subclass"
        raise TypeError(msg)
