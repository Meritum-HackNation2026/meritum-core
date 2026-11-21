"""Constants of the masking gate: Sensitive Data Protection setup and markers.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from types import MappingProxyType
from typing import Final

from meritum_core.security.constants import EMAIL_MARKER, PESEL_MARKER, PHONE_MARKER

ENV_PREFIX: Final = "MERITUM_PII_"
"""Prefix of the gate's settings; ``MERITUM_PII_GATE`` picks the adapter."""

ID_CARD_MARKER: Final = "[dowód osobisty]"
"""Replaces a Polish identity card number."""

PASSPORT_MARKER: Final = "[paszport]"
"""Replaces a Polish passport number."""

BANK_ACCOUNT_MARKER: Final = "[numer konta]"
"""Replaces an IBAN bank account number."""

PAYMENT_CARD_MARKER: Final = "[karta płatnicza]"
"""Replaces a payment card number."""

INFO_TYPE_MARKERS: Final = MappingProxyType(
    {
        "PHONE_NUMBER": PHONE_MARKER,
        "EMAIL_ADDRESS": EMAIL_MARKER,
        "POLAND_PESEL_NUMBER": PESEL_MARKER,
        "POLAND_NATIONAL_ID_NUMBER": ID_CARD_MARKER,
        "POLAND_PASSPORT": PASSPORT_MARKER,
        "IBAN_CODE": BANK_ACCOUNT_MARKER,
        "CREDIT_CARD_NUMBER": PAYMENT_CARD_MARKER,
    }
)
"""Sensitive Data Protection infoTypes the gate masks, each with its marker.

Rule (US-BEZ-04, #102): we mask identifiers of a person: PESEL, identity card,
passport, phone, e-mail, IBAN bank account and payment card numbers. We never
mask first names and surnames, institutions, places, dates, amounts or other
numbers: without them a claim changes its meaning or its evidence cannot be
found (``NEVER_MASKED_INFO_TYPES``). Markers hold no digits or ``@``, so the
patterns never touch them (idempotence)."""

NEVER_MASKED_INFO_TYPES: Final = frozenset(
    {
        "PERSON_NAME",
        "FIRST_NAME",
        "LAST_NAME",
        "ORGANIZATION_NAME",
        "LOCATION",
        "STREET_ADDRESS",
        "DATE",
        "DATE_OF_BIRTH",
    }
)
"""Sensitive Data Protection infoTypes the gate never masks (#102).

Claims name public figures and institutions and quote places and dates; an
institution's address ("Sejm, ul. Wiejska 4") is part of a claim too. None of
them may enter ``INFO_TYPE_MARKERS``."""

MIN_LIKELIHOOD: Final = "LIKELY"
"""Lowest finding likelihood the gate masks; ``POSSIBLE`` hits amounts and dates."""

EU_LOCATIONS: Final = frozenset(
    {
        "europe-central2",
        "europe-north1",
        "europe-north2",
        "europe-southwest1",
        "europe-west1",
        "europe-west3",
        "europe-west4",
        "europe-west8",
        "europe-west9",
        "europe-west10",
        "europe-west12",
    }
)
"""Sensitive Data Protection regions inside the EU with a regional endpoint
(ADR-14); London (``europe-west2``) and Zürich (``europe-west6``) are left out."""

DEFAULT_LOCATION: Final = "europe-central2"
"""Region the gate uses unless ``MERITUM_PII_LOCATION`` says otherwise (Warsaw)."""

ENDPOINT: Final = "https://dlp.{location}.rep.googleapis.com/v2"
"""Regional endpoint: data stays in the region at rest, in use and in transit."""

QUOTA_PROJECT_HEADER: Final = "x-goog-user-project"
"""Header naming the project billed for the call; DLP refuses user credentials
(local Application Default Credentials) without it."""

SCOPES: Final = ("https://www.googleapis.com/auth/cloud-platform",)
"""OAuth scopes the adapter asks Application Default Credentials for."""

HTTP_TIMEOUT_SECONDS: Final = 10.0
"""Longest wait for one deidentify call; masking runs before the 30 s check."""

SUCCESS_CODE: Final = "SUCCESS"
"""Code of a transformation result that was applied."""
