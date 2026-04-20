# Codex App-Server Contract For Rate Limits

This skill uses the local Codex app-server over stdio and normalizes the subscription rate-limit windows into a stable report.

## JSON-RPC sequence

Send these requests in order:

1. `initialize`
   - `clientInfo.name`: `core-rate-limits`
   - `capabilities.experimentalApi`: `true`
2. `account/read`
   - `refreshToken: true`
3. `account/rateLimits/read`

The helper waits for the `account/read` and `account/rateLimits/read` responses and ignores non-JSON output on stdout.

## Normalization rules

- `windowDurationMins = 300` maps to `5h`.
- `windowDurationMins = 10080` maps to `Weekly`.
- Other minute counts fall back to a derived label such as `1 hour`, `2h`, `1 day`, or `90m`.
- `remaining_percent` is computed as `max(0, 100 - usedPercent)`.
- `resetsAt` is exposed both as `resets_at_unix` and as a formatted `resets_at` string.
- `plan_type` prefers `rateLimits.planType` and falls back to `account.planType`.
- The helper preserves the raw `account/rateLimits/read` payload under `raw` for debugging and oracle comparison.

## Failure semantics

- Missing `codex` binary: fail immediately with an explicit PATH error.
- Missing app-server pipes: fail immediately rather than pretending the request ran.
- `account/read` error: instruct the user to sign in with `codex login`.
- `account/rateLimits/read` authentication failure: instruct the user to sign in with `codex login`.
- Other `account/rateLimits/read` errors: treat the environment as unsupported for ChatGPT subscription rate limits and do not guess values.
- Timeout waiting for responses: report timeout and suggest checking local Codex installation and login state.

## Validation oracle

`devel/codex-rate-limits.py` is the repo-local oracle for comparison during validation. The packaged skill must remain self-contained and must not depend on that file at runtime.
