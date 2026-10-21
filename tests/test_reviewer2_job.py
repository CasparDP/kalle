from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents/skills/reviewer2-second-opinion/scripts/reviewer2_job.py"
)
SPEC = importlib.util.spec_from_file_location("reviewer2_job", SCRIPT)
assert SPEC and SPEC.loader
reviewer2_job = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer2_job)


class Reviewer2JobTests(unittest.TestCase):
    def test_default_models_lock(self) -> None:
        provider = {
            "fast_model": "fast:cloud",
            "strong_model": "strong:cloud",
            "default_fast_model": "fast:cloud",
            "default_strong_model": "strong:cloud",
        }
        self.assertTrue(reviewer2_job._default_models(provider))
        self.assertFalse(reviewer2_job._default_models({**provider, "strong_model": "other:cloud"}))

    def test_dotenv_presence_without_exposing_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dotenv = Path(temporary) / ".env"
            dotenv.write_text("OTHER=x\nexport REVIEWER2_API_KEY='secret'\n", encoding="utf-8")
            self.assertTrue(reviewer2_job._dotenv_has_value(dotenv, "REVIEWER2_API_KEY"))
            self.assertFalse(reviewer2_job._dotenv_has_value(dotenv, "MISSING"))
            self.assertFalse(reviewer2_job._file_permissions_secure(dotenv))
            dotenv.chmod(0o600)
            self.assertTrue(reviewer2_job._file_permissions_secure(dotenv))

    def test_process_identity_rejects_non_helper_process(self) -> None:
        identity = reviewer2_job._process_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertFalse(
            reviewer2_job._process_matches(os.getpid(), Path.cwd(), identity)
        )

    def test_run_job_writes_durable_completion_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            work_dir = run_dir / "work"
            work_dir.mkdir()
            report = run_dir / "review.txt"
            log = run_dir / "reviewer2.log"
            command = [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import sys; "
                    "run=Path(sys.argv[1]); "
                    "(run/'work'/'01_stage.txt').write_text('stage'); "
                    "(run/'review.txt').write_text('review')"
                ),
                str(run_dir),
            ]
            job = {
                "repo": temporary,
                "run_dir": temporary,
                "report": str(report),
                "work_dir": str(work_dir),
                "log": str(log),
                "command": command,
                "use_caffeinate": False,
            }
            (run_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")
            (run_dir / "state.json").write_text(
                json.dumps({"status": "created"}), encoding="utf-8"
            )

            self.assertEqual(reviewer2_job._run_job(run_dir), 0)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "complete")
            self.assertEqual(state["exit_code"], 0)
            self.assertTrue(state["report_exists"])

            payload = reviewer2_job._status_payload(run_dir, job, state, 5)
            self.assertEqual(payload["stage_file_count"], 1)
            self.assertEqual(payload["last_stage_file"], "01_stage.txt")

    def test_stop_only_targets_helper_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            work_dir = run_dir / "work"
            work_dir.mkdir()
            job = {
                "repo": temporary,
                "run_dir": temporary,
                "report": str(run_dir / "review.txt"),
                "work_dir": str(work_dir),
                "log": str(run_dir / "reviewer2.log"),
                "command": [sys.executable, "-c", "import time; time.sleep(30)"],
                "use_caffeinate": False,
            }
            (run_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")
            (run_dir / "state.json").write_text(
                json.dumps({"status": "created"}), encoding="utf-8"
            )

            pid = reviewer2_job._launch_helper(run_dir, job)
            try:
                for _ in range(50):
                    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                    if state.get("status") == "running":
                        break
                    time.sleep(0.02)
                else:
                    self.fail("helper did not enter running state")

                self.assertEqual(
                    reviewer2_job.cmd_stop(SimpleNamespace(run_dir=str(run_dir))), 0
                )
                final_state = json.loads(
                    (run_dir / "state.json").read_text(encoding="utf-8")
                )
                self.assertEqual(final_state["status"], "stopped")
                self.assertEqual(final_state["pid"], pid)
            finally:
                if reviewer2_job._process_exists(pid):
                    try:
                        os.killpg(pid, 15)
                    except (ProcessLookupError, PermissionError):
                        pass

    def test_resume_rejects_stage_zero_and_rebuilds_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            base_command = [sys.executable, "-c", "pass"]
            job = {
                "repo": temporary,
                "run_dir": temporary,
                "report": str(run_dir / "review.txt"),
                "work_dir": str(run_dir / "work"),
                "log": str(run_dir / "reviewer2.log"),
                "base_command": base_command,
                "command": base_command + ["--start-stage", "2.0"],
                "use_caffeinate": False,
            }
            (run_dir / "work").mkdir()
            (run_dir / "job.json").write_text(json.dumps(job), encoding="utf-8")
            (run_dir / "state.json").write_text(
                json.dumps({"status": "failed"}), encoding="utf-8"
            )

            zero = SimpleNamespace(run_dir=str(run_dir), start_stage=0.0, stop_stage=None)
            self.assertEqual(reviewer2_job.cmd_resume(zero), 2)

            resumed = SimpleNamespace(run_dir=str(run_dir), start_stage=5.0, stop_stage=None)
            with patch.object(reviewer2_job, "_launch_helper", return_value=999):
                self.assertEqual(reviewer2_job.cmd_resume(resumed), 0)
            saved = json.loads((run_dir / "job.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["command"], base_command + ["--start-stage", "5.0"])


if __name__ == "__main__":
    unittest.main()
