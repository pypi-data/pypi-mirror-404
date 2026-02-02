from datetime import datetime, timezone

import pytest

import adif_io


def test_adif_str_import() -> None:
    """Plain vanilla import test."""
    qsos, header = adif_io.read_from_string(
        "A sample ADIF content for demonstration.\n"
        "<adif_ver:5>3.1.3<eoh>\n"
        "<QSO_DATE:8>20190714 <TIME_ON:4>1140<CALL:5>LY0HQ"
        "<MODE:2>CW<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
        "<STX_STRING:2>28<SRX_STRING:4>LRMD<EOR>\n"
        "<QSO_DATE:8>20190714<TIME_ON:4>1130<CALL:5>SE9HQ<MODE:2>CW<FREQ:1>7"
        "<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
        "<SRX_STRING:3>SSA<DXCC:3>284<EOR>"
    )

    assert [
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "1140",
            "CALL": "LY0HQ",
            "MODE": "CW",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "STX_STRING": "28",
            "SRX_STRING": "LRMD",
        },
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "1130",
            "CALL": "SE9HQ",
            "MODE": "CW",
            "FREQ": "7",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "SRX_STRING": "SSA",
            "DXCC": "284",
        },
    ] == qsos

    assert {"ADIF_VER": "3.1.3"} == header
    assert datetime(
        year=2019, month=7, day=14, hour=11, minute=40, second=0, tzinfo=timezone.utc
    ) == adif_io.time_on(qsos[0])
    assert datetime(
        year=2019, month=7, day=14, hour=11, minute=30, second=0, tzinfo=timezone.utc
    ) == adif_io.time_on(qsos[1])

    with pytest.raises(KeyError) as exinfo:
        adif_io.time_off(qsos[0])
    exinfo.match("TIME_OFF")


def test_adif_file_import() -> None:
    """Plain vanilla import test."""
    qsos, header = adif_io.read_from_file("tests/vanilla.adi")

    assert [
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "1140",
            "CALL": "LY0HQ",
            "MODE": "CW",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "STX_STRING": "28",
            "SRX_STRING": "LRMD",
        },
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "113027",
            "CALL": "SE9HQ",
            "MODE": "CW",
            "FREQ": "7",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "SRX_STRING": "SSA",
            "DXCC": "284",
        },
    ] == qsos

    assert {"ADIF_VER": "3.1.3"} == header


def test_convert_field_names_to_upper_case() -> None:
    qsos, header = adif_io.read_from_string(
        "<QSo_DaTE:8>20190714 <time_on:4>1140<Call:5>LY0HQ"
        "<mODE:2>CW<band:3>40M<RSt_SENt:3>599<RST_RCVD:3>599"
        "<STX_STRING:2>28<SRX_STRING:4>LRMD<EOR>\n"
        "<QSO_DATE:8>20190714<TIME_ON:4>1130<CALL:5>SE9HQ<MODE:2>CW<FREQ:1>7"
        "<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
        "Let us see that the example from the README also works:"
        "<notes:66>In this QSO, we discussed ADIF and in particular the <eor> marker."
        "<SRX_STRING:3>SSA<DXCC:3>284<Eor>"
    )

    assert [
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "1140",
            "CALL": "LY0HQ",
            "MODE": "CW",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "STX_STRING": "28",
            "SRX_STRING": "LRMD",
        },
        {
            "QSO_DATE": "20190714",
            "TIME_ON": "1130",
            "CALL": "SE9HQ",
            "MODE": "CW",
            "FREQ": "7",
            "BAND": "40M",
            "RST_SENT": "599",
            "RST_RCVD": "599",
            "SRX_STRING": "SSA",
            "DXCC": "284",
            "NOTES": "In this QSO, we discussed ADIF and in particular the <eor> marker.",
        },
    ] == qsos

    assert {} == header


def test_nonexisting_fields_are_handled_the_python_way() -> None:
    qsos, header = adif_io.read_from_string(
        "<QSO_DATE:8>20190714<TIME_ON:4>1130<CALL:5>SE9HQ<MODE:2>CW<FREQ:1>7"
        "<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
        "Let us see that the example from the README also works:"
        "<notes:66>In this QSO, we discussed ADIF and in particular the <eor> marker."
        "<SRX_STRING:3>SSA<DXCC:3>284<Eor>"
    )
    assert qsos[0]["TIME_ON"] == "1130"
    with pytest.raises(KeyError) as ex:
        qsos[0]["TIME_OFF"]
    assert ex.match("TIME_OFF")
    assert qsos[0].get("TIME_OFF") is None
    assert "not too much later" == qsos[0].get("TIME_OFF", "not too much later")


