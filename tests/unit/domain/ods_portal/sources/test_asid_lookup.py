from src.prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid


def test_returns_dict_with_one_asid_mapping():
    mappings = [OdsAsid("A12345", "123456789123")]

    asid_lookup = AsidLookup(mappings)

    expected = {"A12345": ["123456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_dict_with_multiple_asid_mappings():
    mappings = [
        OdsAsid("B12345", "223456789123"),
        OdsAsid("C12345", "323456789123"),
        OdsAsid("D12345", "023456789123"),
    ]

    asid_lookup = AsidLookup(mappings)

    expected = {"B12345": ["223456789123"], "C12345": ["323456789123"], "D12345": ["023456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_dict_with_one_practice_with_multiple_asids():
    mappings = [
        OdsAsid("A12345", "123456789123"),
        OdsAsid("A12345", "8765456789123"),
    ]

    asid_lookup = AsidLookup(mappings)

    expected = {"A12345": ["123456789123", "8765456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_true_if_ods_is_in_mapping():
    mappings = [
        OdsAsid("A12345", "123456789123"),
    ]

    asid_lookup = AsidLookup(mappings)

    expected = True
    actual = asid_lookup.is_ods_in_mapping("A12345")

    assert actual == expected


def test_returns_false_if_ods_is_not_in_mapping():
    mappings = [
        OdsAsid("A12345", "123456789123"),
    ]

    asid_lookup = AsidLookup(mappings)

    expected = False
    actual = asid_lookup.is_ods_in_mapping("B12345")

    assert actual == expected


def test_build_asid_lookup_from_spine_directory_format():
    spine_directory_data = [
        {
            "ASID": "123456789123",
            "NACS": "A12345",
            "OrgName": "A GP",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X12 2TB",
        },
        {
            "ASID": "8765456789123",
            "NACS": "A12345",
            "OrgName": "A GP",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X12 2TB",
        },
    ]

    asid_lookup = AsidLookup.from_spine_directory_format(spine_directory_data)

    assert asid_lookup.is_ods_in_mapping("A12345")
    assert asid_lookup.is_ods_in_mapping("A12345")
    assert asid_lookup.ods_asid_mapping["A12345"] == ["123456789123", "8765456789123"]
