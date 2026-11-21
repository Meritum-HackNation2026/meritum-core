"""Table of cases for mask_personal_data, false positives included."""

import time

import pytest

from meritum_core.security import MaskedText, mask_personal_data

CASES = [
    ("Zadzwoń: 601 234 567.", "Zadzwoń: [telefon]."),
    ("tel. +48 601-234-567", "tel. [telefon]"),
    ("tel. +48601234567", "tel. [telefon]"),
    ("tel. 0048 601 234 567", "tel. [telefon]"),
    ("biuro 22 123 45 67", "biuro [telefon]"),
    ("numer 601234567", "numer [telefon]"),
    ("pisz: Jan.Kowalski+x@sub.example.com.pl!", "pisz: [e-mail]!"),
    ("mieszkam na Długiej 5 601 234 567", "mieszkam na Długiej 5 [telefon]"),
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
