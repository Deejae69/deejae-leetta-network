"""Campaign Optimizer Agent — bandit-style learning to rank marketing channels."""

from __future__ import annotations

import math
from typing import Any

from deejae.agents.base import BaseAgent


class CampaignOptimizerAgent(BaseAgent):
    """
    Simple UCB1 multi-armed bandit that scores marketing channels.

    Channels accumulate wins/trials each cycle.  The agent surfaces the
    top-ranked channel and records the outcome for the next cycle.
    """

    name = "campaign_optimizer"
    description = "Rank marketing channels with UCB1 bandit learning."

    _CHANNELS = ["twitter", "instagram", "discord", "email", "youtube", "tiktok"]

    def __init__(self, cfg: dict[str, Any]) -> None:
        super().__init__(cfg)
        self._trials: dict[str, int] = {ch: 0 for ch in self._CHANNELS}
        self._wins: dict[str, float] = {ch: 0.0 for ch in self._CHANNELS}
        self._total_trials: int = 0

    # ------------------------------------------------------------------

    def _ucb1(self, channel: str) -> float:
        t = self._trials[channel]
        if t == 0:
            return float("inf")
        exploitation = self._wins[channel] / t
        exploration = math.sqrt(2 * math.log(self._total_trials) / t)
        return exploitation + exploration

    def record_outcome(self, channel: str, reward: float) -> None:
        """Update bandit state after observing a campaign outcome."""
        self._trials[channel] += 1
        self._wins[channel] += reward
        self._total_trials += 1

    def _run(self) -> dict[str, Any]:
        self.log.info("Ranking marketing channels with UCB1 …")
        scores = {ch: self._ucb1(ch) for ch in self._CHANNELS}
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        top_channel = ranked[0][0]
        self.log.info("Top channel this cycle: %s (score=%.4f)", top_channel, ranked[0][1])
        return {
            "agent": self.name,
            "top_channel": top_channel,
            "rankings": ranked,
        }
