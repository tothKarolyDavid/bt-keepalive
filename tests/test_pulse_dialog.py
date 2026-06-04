from btkeepalive.win_pulse_dialog import parse_pulse_interval


def test_parse_pulse_interval_valid():
    assert parse_pulse_interval("55") == 55.0
    assert parse_pulse_interval(" 30.5 ") == 30.5


def test_parse_pulse_interval_invalid():
    assert parse_pulse_interval("") is None
    assert parse_pulse_interval("5") is None
    assert parse_pulse_interval("400") is None
    assert parse_pulse_interval("x") is None
