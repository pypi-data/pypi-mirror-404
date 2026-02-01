"""
Configurações do plugin tape.

Ordem de precedência:
1) Variáveis de ambiente
2) pftcli.ini
3) Defaults
"""

import os
from pftcli.config import load_config

ENV_PREFIX = "pftcli_TAPE_"


def load_tape_config() -> dict:
    """
    Carrega configurações do plugin tape.

    Variáveis suportadas:
    - pftcli_TAPE_LIMIT
    - pftcli_TAPE_SHOW_SIDE
    """
    cfg = load_config()

    def env(key: str, default=None):
        return os.getenv(f"{ENV_PREFIX}{key}", default)

    limit = int(
        env(
            "LIMIT",
            cfg.get("tape", "default_limit", fallback=50)
        )
    )

    show_side = str(
        env(
            "SHOW_SIDE",
            cfg.get("tape", "show_side", fallback="true")
        )
    ).lower() in ("1", "true", "yes", "on")

    return {
        "limit": limit,
        "show_side": show_side,
    }
