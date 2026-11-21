"""Input normalization and the result-cache key (US-WTY-03, F-05, ADR-19)."""

import pytest

from meritum_core.checks import normalize_input
from meritum_core.checks.constants import NORMALIZATION_VERSION
from meritum_core.checks.normalization import cache_key


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Od jutra  „zakaz” wjazdu", 'Od jutra "zakaz" wjazdu'),
        ("Tusk \u2014 premier", "Tusk - premier"),
        ("Tusk \u2013 premier", "Tusk - premier"),
        ("  inflacja\u00a0wynosi\n5% ", "inflacja wynosi 5%"),
        ("«cytat» i \u2018ten\u2019", "\"cytat\" i 'ten'"),
        ("Zaźolć", "Zaźolć"),  # NFD vs NFC
        ("post https://x.com/a/status/1", "post"),
    ],
)
def test_equivalent_inputs_share_a_key(a: str, b: str) -> None:
    assert normalize_input(a).cache_key == normalize_input(b).cache_key


@pytest.mark.parametrize(
    ("a", "b"),
    [("inflacja 5%", "inflacja 15%"), ("Tusk wygrał", "Tusk przegrał")],
)
def test_different_inputs_differ(a: str, b: str) -> None:
    assert normalize_input(a).cache_key != normalize_input(b).cache_key


def test_post_url_is_canonical_and_kept_apart() -> None:
    result = normalize_input(
        "Tekst HTTPS://X.com/a/status/1?utm_source=fb&s=20&fbclid=1&id=7#frag"
    )
    assert result.text == "Tekst"
    assert result.post_url == "https://x.com/a/status/1?id=7"


def test_separate_post_url_is_canonical_too() -> None:
    result = normalize_input("Tekst", post_url="https://x.com/a?gclid=3")
    assert result.post_url == "https://x.com/a"


def test_key_is_sha256_of_version_and_text() -> None:
    key = normalize_input("abc").cache_key
    assert len(key) == 64
    assert key == cache_key("abc")
    assert key != cache_key("abc", version=NORMALIZATION_VERSION + 1)


def test_sentence_punctuation_is_not_part_of_the_url() -> None:
    assert normalize_input("Zobacz https://x.com/a/status/1.").post_url == (
        "https://x.com/a/status/1"
    )


def test_url_only_inputs_are_keyed_by_the_post() -> None:
    a = normalize_input("https://x.com/a/status/1")
    b = normalize_input("https://x.com/b/status/2")
    assert a.cache_key != b.cache_key
    assert a.cache_key == normalize_input("https://x.com/a/status/1?s=20").cache_key


def test_url_is_not_part_of_the_key() -> None:
    assert (
        normalize_input("Tekst https://x.com/1").cache_key
        == normalize_input("Tekst https://x.com/2").cache_key
    )


def test_non_http_post_url_is_dropped() -> None:
    assert normalize_input("Tekst", post_url="javascript:alert(1)").post_url is None
