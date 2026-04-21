# Codex Rate Limits Plugin

`codex-rate-limits-plugin` is a standalone repository for the `codex-rate-limits` Codex plugin.

The plugin reports current Codex ChatGPT subscription rate-limit windows by querying the local `codex app-server` JSON-RPC API and formatting the `5h` and `Weekly` windows for quick answers.

## What this repo contains

- `plugins/codex-rate-limits/` - the installable local plugin package.
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/` - the skill definition, helper script, and protocol reference.
- `devel/codex-rate-limits.py` - the original developer utility retained as a validation oracle.
- `docs/codex-rate-limits-skill-plugin-plan.md` - the extracted design and implementation plan.
- `.agents/plugins/marketplace.json` - a repo-local marketplace entry for plugin discovery during development.

## Quickstart

Run the bundled helper directly:

```bash
python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --utc
```

If you want JSON output:

```bash
python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --json --utc
```

## Validation

Run the repo validation entrypoints:

```bash
python3 scripts/quality.py ci
python3 scripts/quality.py local
```

Compare the plugin helper against the developer oracle:

```bash
python3 devel/codex-rate-limits.py --json --utc
```

Compare outputs programmatically:

```bash
python3 - <<'PY'
import json
import subprocess

plugin = subprocess.check_output(
    [
        "python3",
        "plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py",
        "--json",
        "--utc",
    ],
    text=True,
)
oracle = subprocess.check_output(
    ["python3", "devel/codex-rate-limits.py", "--json", "--utc"],
    text=True,
)
print(json.loads(plugin)["primary"])
print(json.loads(oracle)["primary"])
PY
```

Syntax-check the helper and oracle:

```bash
python3 -m py_compile \
  devel/codex-rate-limits.py \
  plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py
```

Test the unsupported/no-auth path:

```bash
python3 scripts/quality.py local
```

## Repository layout

- `plugins/codex-rate-limits/.codex-plugin/plugin.json` - local plugin manifest.
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/SKILL.md` - skill definition for checking rate limits.
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py` - packaged helper that makes the JSON-RPC call.
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/references/app-server-contract.md` - protocol reference for the local app-server API.

