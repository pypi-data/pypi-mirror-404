"""
Controller do plugin tape.

Integra CLI (click), model e view.
"""

import logging
import click

from .config import load_tape_config
from .model import TapeModel
from .view import TapeView

logger = logging.getLogger("pftcli.tape")


@click.command()
@click.argument("ticker")
@click.option(
    "-n",
    "--limit",
    type=int,
    help="Quantidade máxima de trades exibidos (buffer)",
)
@click.option(
    "--replay",
    is_flag=True,
    help="Exibe replay inicial do buffer antes do realtime",
)
@click.option(
    "--replay-only",
    is_flag=True,
    help="Exibe replay do buffer e encerra",
)
@click.pass_obj
def tape(app_ctx, ticker, limit, replay, replay_only):
    """
    Exibe o tape (times & trades) em tempo real.

    Um trade por linha, em ordem cronológica.
    """
    cfg = load_tape_config()
    effective_limit = limit or cfg["limit"]

    model = TapeModel(
        ticker=ticker,
        limit=effective_limit,
    )

    view = TapeView(
        show_side=cfg["show_side"]
    )

    def on_trade(evt):
        trade = model.on_trade(evt)
        if trade:
            click.echo(view.render_trade(trade))

    logger.info(
        "Tape iniciado | ticker=%s limit=%s replay=%s replay_only=%s",
        ticker,
        effective_limit,
        replay,
        replay_only,
    )

    app_ctx.subscribe_trades(on_trade)

    click.echo(
        f"Tape ativo | {ticker} | buffer={effective_limit}"
    )

    # 🔁 Replay inicial (buffer dump)
    if replay or replay_only:
        snapshot = model.snapshot()

        if snapshot:
            click.echo("---- REPLAY (buffer) ----")
            for line in view.render_replay(snapshot):
                click.echo(line)
            click.echo("---- FIM REPLAY ----")
        else:
            click.echo("Replay vazio (buffer sem trades)")

    # 🛑 replay-only: encerra após dump
    if replay_only:
        logger.info(
            "Tape replay-only finalizado | ticker=%s",
            ticker,
        )
        return

    # mantém processo vivo (modo realtime)
    click.get_current_context().exit_on_close = False
