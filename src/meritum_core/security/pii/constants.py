"""Constants of the masking gate: Sensitive Data Protection setup and markers.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from types import MappingProxyType
from typing import Final

from meritum_core.security.constants import EMAIL_MARKER, PESEL_MARKER, PHONE_MARKER

ENV_PREFIX: Final = "MERITUM_PII_"
"""Prefix of the gate's settings; ``MERITUM_PII_GATE`` picks the adapter."""

ADDRESS_MARKER: Final = "[adres]"
"""Replaces a street address (Sensitive Data Protection only)."""

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
        "STREET_ADDRESS": ADDRESS_MARKER,
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

Obvious personal data of a citizen (US-BEZ-04). ``PERSON_NAME`` is left out on
purpose: claims name public figures, and masking them would break the check.
Markers hold no digits or ``@``, so the patterns never touch them (idempotence)."""

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
