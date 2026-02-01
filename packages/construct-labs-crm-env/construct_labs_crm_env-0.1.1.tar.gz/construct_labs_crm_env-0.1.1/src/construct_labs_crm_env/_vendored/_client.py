# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-3-Clause license.
# See LICENSE.openenv in this directory for the full license text.
"""WebSocket-based environment client from OpenEnv."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ._types import StateT, StepResult

if TYPE_CHECKING:
    from websockets.sync.client import ClientConnection

from websockets.sync.client import connect as ws_connect

ActT = TypeVar("ActT")
ObsT = TypeVar("ObsT")


def _convert_to_ws_url(url: str) -> str:
    """Convert an HTTP/HTTPS URL to a WS/WSS URL."""
    ws_url = url.rstrip("/")
    if ws_url.startswith("http://"):
        ws_url = "ws://" + ws_url[7:]
    elif ws_url.startswith("https://"):
        ws_url = "wss://" + ws_url[8:]
    elif not ws_url.startswith("ws://") and not ws_url.startswith("wss://"):
        ws_url = "ws://" + ws_url
    return ws_url


class EnvClient(ABC, Generic[ActT, ObsT, StateT]):
    """WebSocket client for environment interactions.

    Maintains a persistent connection to an environment server for efficient
    multi-step interactions without HTTP overhead.

    Example:
        >>> with MyEnvClient(base_url="ws://localhost:8000") as env:
        ...     result = env.reset(seed=42)
        ...     while not result.done:
        ...         action = agent.predict(result.observation)
        ...         result = env.step(action)
    """

    def __init__(
        self,
        base_url: str,
        connect_timeout_s: float = 10.0,
        message_timeout_s: float = 60.0,
    ):
        """Initialize environment client.

        Args:
            base_url: Server URL (http://, https://, ws://, or wss://).
            connect_timeout_s: Timeout for establishing connection.
            message_timeout_s: Timeout for receiving responses.
        """
        ws_url = _convert_to_ws_url(base_url)
        self._ws_url = f"{ws_url}/ws"
        self._connect_timeout = connect_timeout_s
        self._message_timeout = message_timeout_s
        self._ws: ClientConnection | None = None

    def connect(self) -> EnvClient[ActT, ObsT, StateT]:
        """Establish WebSocket connection.

        Returns:
            self for method chaining.

        Raises:
            ConnectionError: If connection fails.
        """
        if self._ws is not None:
            return self

        # Bypass proxy for localhost
        ws_url_lower = self._ws_url.lower()
        is_localhost = "localhost" in ws_url_lower or "127.0.0.1" in ws_url_lower

        old_no_proxy = os.environ.get("NO_PROXY")
        if is_localhost:
            current_no_proxy = old_no_proxy or ""
            if "localhost" not in current_no_proxy.lower():
                os.environ["NO_PROXY"] = (
                    f"{current_no_proxy},localhost,127.0.0.1"
                    if current_no_proxy
                    else "localhost,127.0.0.1"
                )

        try:
            self._ws = ws_connect(
                self._ws_url,
                open_timeout=self._connect_timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self._ws_url}: {e}") from e
        finally:
            if is_localhost:
                if old_no_proxy is None:
                    os.environ.pop("NO_PROXY", None)
                else:
                    os.environ["NO_PROXY"] = old_no_proxy

        return self

    def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._ws is not None:
            try:
                self._send({"type": "close"})
            except Exception:
                pass
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if self._ws is None:
            self.connect()

    def _send(self, message: dict[str, Any]) -> None:
        """Send a message over WebSocket."""
        self._ensure_connected()
        assert self._ws is not None
        self._ws.send(json.dumps(message))

    def _receive(self) -> dict[str, Any]:
        """Receive and parse a message."""
        assert self._ws is not None
        raw = self._ws.recv(timeout=self._message_timeout)
        return json.loads(raw)

    def _send_and_receive(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a message and wait for response."""
        self._send(message)
        response = self._receive()

        if response.get("type") == "error":
            error_data = response.get("data", {})
            raise RuntimeError(
                f"Server error: {error_data.get('message', 'Unknown error')} "
                f"(code: {error_data.get('code', 'UNKNOWN')})"
            )

        return response

    @abstractmethod
    def _step_payload(self, action: ActT) -> dict[str, Any]:
        """Convert action to JSON payload for the server."""
        raise NotImplementedError

    @abstractmethod
    def _parse_result(self, payload: dict[str, Any]) -> StepResult[ObsT]:
        """Convert server response to StepResult."""
        raise NotImplementedError

    @abstractmethod
    def _parse_state(self, payload: dict[str, Any]) -> StateT:
        """Convert server response to State object."""
        raise NotImplementedError

    def reset(self, **kwargs: Any) -> StepResult[ObsT]:
        """Reset the environment.

        Args:
            **kwargs: Parameters for reset (e.g., seed, episode_id).

        Returns:
            StepResult with initial observation.
        """
        message = {"type": "reset", "data": kwargs}
        response = self._send_and_receive(message)
        return self._parse_result(response.get("data", {}))

    def step(self, action: ActT, **kwargs: Any) -> StepResult[ObsT]:
        """Execute an action.

        Args:
            action: The action to execute.
            **kwargs: Additional parameters.

        Returns:
            StepResult with observation, reward, and done status.
        """
        message = {"type": "step", "data": self._step_payload(action)}
        response = self._send_and_receive(message)
        return self._parse_result(response.get("data", {}))

    def state(self) -> StateT:
        """Get current environment state."""
        message = {"type": "state"}
        response = self._send_and_receive(message)
        return self._parse_state(response.get("data", {}))

    def close(self) -> None:
        """Close connection and clean up resources."""
        self.disconnect()

    def __enter__(self) -> EnvClient[ActT, ObsT, StateT]:
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()
