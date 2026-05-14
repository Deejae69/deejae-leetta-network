import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "deejae_agency.py"
LEADS = REPO_ROOT / "examples" / "leads.csv"


class DeejaeAgencyCLITest(unittest.TestCase):
    def test_generate_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            messages = out_dir / "messages.jsonl"
            events = out_dir / "events.jsonl"

            proc = subprocess.run(
                ["python3", str(SCRIPT), "generate", "--leads", str(LEADS), "--out", str(messages), "--events", str(events), "--seed", "1"],
                check=True,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
            self.assertTrue(messages.exists(), msg=proc.stderr)
            lines = messages.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)
            first = json.loads(lines[0])
            self.assertIn("lead_id", first)
            self.assertIn("template_id", first)
            self.assertIn("body", first)

    def test_record_then_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            events = out_dir / "events.jsonl"

            subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "record",
                    "--events",
                    str(events),
                    "--lead-id",
                    "L001",
                    "--segment",
                    "investor",
                    "--template-id",
                    "investor_pitch",
                    "--outcome",
                    "replied",
                ],
                check=True,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PYTHONUTF8": "1"},
            )

            proc = subprocess.run(
                ["python3", str(SCRIPT), "report", "--events", str(events)],
                check=True,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
            self.assertIn("== investor ==", proc.stdout)


if __name__ == "__main__":
    unittest.main()

