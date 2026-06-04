import pytest

from btkeepalive.volume_input import parse_volume_percent, parse_volume_text


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2", 0.02),
        ("2%", 0.02),
        ("0.5", 0.005),
        ("100", 1.0),
        ("0.01", 0.0001),
    ],
)
def test_parse_volume_percent(text, expected):
    assert parse_volume_percent(text) == pytest.approx(expected)


@pytest.mark.parametrize(
    "text",
    ["", "abc", "-1", "101", "0"],
)
def test_parse_volume_percent_invalid(text):
    assert parse_volume_percent(text) is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("50%", 0.5),
        ("0.5", 0.5),
        ("2", 0.02),
    ],
)
def test_parse_volume_text(text, expected):
    assert parse_volume_text(text) == pytest.approx(expected)
