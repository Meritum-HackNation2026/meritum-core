"""Which Sensitive Data Protection infoTypes the gate masks and which it never does."""

from meritum_core.security import MARKERS
from meritum_core.security.pii.constants import (
    INFO_TYPE_MARKERS,
    NEVER_MASKED_INFO_TYPES,
)

NAMES_PLACES_AND_DATES = {
    "PERSON_NAME",
    "FIRST_NAME",
    "LAST_NAME",
    "ORGANIZATION_NAME",
    "LOCATION",
    "DATE",
    "DATE_OF_BIRTH",
}


def test_gate_masks_only_identifiers_of_a_person() -> None:
    assert set(INFO_TYPE_MARKERS) == {
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "POLAND_PESEL_NUMBER",
        "POLAND_NATIONAL_ID_NUMBER",
        "POLAND_PASSPORT",
        "IBAN_CODE",
        "CREDIT_CARD_NUMBER",
    }


def test_names_places_dates_and_addresses_are_never_masked() -> None:
    assert NAMES_PLACES_AND_DATES | {"STREET_ADDRESS"} <= NEVER_MASKED_INFO_TYPES
    assert NEVER_MASKED_INFO_TYPES.isdisjoint(INFO_TYPE_MARKERS)


def test_one_tuple_holds_every_marker_once() -> None:
    expected = {*INFO_TYPE_MARKERS.values(), "[telefon]", "[e-mail]", "[PESEL]"}
    assert set(MARKERS) == expected
    assert len(MARKERS) == len(expected)
