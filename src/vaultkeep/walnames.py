"""WAL segment and timeline history file names.

A WAL segment file is named ``TTTTTTTTXXXXXXXXYYYYYYYY``: the timeline, then the segment
number split into a high part and a low part, all in upper-case hexadecimal. The split depends
on the segment size the cluster was created with (16 MB by default). Archiving and restore
must agree with Postgres on these names exactly, or a restore silently stops early.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from vaultkeep.lsn import Lsn

DEFAULT_SEGMENT_SIZE = 16 * 1024 * 1024
_SEGMENT = re.compile(r"[0-9A-F]{24}")
_HISTORY = re.compile(r"([0-9A-F]{8})\.history")


class Segment(NamedTuple):
    timeline: int
    number: int
    """The segment number counted from LSN 0/0."""


def check_segment_size(segment_size: int) -> None:
    """Raise unless the size is a power of two from 1 MB to 1 GB, as Postgres requires."""
    if not (1 << 20) <= segment_size <= (1 << 30) or segment_size & (segment_size - 1):
        raise ValueError("WAL segment size must be a power of two from 1 MB to 1 GB")


def _segments_per_id(segment_size: int) -> int:
    check_segment_size(segment_size)
    return (1 << 32) // segment_size


def _check_timeline(timeline: int) -> None:
    if not 1 <= timeline <= 0xFFFFFFFF:
        raise ValueError("timeline must be from 1 to FFFFFFFF")


def segment_for(lsn: Lsn, timeline: int, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Segment:
    """Return the segment that holds the byte at ``lsn``."""
    _check_timeline(timeline)
    check_segment_size(segment_size)
    return Segment(timeline, lsn.value // segment_size)


def segment_ending_at(lsn: Lsn, timeline: int, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Segment:
    """Return the segment holding the byte just before ``lsn``.

    This is the segment a backup or a recovery target that stops at ``lsn`` still needs, and
    what ``pg_walfile_name()`` reports: an LSN on a segment boundary belongs to the previous
    segment.
    """
    _check_timeline(timeline)
    check_segment_size(segment_size)
    if lsn.value == 0:
        raise ValueError("no WAL comes before 0/0")
    return Segment(timeline, (lsn.value - 1) // segment_size)


def segment_name(segment: Segment, segment_size: int = DEFAULT_SEGMENT_SIZE) -> str:
    _check_timeline(segment.timeline)
    per_id = _segments_per_id(segment_size)
    high, low = divmod(segment.number, per_id)
    if high > 0xFFFFFFFF or segment.number < 0:
        raise ValueError("segment number is out of range")
    return f"{segment.timeline:08X}{high:08X}{low:08X}"


def parse_segment_name(name: str, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Segment:
    """Parse a WAL segment file name, rejecting names Postgres would never write."""
    if not _SEGMENT.fullmatch(name):
        raise ValueError(f"{name!r} is not a WAL segment file name")
    timeline, high, low = int(name[:8], 16), int(name[8:16], 16), int(name[16:], 16)
    _check_timeline(timeline)
    per_id = _segments_per_id(segment_size)
    if low >= per_id:
        raise ValueError(f"{name!r} is not valid for {segment_size // (1 << 20)} MB segments")
    return Segment(timeline, high * per_id + low)


def segment_start(segment: Segment, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Lsn:
    """Return the LSN of the first byte in a segment."""
    check_segment_size(segment_size)
    return Lsn(segment.number * segment_size)


def history_file_name(timeline: int) -> str:
    """Return the name of the history file Postgres writes when ``timeline`` begins."""
    _check_timeline(timeline)
    if timeline == 1:
        raise ValueError("timeline 1 has no history file")
    return f"{timeline:08X}.history"


def parse_history_file_name(name: str) -> int:
    match = _HISTORY.fullmatch(name)
    if match is None:
        raise ValueError(f"{name!r} is not a timeline history file name")
    timeline = int(match.group(1), 16)
    if timeline < 2:
        raise ValueError(f"{name!r} names a timeline that has no history file")
    return timeline
