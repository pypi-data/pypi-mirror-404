"""
plugin_loader.py

Descobre e carrega plugins internos e externos do pftcli.
"""

import importlib
import logging
import pkgutil

import pftcli.plugins

logger = logging.getLogger("pftcli.plugin_loader")


def load_plugins(cli_group):
    """
    Descobre plugins e registra comandos click.

    Plugins válidos devem expor uma função:

        register(cli_group)

    Falhas em plugins individuais não interrompem a CLI.
    """

    _load_internal_plugins(cli_group)
    _load_external_plugins(cli_group)


def _load_internal_plugins(cli_group):
    """Carrega plugins internos (pftcli.plugins.*)."""
    for _, name, _ in pkgutil.iter_modules(pftcli.plugins.__path__):
        module_name = f"pftcli.plugins.{name}"

        try:
            module = importlib.import_module(module_name)
        except Exception:
            logger.exception("Falha ao importar plugin interno: %s", module_name)
            continue

        _register_plugin(module, module_name, cli_group)


def _load_external_plugins(cli_group):
    """
    Carrega plugins externos registrados via entrypoints Poetry.
    """
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return

    eps = entry_points(group="pftcli.plugins")

    for ep in eps:
        try:
            module = ep.load()
        except Exception:
            logger.exception("Falha ao carregar plugin externo: %s", ep.name)
            continue

        _register_plugin(module, ep.name, cli_group)


def _register_plugin(module, name, cli_group):
    """Registra o plugin se ele expuser register()."""
    if not hasattr(module, "register"):
        logger.warning("Plugin %s ignorado (sem função register)", name)
        return

    try:
        module.register(cli_group)
        logger.info("Plugin carregado com sucesso: %s", name)
    except Exception:
        logger.exception("Erro ao registrar plugin: %s", name)
