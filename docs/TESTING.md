# Testing

## Standard Validation

Use the repo root Python runner as the canonical validation entrypoint:

```bash
python3 scripts/quality.py ci
python3 scripts/quality.py local
```

`python3 scripts/quality.py ci` runs the deterministic checks that also back CI:

- Python syntax compilation for the helper and standalone oracle
- JSON validation for the plugin manifest and repo-local marketplace entry

`python3 scripts/quality.py local` adds local smoke checks that do not require a signed-in ChatGPT session:

- unsupported-path validation with an empty `CODEX_HOME`

The earlier repo-local plugin installation smoke check was removed from the standard local runner because the current Codex CLI no longer supports `codex plugin marketplace add`. Keep plugin-install validation separate until the current CLI exposes a supported local-plugin install path again.

## Live authenticated validation

These checks require a Codex login with available usage and should be run when changing helper behavior or skill routing:

1. Compare the packaged helper and the standalone oracle on the same machine:

   ```bash
   python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --json --utc
   python3 devel/codex-rate-limits.py --json --utc
   ```

2. Exercise both an explicit and a natural-language prompt in a fresh Codex session from the repo root:

   ```bash
   codex exec \
     --skip-git-repo-check \
     --dangerously-bypass-approvals-and-sandbox \
     -C "$PWD" \
     "check my 5h and weekly rate limits"
   codex exec \
     --skip-git-repo-check \
     --dangerously-bypass-approvals-and-sandbox \
     -C "$PWD" \
     "do I have Codex room left today?"
   ```

3. Confirm the answers report the `5h` and `Weekly` ChatGPT subscription windows from the packaged helper, not API RPM/TPM limits.

4. If Codex exposes a supported local-plugin install flow again, add that command back as a separate plugin-routing validation step before treating marketplace installation as covered.
