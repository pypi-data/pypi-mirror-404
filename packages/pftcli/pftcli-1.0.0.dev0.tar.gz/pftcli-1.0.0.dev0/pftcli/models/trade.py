"""
models.trade

Modelos de domínio relacionados a trades.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class TradeEvent:
    """
    Trade normalizado para uso interno.

    Attributes
    ----------
    ticker : str
        Código do ativo.
    price : float
        Preço do negócio.
    quantity : int
        Quantidade negociada.
    timestamp_ns : int
        Timestamp monotônico no momento do recebimento.
    is_edit : bool
        Indica se o trade é uma edição.
    """
    ticker: str
    price: float
    quantity: int
    timestamp_ns: int
    is_edit: bool
