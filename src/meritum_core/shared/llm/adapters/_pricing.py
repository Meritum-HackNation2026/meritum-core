"""Cost of one call from the Vertex AI price list in ``constants``.

Features:
    US-OBS-02, F-30
"""

from meritum_core.shared.llm.constants import PRICES_USD_PER_MTOK, TOKENS_PER_MTOK


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Price a call by the model's EU list price.

    shortcut: long-context price tiers are not applied; check prompts stay far
    below them. Add the tier if passages grow.

    Args:
        model: Model ID from settings.
        input_tokens: Prompt tokens.
        output_tokens: Answer tokens, thinking included.

    Returns:
        The cost in US dollars; 0.0 for a model missing from the list.

    Features:
        US-OBS-02, F-30
    """
    input_price, output_price = PRICES_USD_PER_MTOK.get(model, (0.0, 0.0))
    return (input_tokens * input_price + output_tokens * output_price) / TOKENS_PER_MTOK