def test_need_eoh_after_header() -> None:
    with pytest.raises(adif_io.AdifHeaderWithoutEOHError):
        qsos, header = adif_io.read_from_string("Some header <qso_date:8>20230606<eor>")


def test_double_header_field_rejected() -> None:
    with pytest.raises(adif_io.AdifDuplicateFieldError) as exinfo:
        qsos, header = adif_io.read_from_string(
            "A sample ADIF content for demonstration.\n"
            "<adif_ver:5>3.1.3<adif_ver:5>3.0.2<eoh>\n"
            "<QSO_DATE:8>20190714 <TIME_ON:4>1140<CALL:5>LY0HQ"
            "<MODE:2>CW<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
            "<STX_STRING:2>28<SRX_STRING:4>LRMD<EOR>\n"
            "<QSO_DATE:8>20190714<TIME_ON:4>1130<CALL:5>SE9HQ<MODE:2>CW<FREQ:1>7"
            "<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
            "<SRX_STRING:3>SSA<DXCC:3>284"
            "<qso_date:8>20230606<EOR>"
        )
    exinfo.match(r"3\.1\.3")
    exinfo.match(r"3\.0\.2")
    exinfo.match("ADIF_VER")


def test_double_qso_field_rejected() -> None:
    with pytest.raises(adif_io.AdifDuplicateFieldError) as exinfo:
        adif_io.read_from_string(
            "A sample ADIF content for demonstration.\n"
            "<adif_ver:5>3.1.3<eoh>\n"
            "<QSO_DATE:8>20190714 <TIME_ON:4>1140<CALL:5>LY0HQ"
            "<MODE:2>CW<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
            "<STX_STRING:2>28<SRX_STRING:4>LRMD<EOR>\n"
            "<QSO_DATE:8>20190714<TIME_ON:4>1130<CALL:5>SE9HQ<MODE:2>CW<FREQ:1>7"
            "<BAND:3>40M<RST_SENT:3>599<RST_RCVD:3>599"
            "<SRX_STRING:3>SSA<DXCC:3>284"
            "<qso_date:8>20230606<EOR>"
        )

    exinfo.match("20190714")
    exinfo.match("20230606")
    exinfo.match("QSO_DATE")


def test_time_off_date_heuristic() -> None:
    qsos, header = adif_io.read_from_string(
        "A sample ADIF content for demonstration.\n"
        "<adif_ver:5>3.1.3<eoh>\n"
        "<QSO_DATE:8>20190714 <TIME_ON:6>114018 <TIME_OFF:4>2358 <EOR>\n"
        "<QSO_DATE:8>20190714 <TIME_ON:6>115019 <TIME_OFF:4>1023 <EOR>\n"
        "<QSO_DATE:8>20190714 <TIME_ON:6>115020 <QSO_DATE_OFF:8>20190720 <TIME_OFF:6>115152 <EOR>\n"
    )

    assert datetime(
        year=2019, month=7, day=14, hour=11, minute=40, second=18, tzinfo=timezone.utc
    ) == adif_io.time_on(qsos[0])
    assert datetime(
        year=2019, month=7, day=14, hour=23, minute=58, tzinfo=timezone.utc
    ) == adif_io.time_off(qsos[0])

    assert datetime(
        year=2019, month=7, day=14, hour=11, minute=50, second=19, tzinfo=timezone.utc
    ) == adif_io.time_on(qsos[1])
    assert datetime(
        year=2019, month=7, day=15, hour=10, minute=23, tzinfo=timezone.utc
    ) == adif_io.time_off(qsos[1])

    assert datetime(
        year=2019, month=7, day=14, hour=11, minute=50, second=20, tzinfo=timezone.utc
    ) == adif_io.time_on(qsos[2])
    assert datetime(
        year=2019, month=7, day=20, hour=11, minute=51, second=52, tzinfo=timezone.utc
    ) == adif_io.time_off(qsos[2])
