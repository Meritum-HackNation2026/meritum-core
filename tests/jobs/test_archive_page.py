import pytest
from pydantic import ValidationError

from meritum_core.jobs.contracts import (
    ARCHIVE_PAGE,
    CONTRACT_VERSION,
    WORKFLOWS,
    ArchivePageInput,
)

ARCHIVE_ID = "0123456789abcdef0123456789abcdef"


def test_archive_page_is_a_workflow_of_the_contract() -> None:
    assert ARCHIVE_PAGE in WORKFLOWS


def test_archive_input_is_plain_json() -> None:
    payload = ARCHIVE_PAGE.input(
        archive_id=ARCHIVE_ID, url="https://example.pl/a", owner_id="session-1234"
    ).model_dump(mode="json")
    assert payload == {
        "contract_version": CONTRACT_VERSION,
        "archive_id": ARCHIVE_ID,
        "url": "https://example.pl/a",
        "owner_id": "session-1234",
    }


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "ftp://example.pl", "example.pl"]
)
def test_archive_input_takes_only_http_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        ArchivePageInput(archive_id=ARCHIVE_ID, url=url, owner_id="session-1234")


def test_archive_output_carries_a_copy_or_a_refusal() -> None:
    refused = ARCHIVE_PAGE.output(
        archive_id=ARCHIVE_ID,
        owner_id="session-1234",
        refusal="rate_limited",
        message="Limit",
    )
    assert refused.sha256 is None
    with pytest.raises(ValidationError):
        ARCHIVE_PAGE.output.model_validate(
            {"archive_id": ARCHIVE_ID, "owner_id": "session-1234", "refusal": "nope"}
        )
