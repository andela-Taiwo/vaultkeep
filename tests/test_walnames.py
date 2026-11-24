import pytest
from hypothesis import given
from hypothesis import strategies as st

from vaultkeep.lsn import Lsn
from vaultkeep.walnames import (
    Segment,
    history_file_name,
    parse_history_file_name,
    parse_segment_name,
    segment_ending_at,
    segment_for,
    segment_name,
    segment_start,
)

MB = 1 << 20


def test_segment_holding_a_byte() -> None:
    assert segment_name(segment_for(Lsn.parse("16/B374D848"), 1)) == "0000000100000016000000B3"
    assert segment_name(segment_for(Lsn.parse("0/1000000"), 1)) == "000000010000000000000001"


@pytest.mark.parametrize(
    ("lsn", "expected"),
    [
        # SELECT pg_walfile_name(lsn) on timeline 1, PostgreSQL 14, 16 MB segments
        ("16/B374D848", "0000000100000016000000B3"),
        ("0/1000000", "000000010000000000000000"),
        ("0/FFFFFFFF", "0000000100000000000000FF"),
    ],
)
def test_segment_ending_at_matches_pg_walfile_name(lsn: str, expected: str) -> None:
    assert segment_name(segment_ending_at(Lsn.parse(lsn), 1)) == expected


def test_nothing_ends_at_zero() -> None:
    with pytest.raises(ValueError):
        segment_ending_at(Lsn(0), 1)


def test_last_segment_of_a_log_id_rolls_over() -> None:
    assert segment_name(Segment(1, 255)) == "0000000100000000000000FF"
    assert segment_name(Segment(1, 256)) == "000000010000000100000000"


def test_other_segment_sizes_split_differently() -> None:
    lsn = Lsn.parse("1/40000000")
    assert segment_name(segment_for(lsn, 3, 64 * MB), 64 * MB) == "000000030000000100000010"
    assert segment_name(segment_for(lsn, 3, 1024 * MB), 1024 * MB) == "000000030000000100000001"


@given(
    st.integers(1, 0xFFFFFFFF),
    st.integers(0, (1 << 64) - 1),
    st.sampled_from([MB, 16 * MB, 64 * MB, 1024 * MB]),
)
def test_name_round_trip(timeline: int, position: int, size: int) -> None:
    segment = segment_for(Lsn(position), timeline, size)
    assert parse_segment_name(segment_name(segment, size), size) == segment
    start = segment_start(segment, size).value
    assert start <= position < start + size


@pytest.mark.parametrize(
    "name",
    [
        "0000000100000016000000b3",  # lower case
        "00000001000000160000B3",  # too short
        "000000000000001600000003",  # timeline 0
        "000000010000001600000100",  # low part beyond 16 MB segments
        "0000000100000016000000B3.partial",
    ],
)
def test_bad_segment_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        parse_segment_name(name)


@pytest.mark.parametrize("size", [0, MB - 1, 3 * MB, 2048 * MB])
def test_bad_segment_sizes_are_rejected(size: int) -> None:
    with pytest.raises(ValueError, match="power of two"):
        segment_for(Lsn(0), 1, size)


def test_history_file_names() -> None:
    assert history_file_name(2) == "00000002.history"
    assert history_file_name(0x1A) == "0000001A.history"
    assert parse_history_file_name("0000001A.history") == 0x1A


@pytest.mark.parametrize("name", ["00000001.history", "2.history", "0000000a.history"])
def test_bad_history_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        parse_history_file_name(name)


def test_timeline_one_has_no_history_file() -> None:
    with pytest.raises(ValueError):
        history_file_name(1)
