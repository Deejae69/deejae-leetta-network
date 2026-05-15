"""Base class shared by all DeeJae LeEtta Network agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base for all autonomous agents."""

    #: Override in subclasses with a short, human-readable name.
    name: str = "base"
    #: One-line description surfaced in the CLI help text.
    description: str = ""

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.log = logging.getLogger(f"deejae.agents.{self.name}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """Execute one agent cycle and return a result dict."""
        self.log.info("Starting agent cycle — %s", self.name)
        result = self._run()
        self.log.info("Agent cycle complete — %s | result=%s", self.name, result)
        return result

    # ------------------------------------------------------------------
    # Internal hooks (override in subclasses)
    # ------------------------------------------------------------------

    @abstractmethod
    def _run(self) -> dict[str, Any]:
        """Business logic for one agent cycle.  Must return a plain dict."""
