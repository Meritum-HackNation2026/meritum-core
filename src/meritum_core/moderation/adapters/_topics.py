"""PostgreSQL HighRiskTopicRepository over the ``high_risk_topics`` table.

Features:
    US-MOD-05, F-20
"""

from psycopg import AsyncConnection

from meritum_core.moderation.models import HighRiskTopic


class PostgresHighRiskTopicRepository:
    """HighRiskTopicRepository that keeps each topic as a row (see the port).

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-MOD-05, F-20
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def list_topics(self) -> list[HighRiskTopic]:
        """List every topic, sorted by name in code point order.

        Returns:
            The topics.
        """
        async with await AsyncConnection.connect(self._conninfo) as conn:
            cursor = await conn.execute(
                'SELECT name, keywords FROM high_risk_topics ORDER BY name COLLATE "C"'
            )
            rows = await cursor.fetchall()
        return [HighRiskTopic(name=name, keywords=keywords) for name, keywords in rows]

    async def save_topic(self, topic: HighRiskTopic) -> None:
        """Add or replace a topic.

        Args:
            topic: the topic.
        """
        async with await AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute(
                "INSERT INTO high_risk_topics (name, keywords) VALUES (%s, %s)"
                " ON CONFLICT (name) DO UPDATE SET keywords = EXCLUDED.keywords",
                (topic.name, topic.keywords),
            )

    async def delete_topic(self, name: str) -> None:
        """Delete a topic, if present.

        Args:
            name: the topic's name.
        """
        async with await AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute("DELETE FROM high_risk_topics WHERE name = %s", (name,))
