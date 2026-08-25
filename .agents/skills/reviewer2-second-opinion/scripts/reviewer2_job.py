#!/usr/bin/env python3
"""Durable background launcher for reviewer2 second-opinion runs."""

from __future__ import annotations

import argparse
from collections import deque
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_VERSION = 1
DEFAULT_RUNS_DIR = ".reviewer2-runs"
# Keep detached Popen objects alive so Python does not emit false-positive
# ResourceWarnings while the deliberately independent helpers are running.
_DETACHED_PROCESSES: list[subprocess.Popen[Any]] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _is_reviewer2_repo(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "src/reviewer2/cli.py").is_file()


def _find_repo(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if value := os.environ.get("REVIEWER2_REPO"):
        candidates.append(Path(value).expanduser())
    candidates.extend(Path.cwd().resolve().parents)
    candidates.insert(0, Path.cwd().resolve())
    resolved_script = Path(__file__).resolve()
    candidates.extend(resolved_script.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if _is_reviewer2_repo(candidate):
            return candidate
    raise RuntimeError("reviewer2 repository not found; pass --repo or set REVIEWER2_REPO")


def _runner_command(repo: Path) -> list[str]:
    poetry = shutil.which("poetry")
    if poetry and (repo / "poetry.lock").is_file():
        return [poetry, "run", "python", "-m", "reviewer2.cli"]
    executable = shutil.which("reviewer2")
    if executable:
        return [executable]
    raise RuntimeError("reviewer2 is not installed and Poetry is unavailable")


def _effective_provider(repo: Path, config_path: str | None = None) -> dict[str, Any]:
    """Resolve the same provider configuration the reviewer2 CLI will use."""
    script = (
        "import json,sys; from reviewer2.config import load_config; "
        "c=load_config(None if sys.argv[1] == '-' else sys.argv[1]); "
        "print(json.dumps({'base_url': c.provider.base_url, "
        "'fast_model': c.provider.fast_model, "
        "'strong_model': c.provider.strong_model, "
        "'api_key_present': bool(c.provider.api_key)}))"
    )
    command = _runner_command(repo)
    # Replace the reviewer2 module invocation with the same environment's Python.
    if command[-3:] == ["python", "-m", "reviewer2.cli"]:
        command = command[:-2]
    else:
        poetry = shutil.which("poetry")
        command = [poetry, "run", "python"] if poetry and (repo / "poetry.lock").is_file() else [sys.executable]
    result = subprocess.run(
        command + ["-c", script, config_path or "-"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError("could not resolve reviewer2 provider config: " + result.stderr.strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("reviewer2 provider config returned invalid output") from error


def _deepseek_models(provider: dict[str, Any]) -> bool:
    return all(
        "deepseek" in str(provider.get(key, "")).lower()
        for key in ("fast_model", "strong_model")
    )


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned[:60] or "paper"


def _dotenv_has_value(path: Path, key: str) -> bool:
    if not path.is_file():
        return False
    prefix = key + "="
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        if line.startswith(prefix):
            return bool(line[len(prefix) :].strip().strip("\"'"))
    return False


def _file_permissions_secure(path: Path) -> bool | None:
    if not path.exists():
        return None
    return (path.stat().st_mode & 0o077) == 0


def _tail(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", errors="replace") as handle:
        return [line.rstrip("\n") for line in deque(handle, maxlen=max(lines, 0))]


def _process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _ps_value(pid: int, field: str) -> str | None:
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", f"{field}="],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def _process_identity(pid: int) -> dict[str, Any] | None:
    start_time = _ps_value(pid, "lstart")
    process_group = _ps_value(pid, "pgid")
    user_id = _ps_value(pid, "uid")
    command = _ps_value(pid, "command")
    if not all((start_time, process_group, user_id, command)):
        return None
    return {
        "pid": pid,
        "start_time": start_time,
        "process_group": int(process_group),
        "user_id": int(user_id),
        "command": command,
    }


def _process_matches(pid: int, run_dir: Path, expected: dict[str, Any] | None) -> bool:
    if not expected:
        return False
    current = _process_identity(pid)
    if not current:
        return False
    script = str(Path(__file__).resolve())
    return (
        current["pid"] == expected.get("pid") == pid
        and current["start_time"] == expected.get("start_time")
        and current["process_group"] == expected.get("process_group") == pid
        and current["user_id"] == expected.get("user_id") == os.getuid()
        and script in current["command"]
        and str(run_dir) in current["command"]
        and "_run" in current["command"]
    )


def _process_matches_with_retry(
    pid: int, run_dir: Path, expected: dict[str, Any] | None, attempts: int = 3
) -> bool:
    for attempt in range(attempts):
        if _process_matches(pid, run_dir, expected):
            return True
        if attempt + 1 < attempts:
            time.sleep(0.05)
    return False


def _load_run(run_dir_value: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(run_dir_value).expanduser().resolve()
    job_path = run_dir / "job.json"
    state_path = run_dir / "state.json"
    if not job_path.exists() or not state_path.exists():
        raise RuntimeError(f"not a reviewer2 helper run directory: {run_dir}")
    return run_dir, _read_json(job_path), _read_json(state_path)


def _launch_helper(run_dir: Path, job: dict[str, Any]) -> int:
    run_dir = run_dir.resolve()
    script = Path(__file__).resolve()
    process = subprocess.Popen(
        [sys.executable, str(script), "_run", str(run_dir)],
        cwd=job["repo"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _DETACHED_PROCESSES.append(process)
    job["launcher_pid"] = process.pid
    identity = None
    expected_script = str(script)
    for _ in range(20):
        candidate = _process_identity(process.pid)
        if candidate and expected_script in candidate["command"] and "_run" in candidate["command"]:
            identity = candidate
            break
        if process.poll() is not None:
            break
        time.sleep(0.01)
    if identity is None:
        process.terminate()
        raise RuntimeError("background helper did not establish a verifiable process identity")
    job["launcher_identity"] = identity
    job["launched_at"] = _now()
    _write_json(run_dir / "job.json", job)
    return process.pid


def _build_review_command(args: argparse.Namespace, repo: Path, run_dir: Path) -> list[str]:
    command = _runner_command(repo)
    command.extend(
        [
            str(Path(args.pdf).expanduser().resolve()),
            "--output",
            str(run_dir / "review.txt"),
            "--work-dir",
            str(run_dir / "work"),
        ]
    )
    if args.base:
        command.append("--base")
    if args.math:
        command.append("--math")
    if args.code_dir:
        command.extend(["--code-dir", str(Path(args.code_dir).expanduser().resolve())])
    for supplement in args.supp:
        command.extend(["--supp", str(Path(supplement).expanduser().resolve())])
    if args.config:
        command.extend(["--config", str(Path(args.config).expanduser().resolve())])
    if args.no_copyedit:
        command.append("--no-copyedit")
    if args.no_editor_note:
        command.append("--no-editor-note")
    if args.skip_size_check:
        command.append("--skip-size-check")
    return command


def cmd_check(args: argparse.Namespace) -> int:
    try:
        repo = _find_repo(args.repo)
        command = _runner_command(repo)
        provider = _effective_provider(repo, args.config)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    result = subprocess.run(
        command + ["--help"],
        cwd=repo,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    api_key_present = bool(provider["api_key_present"])
    env_file_permissions_secure = _file_permissions_secure(repo / ".env")
    payload = {
        "repo": str(repo),
        "runner": command,
        "runner_ready": result.returncode == 0,
        "api_key_present": api_key_present,
        "env_file_permissions_secure": env_file_permissions_secure,
        "caffeinate": shutil.which("caffeinate"),
        "provider": {key: value for key, value in provider.items() if key != "api_key_present"},
        "deepseek_locked": _deepseek_models(provider),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
        if not payload["runner_ready"]:
            print("runner_error: " + result.stderr.strip(), file=sys.stderr)
    ready = (
        payload["runner_ready"]
        and (api_key_present or args.allow_missing_api_key)
        and (payload["deepseek_locked"] or args.allow_non_deepseek)
    )
    return 0 if ready else 2


def cmd_start(args: argparse.Namespace) -> int:
    if args.base and (args.math or args.code_dir):
        print("error: --base disables --math and --code-dir", file=sys.stderr)
        return 2

    pdf = Path(args.pdf).expanduser().resolve()
    if not pdf.is_file():
        print(f"error: PDF not found: {pdf}", file=sys.stderr)
        return 2
    if args.code_dir and not Path(args.code_dir).expanduser().resolve().is_dir():
        print(f"error: code directory not found: {args.code_dir}", file=sys.stderr)
        return 2
    missing_supplements = [value for value in args.supp if not Path(value).expanduser().resolve().is_file()]
    if missing_supplements:
        print(f"error: supplementary PDF not found: {missing_supplements[0]}", file=sys.stderr)
        return 2

    try:
        repo = _find_repo(args.repo)
        _runner_command(repo)
        provider = _effective_provider(repo, args.config)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if not provider["api_key_present"] and not args.allow_missing_api_key:
        print("error: REVIEWER2_API_KEY is not available in the effective config", file=sys.stderr)
        return 2
    if not _deepseek_models(provider) and not args.allow_non_deepseek:
        print(
            "error: effective reviewer2 models are not both DeepSeek; "
            "pass --allow-non-deepseek for an intentional override",
            file=sys.stderr,
        )
        return 2

    if args.run_dir:
        run_dir = Path(args.run_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = (Path.cwd() / DEFAULT_RUNS_DIR / f"{stamp}-{_slug(pdf.stem)}").resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        print(f"error: run directory is not empty: {run_dir}", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "work").mkdir(exist_ok=True)

    command = _build_review_command(args, repo, run_dir)
    use_caffeinate = not args.no_caffeinate and bool(shutil.which("caffeinate"))
    job = {
        "version": STATE_VERSION,
        "created_at": _now(),
        "repo": str(repo),
        "run_dir": str(run_dir),
        "paper": str(pdf),
        "report": str(run_dir / "review.txt"),
        "work_dir": str(run_dir / "work"),
        "log": str(run_dir / "reviewer2.log"),
        "base_command": command,
        "command": command,
        "provider": {key: value for key, value in provider.items() if key != "api_key_present"},
        "use_caffeinate": use_caffeinate,
    }
    state = {"version": STATE_VERSION, "status": "created", "updated_at": _now()}
    _write_json(run_dir / "job.json", job)
    _write_json(run_dir / "state.json", state)

    if args.dry_run:
        print(json.dumps(job, indent=2, sort_keys=True))
        return 0

    pid = _launch_helper(run_dir, job)
    print(f"started reviewer2 job {pid}")
    print(f"run_dir: {run_dir}")
    print(f"status: {Path(__file__).resolve()} status {shlex.quote(str(run_dir))}")
    return 0


def _run_job(run_dir: Path) -> int:
    job = _read_json(run_dir / "job.json")
    state_path = run_dir / "state.json"
    log_path = Path(job["log"])
    command = list(job["command"])
    if job.get("use_caffeinate") and shutil.which("caffeinate"):
        command = [shutil.which("caffeinate"), "-i"] + command

    _write_json(
        state_path,
        {
            "version": STATE_VERSION,
            "status": "running",
            "pid": os.getpid(),
            "started_at": _now(),
            "updated_at": _now(),
        },
    )
    exit_code = 1
    error_text: str | None = None
    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"[{_now()}] command: {shlex.join(command)}\n")
            log.flush()
            result = subprocess.run(
                command,
                cwd=job["repo"],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
            exit_code = result.returncode
    except Exception as error:  # The state file must survive launcher failures.
        error_text = f"{type(error).__name__}: {error}"

    report_exists = Path(job["report"]).is_file()
    status = "complete" if exit_code == 0 and report_exists else "failed"
    final_state: dict[str, Any] = {
        "version": STATE_VERSION,
        "status": status,
        "pid": os.getpid(),
        "exit_code": exit_code,
        "report_exists": report_exists,
        "finished_at": _now(),
        "updated_at": _now(),
    }
    if error_text:
        final_state["error"] = error_text
    _write_json(state_path, final_state)
    return 0 if status == "complete" else 1


def _status_payload(run_dir: Path, job: dict[str, Any], state: dict[str, Any], tail_lines: int) -> dict[str, Any]:
    work_dir = Path(job["work_dir"])
    stage_files = sorted(work_dir.glob("*.txt")) if work_dir.exists() else []
    payload = dict(state)
    payload.update(
        {
            "run_dir": str(run_dir),
            "report": job["report"],
            "report_exists": Path(job["report"]).is_file(),
            "log": job["log"],
            "stage_file_count": len(stage_files),
            "last_stage_file": stage_files[-1].name if stage_files else None,
            "log_tail": _tail(Path(job["log"]), tail_lines),
        }
    )
    pid = int(state.get("pid") or job.get("launcher_pid") or 0)
    if state.get("status") in {"created", "running"} and pid and not _process_exists(pid):
        payload["status"] = "stopped_without_final_state"
    return payload


def cmd_status(args: argparse.Namespace) -> int:
    try:
        run_dir, job, state = _load_run(args.run_dir)
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    payload = _status_payload(run_dir, job, state, args.tail)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for key in (
            "status",
            "exit_code",
            "report_exists",
            "report",
            "stage_file_count",
            "last_stage_file",
            "log",
        ):
            if key in payload:
                print(f"{key}: {payload[key]}")
        if payload["log_tail"]:
            print("log_tail:")
            for line in payload["log_tail"]:
                print(f"  {line}")
    return 0 if payload["status"] in {"created", "running", "complete"} else 1


def cmd_resume(args: argparse.Namespace) -> int:
    try:
        run_dir, job, state = _load_run(args.run_dir)
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if state.get("status") in {"created", "running"}:
        pid = int(state.get("pid") or job.get("launcher_pid") or 0)
        if pid and _process_exists(pid):
            print(f"error: job is already running with pid {pid}", file=sys.stderr)
            return 2
    if args.start_stage <= 0:
        print("error: --start-stage must be greater than 0 for resume", file=sys.stderr)
        return 2
    command = list(job.get("base_command", job["command"]))
    command.extend(["--start-stage", str(args.start_stage)])
    if args.stop_stage is not None:
        command.extend(["--stop-stage", str(args.stop_stage)])
    job["command"] = command
    job["resume_start_stage"] = args.start_stage
    job["resume_stop_stage"] = args.stop_stage
    _write_json(run_dir / "job.json", job)
    _write_json(
        run_dir / "state.json",
        {
            "version": STATE_VERSION,
            "status": "created",
            "resume_start_stage": args.start_stage,
            "resumed_at": _now(),
            "updated_at": _now(),
        },
    )
    pid = _launch_helper(run_dir, job)
    print(f"resumed reviewer2 job {pid}")
    print(f"run_dir: {run_dir}")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    try:
        run_dir, job, state = _load_run(args.run_dir)
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if state.get("status") not in {"created", "running"}:
        print(f"error: job status is {state.get('status')}, not running", file=sys.stderr)
        return 2
    pid = int(state.get("pid") or job.get("launcher_pid") or 0)
    if not pid or not _process_exists(pid):
        print("error: launcher process is not running", file=sys.stderr)
        return 1
    if not _process_matches_with_retry(pid, run_dir, job.get("launcher_identity")):
        print("error: refusing to signal a process that does not match this run", file=sys.stderr)
        return 2
    os.killpg(pid, signal.SIGTERM)
    _write_json(
        run_dir / "state.json",
        {
            "version": STATE_VERSION,
            "status": "stopped",
            "pid": pid,
            "stopped_at": _now(),
            "updated_at": _now(),
        },
    )
    print(f"stopped reviewer2 job {pid}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check the reviewer2 runner and prerequisites.")
    check.add_argument("--repo")
    check.add_argument("--config")
    check.add_argument("--json", action="store_true")
    check.add_argument(
        "--allow-missing-api-key",
        action="store_true",
        help="Allow providers that genuinely do not require authentication.",
    )
    check.add_argument(
        "--allow-non-deepseek",
        action="store_true",
        help="Accept an intentional non-DeepSeek reviewer2 configuration.",
    )
    check.set_defaults(func=cmd_check)

    start = subparsers.add_parser("start", help="Launch a reviewer2 job in the background.")
    start.add_argument("pdf")
    start.add_argument("--repo")
    start.add_argument("--run-dir")
    start.add_argument("--supp", action="append", default=[], metavar="PDF")
    start.add_argument("--code-dir")
    start.add_argument("--math", action="store_true")
    start.add_argument("--base", action="store_true")
    start.add_argument("--config")
    start.add_argument("--no-copyedit", action="store_true")
    start.add_argument("--no-editor-note", action="store_true")
    start.add_argument("--skip-size-check", action="store_true")
    start.add_argument("--no-caffeinate", action="store_true")
    start.add_argument("--dry-run", action="store_true")
    start.add_argument("--allow-missing-api-key", action="store_true")
    start.add_argument("--allow-non-deepseek", action="store_true")
    start.set_defaults(func=cmd_start)

    status = subparsers.add_parser("status", help="Show durable status and the log tail.")
    status.add_argument("run_dir")
    status.add_argument("--tail", type=int, default=20)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    resume = subparsers.add_parser(
        "resume", help="Resume a stopped or failed run from an explicit pipeline stage."
    )
    resume.add_argument("run_dir")
    resume.add_argument("--start-stage", type=float, required=True)
    resume.add_argument("--stop-stage", type=float)
    resume.set_defaults(func=cmd_resume)

    stop = subparsers.add_parser("stop", help="Stop a running helper-created job.")
    stop.add_argument("run_dir")
    stop.set_defaults(func=cmd_stop)

    internal = subparsers.add_parser("_run", help=argparse.SUPPRESS)
    internal.add_argument("run_dir")
    internal.set_defaults(func=lambda args: _run_job(Path(args.run_dir).expanduser().resolve()))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
