from unittest.mock import MagicMock

from src.prmods.domain.ods_portal.asid_lookup import AsidLookup


def test_returns_dict_with_one_asid_mapping():
    raw_asid_lookup = [
        {
            "ASID": "123456789123",
            "NACS": "A12345",
            "OrgName": "A GP",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X12 2TB",
        }
    ]

    asid_lookup = AsidLookup(raw_asid_lookup)

    expected = {"A12345": ["123456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_dict_with_multiple_asid_mappings():
    raw_asid_lookup = [
        {
            "ASID": "223456789123",
            "NACS": "B12345",
            "OrgName": "A GP",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X42 2TB",
        },
        {
            "ASID": "323456789123",
            "NACS": "C12345",
            "OrgName": "Another GP",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X45 2TB",
        },
        {
            "ASID": "023456789123",
            "NACS": "D12345",
            "OrgName": "GP Three",
            "MName": "A Supplier",
            "PName": "A system",
            "OrgType": "GP Practice",
            "PostCode": "X78 2TB",
        },
    ]

    asid_lookup = AsidLookup(raw_asid_lookup)

    expected = {"B12345": ["223456789123"], "C12345": ["323456789123"], "D12345": ["023456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_dict_with_one_practice_with_multiple_asids():
    raw_asid_lookup = [
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

    asid_lookup = AsidLookup(raw_asid_lookup)

    expected = {"A12345": ["123456789123", "8765456789123"]}
    actual = asid_lookup.ods_asid_mapping

    assert actual == expected


def test_returns_true_if_ods_is_in_mapping():
    raw_asid_lookup = [
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

    asid_lookup = AsidLookup(raw_asid_lookup)

    expected = True
    actual = asid_lookup.is_ods_in_mapping("A12345")

    assert actual == expected


def test_returns_false_if_ods_is_not_in_mapping():
    raw_asid_lookup = [
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

    asid_lookup = AsidLookup(raw_asid_lookup)

    expected = False
    actual = asid_lookup.is_ods_in_mapping("B12345")

    assert actual == expected
