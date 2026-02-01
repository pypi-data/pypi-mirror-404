"""
config.py

Carregamento de configuração do pftcli.

Ordem de precedência:
1) Diretório corrente (CWD)
2) %APPDATA%/pftcli
"""

from configparser import ConfigParser
from pathlib import Path
import os

APP_NAME = "pftcli"

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

CWD_CONFIG_FILE = Path.cwd() / "pftcli.ini"

APPDATA_DIR = Path(os.getenv("APPDATA", "")) / APP_NAME
APPDATA_CONFIG_FILE = APPDATA_DIR / "pftcli.ini"

APPDATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Core loader
# ---------------------------------------------------------

def load_config() -> ConfigParser:
    """
    Carrega o arquivo pftcli.ini seguindo a ordem:

    1) CWD/pftcli.ini
    2) %APPDATA%/pftcli/pftcli.ini
    """
    parser = ConfigParser()

    if CWD_CONFIG_FILE.exists():
        parser.read(CWD_CONFIG_FILE, encoding="utf-8")
        return parser

    if APPDATA_CONFIG_FILE.exists():
        parser.read(APPDATA_CONFIG_FILE, encoding="utf-8")
        return parser

    return parser  # vazio


# ---------------------------------------------------------
# Credentials
# ---------------------------------------------------------

def load_credentials():
    """
    Ordem:
    1) Variáveis de ambiente
    2) pftcli.ini (CWD)
    3) pftcli.ini (%APPDATA%)
    """
    # 1) ENV
    key = os.getenv("PROFIT_KEY")
    user = os.getenv("PROFIT_USER")
    password = os.getenv("PROFIT_PASSWORD")

    if key and user and password:
        return key, user, password

    # 2/3) Config file
    cfg = load_config()

    if cfg.has_section("profit"):
        key = cfg.get("profit", "key", fallback=None)
        user = cfg.get("profit", "user", fallback=None)
        password = cfg.get("profit", "password", fallback=None)

        if key and user and password:
            return key, user, password

    return None, None, None


# ---------------------------------------------------------
# DLL path
# ---------------------------------------------------------

def load_dll_path(default: str | None = None) -> str:
    """
    Retorna o caminho da ProfitDLL.

    Ordem:
    1) pftcli.ini (CWD)
    2) pftcli.ini (%APPDATA%)
    3) default
    """
    cfg = load_config()

    if cfg.has_section("dll"):
        path = cfg.get("dll", "path", fallback=None)
        if path:
            return str(Path(path).expanduser())

    if default:
        return str(Path(default).expanduser())

    raise FileNotFoundError(
        "Caminho da ProfitDLL não configurado.\n"
        "Defina em pftcli.ini (CWD ou %APPDATA%/pftcli)"
    )
