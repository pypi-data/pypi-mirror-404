from typing import cast

import adif_io


def test_vanilla_adif_string_generation() -> None:
    """Plain vanilla test of generating an ADIF string."""
    wanted_string = (
        " <ADIF_VER:5>3.1.0 <PROGRAMMID:5>Lorem <EOH>\n"
        "<CALL:5>DJ3EI <NOTE:25>Unicode is here to stay!🤗 <RST_SEND:3>579 <EOR>\n"
    )
    qsos, headers = adif_io.read_from_string(wanted_string)
    assert 2 == len(headers)
    assert 1 == len(qsos)
    assert wanted_string == f"{str(headers)}{str(qsos[0])}"


def test_no_empty_adif_header_fields() -> None:
    headers = adif_io.headers_from_dict(
        cast(
            dict[str, str],
            {"ADIF_VER": "", "PROGRAMMID": "Cool Programm", "PROGRAMMVERSION": None},
        )
    )
    headers["ADIF_VER"] = ""
    headers["PROGRAMMVERSION"] = cast(str, None)
    assert " <PROGRAMMID:13>Cool Programm <EOH>\n" == str(headers)


def test_no_empty_adif_qso_fields() -> None:
    qso = adif_io.qso_from_dict(
        cast(
            dict[str, str],
            {
                "CALL": "dj3ei",
                "FREQ": "",
                "QSO_DATE": None,
                "NOTE": None,
                "RST_SEND": "",
                "RST_RCVD": "599",
                "TIME_ON": "0116",
            },
        )
    )
    assert "<TIME_ON:4>0116 <CALL:5>DJ3EI <RST_RCVD:3>599 <EOR>\n" == str(qso)
    qso["TIME_ON"] = cast(str, None)
    qso["MODE"] = ""
    qso["MY_CALL"] = ""
    assert "<CALL:5>DJ3EI <RST_RCVD:3>599 <EOR>\n" == str(qso)
    qso["MODE"] = "ssb"
    assert "<CALL:5>DJ3EI <MODE:3>SSB <RST_RCVD:3>599 <EOR>\n" == str(qso)
    qso["MY_CALL"] = cast(str, None)
    qso["TIME_ON"] = "0143"
    assert "<TIME_ON:4>0143 <CALL:5>DJ3EI <MODE:3>SSB <RST_RCVD:3>599 <EOR>\n" == str(
        qso
    )
    del qso["TIME_ON"]
    assert "<CALL:5>DJ3EI <MODE:3>SSB <RST_RCVD:3>599 <EOR>\n" == str(qso)
    assert 3 == len(qso)
    qso2 = adif_io.qso_from_dict({"NOTE": "not much as far as QSOs go."})
    assert "<NOTE:27>not much as far as QSOs go. <EOR>\n" == str(qso2)
