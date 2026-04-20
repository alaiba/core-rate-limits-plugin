# Codex Rate Limits Plugin Distribution Notes

## Preferred shared model

The default shared model is one dedicated repository per installable plugin.

This repository is that dedicated home for the `codex-rate-limits` plugin. Multiple closely related skills can live inside the same plugin package when they share the same owner, release cadence, support boundary, and validation workflow. Unrelated plugins should usually live in separate repositories.

## Team install path

For cross-project reuse, the preferred team rollout path is:

1. Clone this repository into a shared working location.
2. Copy or sync the installable plugin directory `plugins/codex-rate-limits/` to `~/plugins/codex-rate-limits/`.
3. Add or update `~/.agents/plugins/marketplace.json` with a local marketplace entry that points to `./plugins/codex-rate-limits`.

The repo-local `.agents/plugins/marketplace.json` in this repository is for development and validation convenience. It is not the long-term shared installation path for teammates.

## When a multi-plugin repo is acceptable

Use a multi-plugin repository only when the plugins share:

- the same ownership and review path
- the same release cadence
- the same CI and validation surface
- the same support boundary

If those conditions are not true, prefer one repository per plugin.

## Portability boundary

Keep the installable content under `plugins/codex-rate-limits/` free of Arcogine-specific assumptions. The standalone plugin package should be portable as-is into other repositories, shared plugin mirrors, or home-local plugin directories without needing code changes.
