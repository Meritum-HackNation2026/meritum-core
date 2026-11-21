"""Which Sensitive Data Protection infoTypes the gate masks and which it never does."""

from meritum_core.security.pii.constants import (
    INFO_TYPE_MARKERS,
    NEVER_MASKED_INFO_TYPES,
)

MENTOR_MINIMUM = {
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
    assert MENTOR_MINIMUM | {"STREET_ADDRESS"} <= NEVER_MASKED_INFO_TYPES
    assert NEVER_MASKED_INFO_TYPES.isdisjoint(INFO_TYPE_MARKERS)
