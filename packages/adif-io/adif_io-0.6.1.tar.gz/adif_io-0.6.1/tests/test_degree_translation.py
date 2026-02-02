from pytest import approx

import adif_io


def test_plain_vanilla() -> None:
    assert approx(52 + 26.592 / 60) == adif_io.degrees_from_location("N052 26.592")
    assert "N052 26.592" == adif_io.location_from_degrees(52 + 26.592 / 60, True)

    assert approx(-(17 + 3.123 / 60)) == adif_io.degrees_from_location("S017 03.123")
    assert "S017 03.123" == adif_io.location_from_degrees(-(17 + 3.123 / 60), True)

    assert approx(0.001 / 60) == adif_io.degrees_from_location("E000 00.001")
    assert "E000 00.001" == adif_io.location_from_degrees(0.001 / 60, False)

    assert approx(-90) == adif_io.degrees_from_location("W090 00.000")
    assert "W090 00.000" == adif_io.location_from_degrees(-90, False)

    assert approx(179.5) == adif_io.degrees_from_location("E179 30.000")
    assert "E179 30.000" == adif_io.location_from_degrees(179.5, False)
