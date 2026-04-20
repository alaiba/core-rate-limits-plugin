# Check Core Rate Limits

Use this skill when the user asks for current Codex ChatGPT subscription rate limits, remaining room in the `5h` window, or remaining room in the `Weekly` window.

## Workflow

1. Run the bundled helper at `scripts/read_rate_limits.py`, resolved relative to this skill directory.
2. Prefer `--utc` unless the user explicitly asks for local time formatting.
3. Use `--json` only when you need the raw structured values for comparison or debugging.
4. Report the `5h` and `Weekly` windows plainly and do not guess values if the helper fails.

## Failure Handling

- If `codex` is unavailable, say that the local Codex CLI is not installed or not on `PATH`.
- If `account/rateLimits/read` fails, explain that the local Codex build or account session does not expose subscription rate limits.
- If the user is not signed in with the needed ChatGPT account, say so and stop rather than inventing values.
