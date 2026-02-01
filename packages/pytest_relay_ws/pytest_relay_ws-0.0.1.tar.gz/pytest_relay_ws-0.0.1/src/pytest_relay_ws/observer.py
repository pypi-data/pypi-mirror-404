"""
Websocket-based observer.
"""

import pytest
from annotated_types import Any, Optional
from pydantic import BaseModel
from pytest_relay.model import Message, Observer
from websocket import WebSocket


class AnyMessage(BaseModel):
    """
    Message compatible with 'Message', used for identification.
    """

    type: str
    payload: Optional[dict[str, Any]] = None


class WsObserver(Observer):
    """
    Websocket based observer
    """

    #: websocket instance
    ws: WebSocket

    def __init__(self, url: Optional[str]) -> None:
        super().__init__()
        self.ws = WebSocket()
        try:
            self.ws.connect(url, timeout=1.0)
        except Exception as e:
            raise pytest.UsageError(
                f"`pytest-relay-ws` failed to connect to the provided URL '{url}': {e}"
            )
        self._identify()

    def _identify(self) -> None:
        """
        Sends a message to the websocket server identifying the instance as pytest-source.
        The server forwards messages as follows:

        - messages from `pytest-source` clients are forwarded to all `pytest-sink` clients.
        - messages from `pytest-sink` clients are forwarded to all `pytest-source` clients.
        """
        if not self.ws.connected:
            return
        msg = AnyMessage(type="pytest-source")
        try:
            self.ws.send(msg.model_dump_json())
        except Exception as e:
            raise pytest.UsageError(f"`pytest-relay-ws` failed to send identify-message: {e}")

    def publish(self, message: Message) -> None:
        if not self.ws.connected:
            return
        msg_str: str = message.model_dump_json()
        self.ws.send(msg_str)

    def unregister(self) -> None:
        if self.ws.connected:
            try:
                self.ws.close(timeout=1)
            except:  # pylint: disable=bare-except
                pass
