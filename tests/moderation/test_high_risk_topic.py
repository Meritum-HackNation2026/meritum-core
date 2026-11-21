"""HighRiskTopic validation: the admin list never holds an empty topic."""

import pytest
from pydantic import ValidationError

from meritum_core.moderation import HighRiskTopic


@pytest.mark.parametrize(
    "fields",
    [{"name": "", "keywords": ["x"]}, {"name": "zdrowie", "keywords": []}],
)
def test_a_topic_needs_a_name_and_keywords(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        HighRiskTopic.model_validate(fields)
