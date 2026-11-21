"""Table of cases for mask_personal_data, false positives included."""

import asyncio
import time

import pytest

from meritum_core.security import MaskedText, NullPiiGate
from meritum_core.security import mask_personal_data as mask_with_gate


def mask_personal_data(text: str) -> MaskedText:
    """Patterns only: the null gate, as in a deployment without DLP."""
    return asyncio.run(mask_with_gate(text, NullPiiGate()))


CASES = [
    ("Zadzwoń: 601 234 567.", "Zadzwoń: [telefon]."),
    ("tel. +48 601-234-567", "tel. [telefon]"),
    ("tel. +48601234567", "tel. [telefon]"),
    ("tel. 0048 601 234 567", "tel. [telefon]"),
    ("biuro 22 123 45 67", "biuro [telefon]"),
    ("numer 601234567", "numer [telefon]"),
    ("pisz: Jan.Kowalski+x@sub.example.com.pl!", "pisz: [e-mail]!"),
    ("lokal 12 601-234-567", "lokal 12 [telefon]"),
    ("601 234 567 601 234 567", "[telefon] [telefon]"),
    ("PESEL 44051401359", "PESEL [PESEL]"),
    ("PESEL: 02070803628,", "PESEL: [PESEL],"),
    # false positives: left unchanged
    ("Budżet wynosi 12345678901 zł", "Budżet wynosi 12345678901 zł"),
    ("Rok 2024, 15 osób", "Rok 2024, 15 osób"),
    ("Kwota 1 234 567 zł", "Kwota 1 234 567 zł"),
    ("Konto 12345678901234567890", "Konto 12345678901234567890"),
    ("Data 2024-05-14", "Data 2024-05-14"),
    ("adres @meritum w serwisie", "adres @meritum w serwisie"),
    # amounts with thousands separators are claims, not phones (#102)
    ("Budżet na 2025 r. to 850 000 000 zł", "Budżet na 2025 r. to 850 000 000 zł"),
    ("Polska ma 1 450 000 000 zł długu", "Polska ma 1 450 000 000 zł długu"),
    ("Na 500+ wydano 40 000 000 000 zł", "Na 500+ wydano 40 000 000 000 zł"),
    ("dług 1 450 000 000 i rośnie", "dług 1 450 000 000 i rośnie"),
    ("dług 1-450-000-000 i rośnie", "dług 1-450-000-000 i rośnie"),
    ("dług 1.450.000.000 zł", "dług 1.450.000.000 zł"),
    ("dług 1\u00a0450\u00a0000\u00a0000 zł", "dług 1\u00a0450\u00a0000\u00a0000 zł"),
    ("wydano 850 000 000 PLN", "wydano 850 000 000 PLN"),
    ("wydano 850 000 000 złotych", "wydano 850 000 000 złotych"),
    ("wydano 850 000 000,50 zł", "wydano 850 000 000,50 zł"),
    ("koszt 850 000 000 euro", "koszt 850 000 000 euro"),
    ("koszt 850 000 000 €", "koszt 850 000 000 €"),
    ("koszt $850 000 000", "koszt $850 000 000"),
    ("koszt 850 000 000 $", "koszt 850 000 000 $"),
    ("to 850 000 000 osób", "to 850 000 000 osób"),
    ("to 850 000 000 tys. zł", "to 850 000 000 tys. zł"),
    ("to 850 000 000 mln", "to 850 000 000 mln"),
    # known limit: a house number before a space-grouped phone reads as an amount
    ("Długiej 5 601 234 567", "Długiej 5 601 234 567"),
    # phones stay masked next to digits and units that do not make them amounts
    ("tel. +48 601 234 567 zł", "tel. [telefon] zł"),
    ("Dzwoń na +48 601 234 567 albo 22 123 45 67", "Dzwoń na [telefon] albo [telefon]"),
    ("nr 5 601234567", "nr 5 [telefon]"),
]


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_masks_personal_data_and_keeps_the_rest(text: str, expected: str) -> None:
    assert mask_personal_data(text).text == expected


@pytest.mark.parametrize(("text", "_expected"), CASES)
def test_masking_twice_changes_nothing(text: str, _expected: str) -> None:
    once = mask_personal_data(text).text
    assert mask_personal_data(once).text == once


def test_result_counts_replacements_and_holds_no_original() -> None:
    text = "601 234 567 i a@b.pl oraz 44051401359"
    result = mask_personal_data(text)
    assert result == MaskedText(text="[telefon] i [e-mail] oraz [PESEL]", replaced=3)
    dumped = result.model_dump_json()
    assert all(s not in dumped for s in ("601 234 567", "a@b.pl", "44051401359"))


def test_masked_text_is_frozen() -> None:
    with pytest.raises(ValueError, match="frozen"):
        mask_personal_data("x").text = "y"  # ty: ignore[invalid-assignment]  # checks immutability


@pytest.mark.parametrize("token", ["a" * 100_000, "1" * 100_000, "a@" + "b" * 100_000])
def test_long_token_is_masked_in_linear_time(token: str) -> None:
    started = time.perf_counter()
    mask_personal_data(token)
    assert time.perf_counter() - started < 0.5
