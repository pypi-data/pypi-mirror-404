"""
Model do Tape (Times & Trades).

Responsável por:
- Filtrar ticker
- Manter buffer circular
- Expor snapshot para replay
"""

import logging

logger = logging.getLogger("pftcli.tape.model")


class TapeModel:
    """
    Modelo de estado do tape.

    :param ticker: Ativo monitorado
    :param limit: Tamanho máximo do buffer
    """

    def __init__(self, ticker: str, limit: int):
        self.ticker = ticker
        self.limit = limit
        self.buffer: list = []

        logger.debug(
            "TapeModel inicializado | ticker=%s limit=%s",
            ticker,
            limit,
        )

    def on_trade(self, evt):
        """
        Callback chamado a cada TradeEvent.

        Retorna o evento caso seja aceito,
        ou None se for descartado.
        """
        if evt.ticker != self.ticker:
            return None

        self.buffer.append(evt)

        if len(self.buffer) > self.limit:
            self.buffer.pop(0)

        return evt

    def snapshot(self) -> list:
        """
        Retorna uma cópia ordenada do buffer atual.
        Usado para replay (buffer dump).
        """
        return list(self.buffer)
