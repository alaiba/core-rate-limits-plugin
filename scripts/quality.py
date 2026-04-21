#!/usr/bin/env python3
"""Cross-platform validation entrypoints for the codex-rate-limits repo."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import py_compile
import subprocess
import sys
import tempfile


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ORACLE = REPO_ROOT / "devel" / "codex-rate-limits.py"
HELPER = (
    REPO_ROOT
    / "plugins"
    / "codex-rate-limits"
    / "skills"
    / "check-codex-rate-limits"
    / "scripts"
    / "read_rate_limits.py"
)
PLUGIN_MANIFEST = REPO_ROOT / "plugins" / "codex-rate-limits" / ".codex-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run repo validation checks without a platform-specific task runner."
    )
    parser.add_argument(
        "target",
        choices=("ci", "local"),
        nargs="?",
        default="ci",
        help="ci: deterministic checks only; local: add local smoke checks",
    )
    return parser.parse_args()


def run_check(name: str, func: callable) -> None:
    print(f"[check] {name}")
    func()
    print(f"[ok] {name}")


def compile_python() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)
        py_compile.compile(
            str(ORACLE),
            cfile=str(tmpdir_path / "oracle.pyc"),
            doraise=True,
        )
        py_compile.compile(
            str(HELPER),
            cfile=str(tmpdir_path / "helper.pyc"),
            doraise=True,
        )


def validate_json_file(path: pathlib.Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        json.load(handle)


def validate_json() -> None:
    validate_json_file(PLUGIN_MANIFEST)
    validate_json_file(MARKETPLACE)


def no_auth_smoke() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["CODEX_HOME"] = tmpdir
        proc = subprocess.run(
            [sys.executable, str(HELPER), "--json", "--utc"],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            raise RuntimeError("expected helper to fail without Codex auth")

        stderr = proc.stderr
        allowed_markers = (
            "codex login",
            "account/read failed",
            "account/rateLimits/read failed",
        )
        if not any(marker in stderr for marker in allowed_markers):
            raise RuntimeError(
                "helper failed without a recognized unsupported-path message:\n"
                f"{stderr}"
            )


def main() -> None:
    args = parse_args()

    run_check("python-compile", compile_python)
    run_check("json-validate", validate_json)

    if args.target == "local":
        run_check("no-auth-smoke", no_auth_smoke)


if __name__ == "__main__":
    main()
