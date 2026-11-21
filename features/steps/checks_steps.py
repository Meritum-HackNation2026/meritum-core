"""Steps for features/checks.feature: they build a CheckRequest like a channel does."""

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import CheckRequest


@given('tekst "{text}" wysłany przez kanał "{channel}"')
def given_text_from_channel(context: Context, text: str, channel: str) -> None:
    """Remember what the channel sends."""
    context.payload = {"channel": channel, "text": text}


@when("kanał buduje zgłoszenie sprawdzenia")
def when_channel_builds_request(context: Context) -> None:
    """Validate the payload through the public contract."""
    context.request = CheckRequest.model_validate(context.payload)


@then("zgłoszenie jest przyjęte z tym tekstem")
def then_request_is_accepted(context: Context) -> None:
    """The request keeps the channel's text unchanged."""
    assert context.request.text == context.payload["text"]
