# App-Server Contract

The helper uses the local `codex app-server --listen stdio://` JSON-RPC flow.

## Requests

The helper sends these methods in order:

1. `initialize`
2. `account/read`
3. `account/rateLimits/read`

## Window Mapping

- `300` minutes maps to `5h`
- `10080` minutes maps to `Weekly`
- Other whole-day windows are rendered as `N day` or `N days`
- Other whole-hour windows are rendered as `Nh`
- Remaining percentage is derived as `100 - usedPercent`

## Failure Semantics

- Missing `codex` on `PATH` is a hard failure.
- Missing pipes, timeouts, or JSON-RPC errors are hard failures.
- The helper never substitutes guessed or cached rate-limit values.
