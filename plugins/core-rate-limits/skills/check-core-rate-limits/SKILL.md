---
name: check-core-rate-limits
description: Report the current Codex ChatGPT subscription rate-limit windows, including “do I have room left today?” requests, using the local Codex app-server instead of guessing.
---

# Check Core Rate Limits

Use this skill when the user asks about their current Codex ChatGPT subscription room, including:

- direct `5h` or `Weekly` limit checks
- natural-language questions like “do I have Codex room left today?”
- requests for remaining subscription usage before the next reset

## Workflow

1. Run the bundled helper from this skill directory:

```bash
python3 scripts/read_rate_limits.py --json --utc
```

2. Read the normalized JSON and answer with the current `5h` and `Weekly` windows:
   - remaining percent
   - used percent
   - reset time
   - `plan_type` when present
   - `limit_id` when useful for debugging

3. Prefer exact values from the helper output. Do not estimate, infer stale values, or substitute API RPM/TPM limits.

4. If the user asks for a simpler answer, summarize the two subscription windows in plain language and keep the exact reset timestamps.

## Failure handling

- If `python3` is unavailable, say that the helper could not be started because Python 3 is missing.
- If `codex` is unavailable, report that Codex is not on `PATH`.
- If `account/read` fails, tell the user to sign in with `codex login`.
- If `account/rateLimits/read` fails because authentication is required, tell the user to sign in with `codex login`.
- If `account/rateLimits/read` fails for another reason, say that this local Codex build or account does not expose ChatGPT subscription rate limits and do not guess.
- If the helper times out, tell the user the local Codex app-server did not respond in time and suggest retrying after confirming Codex is installed and logged in.

## Output guidance

- Always mention both `5h` and `Weekly` when present.
- Use UTC timestamps unless the user explicitly asks for local time.
- Keep the answer focused on subscription usage windows, not token/request throughput limits from unrelated APIs.

See `references/app-server-contract.md` for the JSON-RPC sequence, normalization rules, and unsupported-path notes.
