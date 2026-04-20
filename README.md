# Codex Rate Limits Plugin

`codex-rate-limits-plugin` is a standalone GitHub-ready home for the `codex-rate-limits` Codex plugin.

The plugin reads the current Codex ChatGPT subscription rate-limit windows from the local `codex app-server` JSON-RPC API and formats the `5h` and `Weekly` windows for quick answers.

## Layout

- `plugins/codex-rate-limits/` contains the installable plugin package.
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/` contains the skill, runtime helper, and protocol notes.
- `devel/codex-rate-limits.py` is the original developer oracle moved out of Arcogine for comparison and debugging.
- `docs/codex-rate-limits-skill-plugin-plan.md` is the historical extraction plan carried over with the source material.
- `.agents/plugins/marketplace.json` provides a repo-local marketplace entry for development.

## Local Validation

Run the helper directly:

```bash
python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --utc
```

Compare with the moved oracle:

```bash
python3 devel/codex-rate-limits.py --json --utc
```

Compare the packaged helper and oracle together:

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

Syntax-check both scripts:

```bash
python3 -m py_compile \
  devel/codex-rate-limits.py \
  plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py
```

Exercise one unsupported path with no auth:

```bash
tmpdir="$(mktemp -d)"
CODEX_HOME="$tmpdir" \
python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --json --utc
```

## GitHub Setup

1. Create a new GitHub repository named `codex-rate-limits-plugin`.
2. Push this directory as that repository's root.
3. Update plugin metadata in `plugins/codex-rate-limits/.codex-plugin/plugin.json` if you want repo-specific URLs or publisher details.
