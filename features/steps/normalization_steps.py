"""Steps for features/normalization.feature: two channels, one result-cache key."""

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.normalization import normalize_input


@given('tekst z formularza "{text}"')
def given_form_text(context: Context, text: str) -> None:
    """Remember what the web form sends."""
    context.form_text = text


@given('tekst z wtyczki "{text}"')
def given_extension_text(context: Context, text: str) -> None:
    """Remember what the extension sends (behave keeps the backslash escapes)."""
    context.extension_text = text.replace('\\"', '"')


@when("system normalizuje oba wejścia")
def when_system_normalizes(context: Context) -> None:
    """Normalize both inputs through the public function."""
    context.form = normalize_input(context.form_text)
    context.extension = normalize_input(context.extension_text)


@then("oba dają ten sam klucz pamięci wyników")
def then_same_key(context: Context) -> None:
    """Both channels land on one cache entry."""
    assert context.form.cache_key == context.extension.cache_key


@then("adres posta jest zapisany osobno jako kontekst")
def then_post_url_kept(context: Context) -> None:
    """The post URL is cut from the text and kept as context."""
    assert context.extension.post_url == "https://x.com/a/status/1"
    assert "https://" not in context.extension.text
    assert context.form.post_url is None
