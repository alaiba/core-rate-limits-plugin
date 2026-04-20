#!/usr/bin/env python3
"""Read Codex account rate limits via the local app-server JSON-RPC API."""

from __future__ import annotations

import argparse
import json
import selectors
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, NoReturn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print Codex ChatGPT account rate-limit windows by calling "
            "`codex app-server` over stdio."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the fetched payload and derived values as JSON",
    )
    parser.add_argument(
        "--utc",
        action="store_true",
        help="render reset timestamps in UTC instead of local time",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="seconds to wait for app-server responses (default: 10)",
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def format_reset_timestamp(timestamp: int | None, use_utc: bool) -> str | None:
    if timestamp is None:
        return None

    if use_utc:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    dt = datetime.fromtimestamp(timestamp).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_window_name(minutes: int | None, fallback: str) -> str:
    if minutes == 300:
        return "5h"
    if minutes == 10080:
        return "Weekly"
    if minutes is None:
        return fallback
    if minutes % 1440 == 0:
        days = minutes // 1440
        return "1 day" if days == 1 else f"{days} days"
    if minutes % 60 == 0:
        hours = minutes // 60
        return "1 hour" if hours == 1 else f"{hours}h"
    return f"{minutes}m"


def derive_window_data(
    name_fallback: str,
    window: dict[str, Any] | None,
    use_utc: bool,
) -> dict[str, Any] | None:
    if not window:
        return None

    used_percent = window.get("usedPercent")
    remaining_percent = None if used_percent is None else max(0, 100 - used_percent)

    return {
        "name": format_window_name(window.get("windowDurationMins"), name_fallback),
        "used_percent": used_percent,
        "remaining_percent": remaining_percent,
        "window_duration_mins": window.get("windowDurationMins"),
        "resets_at_unix": window.get("resetsAt"),
        "resets_at": format_reset_timestamp(window.get("resetsAt"), use_utc),
    }


def build_report(
    account: dict[str, Any] | None,
    rate_limits: dict[str, Any],
    use_utc: bool,
) -> dict[str, Any]:
    snapshot = rate_limits.get("rateLimits") or {}
    credits = snapshot.get("credits") or {}

    primary = derive_window_data("Primary", snapshot.get("primary"), use_utc)
    secondary = derive_window_data("Secondary", snapshot.get("secondary"), use_utc)

    return {
        "account": account,
        "limit_id": snapshot.get("limitId"),
        "limit_name": snapshot.get("limitName"),
        "plan_type": snapshot.get("planType") or (account or {}).get("planType"),
        "credits": credits,
        "primary": primary,
        "secondary": secondary,
        "raw": rate_limits,
    }


def call_app_server(timeout: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    codex = shutil.which("codex")
    if not codex:
        fail("`codex` was not found on PATH")

    proc = subprocess.Popen(
        [codex, "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    if proc.stdin is None or proc.stdout is None or proc.stderr is None:
        fail("failed to open pipes to `codex app-server`")

    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")

    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "core-rate-limits",
                    "title": "Core Rate Limits",
                    "version": "1",
                },
                "capabilities": {
                    "experimentalApi": True,
                    "optOutNotificationMethods": [],
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "account/read",
            "params": {"refreshToken": True},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "account/rateLimits/read",
        },
    ]

    for request in requests:
        proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    responses: dict[int, dict[str, Any]] = {}
    stderr_lines: list[str] = []
    deadline = time.monotonic() + timeout

    try:
        while time.monotonic() < deadline:
            if 2 in responses and 3 in responses:
                break

            remaining = max(0.0, deadline - time.monotonic())
            events = selector.select(timeout=min(0.25, remaining))
            if not events:
                continue

            for key, _ in events:
                stream = key.fileobj
                line = stream.readline()
                if not line:
                    continue

                if key.data == "stderr":
                    stderr_lines.append(line.rstrip("\n"))
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if "id" in payload:
                    responses[payload["id"]] = payload

        if 2 not in responses or 3 not in responses:
            details = ""
            if stderr_lines:
                details = f" stderr: {stderr_lines[-1]}"
            fail(f"timed out waiting for app-server responses.{details}")

        account_response = responses[2]
        rate_limit_response = responses[3]

        if "error" in account_response:
            fail(f"account/read failed: {account_response['error']}")
        if "error" in rate_limit_response:
            fail(f"account/rateLimits/read failed: {rate_limit_response['error']}")

        account = account_response["result"].get("account")
        rate_limits = rate_limit_response["result"]
        return account, rate_limits
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def print_human(report: dict[str, Any]) -> None:
    account = report.get("account") or {}

    if account.get("type") == "chatgpt":
        print(f"Account: {account.get('email')} ({report.get('plan_type')})")
    elif report.get("plan_type"):
        print(f"Plan: {report['plan_type']}")

    if report.get("limit_id"):
        print(f"Limit ID: {report['limit_id']}")

    for key in ("primary", "secondary"):
        window = report.get(key)
        if not window:
            continue

        remaining = window.get("remaining_percent")
        used = window.get("used_percent")
        reset = window.get("resets_at") or "unknown"
        label = window.get("name", key)

        if remaining is None or used is None:
            print(f"{label}: reset {reset}")
            continue

        print(f"{label}: {remaining}% remaining ({used}% used), resets {reset}")

    credits = report.get("credits") or {}
    if credits:
        has_credits = "yes" if credits.get("hasCredits") else "no"
        unlimited = "yes" if credits.get("unlimited") else "no"
        balance = credits.get("balance") or "n/a"
        print(f"Credits: has={has_credits}, unlimited={unlimited}, balance={balance}")


def main() -> None:
    args = parse_args()
    account, rate_limits = call_app_server(timeout=args.timeout)
    report = build_report(account, rate_limits, use_utc=args.utc)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print_human(report)


if __name__ == "__main__":
    main()
