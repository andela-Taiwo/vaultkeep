import pytest
from hypothesis import given
from hypothesis import strategies as st

from vaultkeep.lsn import Lsn

u64 = st.integers(0, (1 << 64) - 1)


def test_parse_and_format() -> None:
    lsn = Lsn.parse("16/B374D848")
    assert lsn.value == 0x16_B374D848
    assert str(lsn) == "16/B374D848"


def test_format_drops_leading_zeros_like_postgres() -> None:
    assert str(Lsn(0)) == "0/0"
    assert str(Lsn.parse("00000000/01000000")) == "0/1000000"


def test_lower_case_is_accepted() -> None:
    assert Lsn.parse("a/ff") == Lsn.parse("A/FF")


@pytest.mark.parametrize("text", ["", "16", "16/", "/B3", "G/0", "123456789/0", "1/2/3", "-1/0"])
def test_bad_lsns_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        Lsn.parse(text)


@given(u64)
def test_round_trip(value: int) -> None:
    assert Lsn.parse(str(Lsn(value))).value == value


@given(u64, u64)
def test_ordering_follows_the_byte_position(a: int, b: int) -> None:
    assert (Lsn(a) < Lsn(b)) == (a < b)
    assert (Lsn(a) == Lsn(b)) == (a == b)


def test_ordering_is_numeric_not_textual() -> None:
    # As text "9/0" sorts after "10/0"; as positions it comes first.
    assert Lsn.parse("9/0") < Lsn.parse("10/0")


def test_difference_is_bytes_of_wal() -> None:
    assert Lsn.parse("1/0") - Lsn.parse("0/FFFFFF00") == 0x100


def test_add_bytes() -> None:
    assert Lsn.parse("0/FFFFFFFF") + 1 == Lsn.parse("1/0")


def test_out_of_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        Lsn(-1)
    with pytest.raises(ValueError):
        Lsn((1 << 64) - 1) + 1


def test_hashable() -> None:
    assert len({Lsn.parse("1/0"), Lsn.parse("1/00000000")}) == 1
