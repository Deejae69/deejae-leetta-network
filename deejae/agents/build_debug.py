from __future__ import annotations

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

from deejae.runner import Agent, AgentContext

logger = logging.getLogger(__name__)


class BuildDebugAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        run_self_check = bool(ctx.config.get("run_self_check", True))
        repo_root = Path(ctx.config.get("repo_root") or Path.cwd())

        info = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
            "repo_root": str(repo_root),
        }
        logger.info("build_debug_info", extra={"agent_id": ctx.agent_id, "event": "build_debug"})

        details = []
        for key, value in info.items():
            details.append(f"{key}={value}")

        if run_self_check:
            cmd = [sys.executable, "-m", "unittest", "discover", "-q"]
            env = dict(os.environ)
            proc = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True)
            details.append(f"unittest_exit_code={proc.returncode}")
            if proc.stdout.strip():
                details.append("stdout:\n" + proc.stdout.strip())
            if proc.stderr.strip():
                details.append("stderr:\n" + proc.stderr.strip())

        await ctx.webhooks.send_event(
            event="build_debug",
            title="Build/debug report",
            body="\n".join(details),
            agent_id=ctx.agent_id,
        )
