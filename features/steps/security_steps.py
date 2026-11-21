"""Steps for features/security.feature: they mask text through the public API."""

from behave import given, then, when
from behave.runner import Context

from meritum_core.security import mask_personal_data


@given('tekst do maskowania "{text}"')
def given_text_to_mask(context: Context, text: str) -> None:
    """Remember the citizen's text."""
    context.raw_text = text


@when("system maskuje tekst")
def when_system_masks(context: Context) -> None:
    """Mask the remembered text."""
    context.masked = mask_personal_data(context.raw_text)


@then('wynik zawiera "{phone}", "{email}" i "{pesel}" zamiast tych danych')
def then_markers_replace_data(
    context: Context, phone: str, email: str, pesel: str
) -> None:
    """Every marker is present and no personal data is left."""
    masked = context.masked.text
    assert all(marker in masked for marker in (phone, email, pesel)), masked
    for secret in ("601 234 567", "jan.kowalski@example.pl", "44051401359"):
        assert secret not in masked, masked


@then("reszta tekstu jest bez zmian")
def then_rest_is_unchanged(context: Context) -> None:
    """Only the personal data changed."""
    expected = "Dzwonił z [telefon], pisz na [e-mail], PESEL [PESEL]"
    assert context.masked.text == expected, context.masked.text


@then("liczba z błędną sumą kontrolną PESEL zostaje bez zmian")
def then_number_is_kept(context: Context) -> None:
    """A number with a bad PESEL checksum is not personal data."""
    assert context.masked.text == context.raw_text, context.masked.text
