"""
View do Tape.

Responsável exclusivamente pela saída textual
linear e acessível (stdout).
"""

import logging
from datetime import datetime

logger = logging.getLogger("pftcli.tape.view")


class TapeView:
    """
    Renderização do tape (Times & Trades).
    """

    def __init__(self, show_side: bool = True):
        self.show_side = show_side

    def render_trade(self, evt) -> str:
        """
        Formata um TradeEvent para saída textual.

        Espera que evt possua:
        - timestamp (epoch)
        - ticker (str)
        - quantity (int)
        - price (float | int)
        """
        ts = datetime.fromtimestamp(
            evt.timestamp
        ).strftime("%H:%M:%S.%f")[:-3]

        side = "BUY" if evt.quantity > 0 else "SELL"
        qty = abs(evt.quantity)

        parts = [ts, evt.ticker]

        if self.show_side:
            parts.append(side)

        parts.append(f"{qty} @ {evt.price}")

        return " ".join(parts)

    def render_replay(self, trades):
        """
        Gera saída textual de replay do buffer.
        """
        for evt in trades:
            yield self.render_trade(evt)
