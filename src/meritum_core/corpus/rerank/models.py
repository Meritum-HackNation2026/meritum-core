"""What the reranker returns: a passage with its relevance to the claim.

Features:
    US-KOR-02, US-SPR-04, F-12
"""

from pydantic import BaseModel, ConfigDict

from meritum_core.corpus.models import Passage


class RankedPassage(BaseModel):
    """One passage with the reranker's relevance score for one claim.

    Attributes:
        passage: The passage as the hybrid search returned it.
        relevance: Higher is more relevant; the scale is the provider's own, so
            compare scores only within one reranking.

    Features:
        US-KOR-02, US-SPR-04, F-12
    """

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    passage: Passage
    relevance: float
