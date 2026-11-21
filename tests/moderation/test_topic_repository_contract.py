"""HighRiskTopicRepository contract: every adapter in conftest.py must pass these tests."""

import asyncio

import pytest
from pydantic import ValidationError

from meritum_core.moderation import HighRiskTopic, HighRiskTopicRepository

HEALTH = HighRiskTopic(name="zdrowie", keywords=["szczepionka", "epidemia"])
SAFETY = HighRiskTopic(name="bezpieczeństwo publiczne", keywords=["bankomaty"])


def test_saved_topics_are_listed_by_name(
    run: asyncio.Runner, topics: HighRiskTopicRepository
) -> None:
    run.run(topics.save_topic(HEALTH))
    run.run(topics.save_topic(SAFETY))
    assert run.run(topics.list_topics()) == [SAFETY, HEALTH]


def test_saving_a_topic_again_replaces_its_keywords(
    run: asyncio.Runner, topics: HighRiskTopicRepository
) -> None:
    run.run(topics.save_topic(HEALTH))
    changed = HighRiskTopic(name="zdrowie", keywords=["lek"])
    run.run(topics.save_topic(changed))
    assert run.run(topics.list_topics()) == [changed]


def test_delete_topic_removes_it_and_ignores_unknown_names(
    run: asyncio.Runner, topics: HighRiskTopicRepository
) -> None:
    run.run(topics.save_topic(HEALTH))
    run.run(topics.delete_topic("zdrowie"))
    run.run(topics.delete_topic("nieznany"))
    assert run.run(topics.list_topics()) == []


@pytest.mark.parametrize(
    "fields",
    [{"name": "", "keywords": ["x"]}, {"name": "zdrowie", "keywords": []}],
)
def test_a_topic_needs_a_name_and_keywords(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        HighRiskTopic.model_validate(fields)
