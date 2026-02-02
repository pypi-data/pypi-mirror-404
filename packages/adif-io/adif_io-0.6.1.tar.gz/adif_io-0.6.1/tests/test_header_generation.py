import adif_io


def test_vanilla_header_generation() -> None:
    """Test a plain vanilla case of header generation."""
    RAW_HEADER = {
        "adif_ver": "3.1.3",
        "CREATED_TIMESTAMP": "20240825 221514",
        "PROGRAMID": "PyCharme Community Edition",
        "PROGRAMMVERSION": "2024.1.3",
    }
    header = adif_io.headers_from_dict(RAW_HEADER)
    assert len(RAW_HEADER) == len(header)
    for key in RAW_HEADER.keys():
        assert RAW_HEADER[key] == header[key]
