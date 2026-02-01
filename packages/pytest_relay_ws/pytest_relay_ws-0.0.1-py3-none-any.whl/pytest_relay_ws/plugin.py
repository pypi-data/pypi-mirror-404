"""
pytest_relay observer websocket implementation.
"""

from typing import Any

import pytest  # pylint: disable=unused-import
from _pytest.config import Config, Parser

from pytest_relay_ws.observer import WsObserver


def pytest_addoption(parser: Parser) -> None:
    """
    Adds relay_ws plugin options.
    """
    group = parser.getgroup("relay_ws", "pytest-relay-ws plugin")
    group.addoption(
        "--ws-url",
        type=str,
        dest="ws_url",
        default="ws://0.0.0.0:8000",
        help="Websocket URL, e.g., ws://some.websocket:443",
    )


def pytest_configure(config: Config) -> None:
    """
    Registeres the websocket-based observer with `pytest_relay§.
    """
    relay: Any = config.pluginmanager.get_plugin("pytest_relay")
    assert relay is not None
    relay.register_observer(WsObserver(config.option.ws_url))
