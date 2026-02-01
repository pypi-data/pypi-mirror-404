"""
services.profit_service

Integração com a Profit DLL.
"""

import time
import logging
from ctypes import (
    WINFUNCTYPE,
    c_int,
    c_uint,
    c_size_t,
    byref,
)
from typing import Callable, List

from pftcli.config import load_credentials, load_dll_path
from pftcli.models.trade import TradeEvent
from pftcli.profitdll.profit_dll import initializeDll
from pftcli.profitdll.profitTypes import (
    TConnectorTrade,
    TConnectorAssetIdentifier,
    TConnectorTradingAccountOut,
)

log = logging.getLogger("pftcli.service")


class ProfitService:
    def __init__(self):
        self._dll = None
        self._trade_listeners: List[Callable[[TradeEvent], None]] = []

        self._cb_state = None
        self._cb_trade = None

        self._accounts: list[TConnectorTradingAccountOut] = []
        self._logged_in = False
        self._market_ready = False
        self._started = False

    # -------------------------------------------------
    # Lifecycle
    # -------------------------------------------------

    def start(self):
        if self._started:
            return

        dll_path = load_dll_path()
        log.info("Inicializando Profit DLL: %s", dll_path)

        self._dll = initializeDll(dll_path)
        self._register_callbacks()
        self._login()

        self._started = True

    def stop(self):
        if not self._started:
            return

        self._dll.DLLFinalize()
        self._started = False

    # -------------------------------------------------
    # API pública
    # -------------------------------------------------

    def subscribe_trades(self, fn: Callable[[TradeEvent], None]):
        self._trade_listeners.append(fn)

    def login_healthcheck(self, timeout_sec: float = 5.0) -> bool:
        """
        Login só é considerado OK quando:
        - DLL sinalizou market_state == 4
        - GetAccountCount() > 0
        """
        deadline = time.time() + timeout_sec
        self._accounts.clear()

        while time.time() < deadline:
            if not self._market_ready:
                time.sleep(0.1)
                continue

            try:
                count = self._dll.GetAccountCount()
            except Exception as exc:
                log.error("Erro ao consultar contas: %s", exc)
                break

            if count > 0:
                accounts = (TConnectorTradingAccountOut * count)()
                filled = self._dll.GetAccounts(accounts, count)

                for i in range(filled):
                    acc = accounts[i]
                    self._accounts.append(acc)
                    log.info(
                        "Conta ativa | Broker=%s Conta=%s SubConta=%s",
                        acc.AccountID.BrokerID,
                        acc.AccountID.AccountID,
                        acc.AccountID.SubAccountID,
                    )

                self._logged_in = True
                return True

            time.sleep(0.2)

        self._logged_in = False
        return False

    # -------------------------------------------------
    # Callbacks
    # -------------------------------------------------

    def _register_callbacks(self):
        @WINFUNCTYPE(None, c_int, c_int)
        def state_callback(nType, nResult):
            log.info("Estado DLL | type=%s result=%s", nType, nResult)

            # type 2 = estado do mercado
            if nType == 2 and nResult == 4:
                log.info("Mercado pronto (market_state=4)")
                self._market_ready = True

        @WINFUNCTYPE(None, TConnectorAssetIdentifier, c_size_t, c_uint)
        def trade_callback(asset_id, p_trade, flags):
            trade = TConnectorTrade(Version=0)
            is_edit = bool(flags & 1)

            if self._dll.TranslateTrade(p_trade, byref(trade)):
                evt = TradeEvent(
                    ticker=asset_id.Ticker,
                    price=trade.Price,
                    quantity=trade.Quantity,
                    timestamp_ns=time.time_ns(),
                    is_edit=is_edit,
                )
                for listener in self._trade_listeners:
                    listener(evt)

        self._cb_state = state_callback
        self._cb_trade = trade_callback

        self._dll.SetTradeCallbackV2(self._cb_trade)

    # -------------------------------------------------
    # Login
    # -------------------------------------------------

    def _login(self):
        key, user, password = load_credentials()

        if not all([key, user, password]):
            raise RuntimeError("Credenciais não encontradas")

        ret = self._dll.DLLInitializeLogin(
            key,
            user,
            password,
            self._cb_state,
            None, None, None, None,
            None, None, None, None,
            None, None,
        )

        log.info("DLLInitializeLogin retornou: %s", ret)
