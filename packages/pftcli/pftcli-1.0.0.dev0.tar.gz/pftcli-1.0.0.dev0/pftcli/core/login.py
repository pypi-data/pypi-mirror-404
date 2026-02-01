import time
from .state import login_state

LOGIN_TIMEOUT = 5  # segundos


def login_healthcheck(dll) -> bool:
    """
    Verifica se o login na corretora foi bem-sucedido.

    Critério:
    - Recebimento de ao menos uma Trading Account

    Retorna:
    - True  -> logado na corretora
    - False -> não logado
    """

    # limpa estado anterior
    login_state["accounts"].clear()
    login_state["account_event"].clear()

    # 1) Inicializa login (assumindo que credenciais já foram setadas)
    ret = dll.DLLInitializeLogin()

    if ret != 0:
        return False

    # 2) Aguarda callback de conta
    received = login_state["account_event"].wait(timeout=LOGIN_TIMEOUT)

    if not received:
        return False

    # 3) Validação final
    return len(login_state["accounts"]) > 0
