"""Domain skeleton: every core domain of meritum-architecture rule 1 is a slice.

`channels` is not listed: inbound channels live in meritum-backend.
"""

DOMAINS = {
    "checks",
    "corpus",
    "evidence",
    "jobs",
    "moderation",
    "notifications",
    "observability",
    "security",
    "shared",
}


def test_every_domain_is_a_slice_the_architecture_tests_cover(own: list[str]) -> None:
    slices = {m.split(".")[1] for m in own if m.count(".") > 1}
    assert DOMAINS - slices == set()
