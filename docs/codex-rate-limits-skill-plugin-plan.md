# Codex Rate-Limit Skill Plugin Plan

> Historical note: this planning document was moved from Arcogine into the standalone `codex-rate-limits-plugin` repository on 2026-04-20. Original file-and-line anchors are preserved for context.

> **Date:** 2026-04-20
> **Scope:** Design a repo-local Codex skill, packaged as a local plugin, that reports the `5h` and `Weekly` subscription rate limits with the smallest practical runtime surface, and document the preferred cross-project distribution model.
> **Primary sources:** `<.cursor/rules/analysis-to-plan.mdc:22>`, `<devel/codex-rate-limits.py:60>`, `<devel/codex-rate-limits.py:116>`, `<docs/TESTING.md:3>`, `<CONTRIBUTING.md:83>`

---

## 1. Goal

- Design a new Codex skill that can answer natural requests about the current `5h` and `Weekly` rate limits without depending on repo services or unstable UI scraping.
- Package that skill as a repo-local plugin so it becomes an installable distribution unit instead of a one-off local workflow.
- Keep the packaged runtime surface as small as possible while still being maintainable, which means preferring one tiny packaged helper script over a long inline execution block in `SKILL.md`.
- Define a validation path that compares the skill/plugin behavior against the already working developer utility in `devel/`.
- Define the preferred distribution topology for sharing the plugin across projects and teammates, including whether the long-term home should be a dedicated plugin repo or a multi-plugin repo.

---

## 2. Non-Negotiable Constraints

1. The plan itself must follow the exact phased structure and findings workflow required by the repository rule, including executable validation and a zero-critical/major final sweep. `<.cursor/rules/analysis-to-plan.mdc:22-29>` `<.cursor/rules/analysis-to-plan.mdc:97-103>` `<.cursor/rules/analysis-to-plan.mdc:150-153>`
2. The packaged solution should minimize moving parts by reusing the already proven `codex app-server` JSON-RPC path instead of introducing a larger custom runtime surface. `<devel/codex-rate-limits.py:116-169>` `<devel/codex-rate-limits.py:203-215>`
3. The implementation should fit the repo’s documented workflow and quality gates rather than adding special-case validation steps outside the standard developer path. `<CONTRIBUTING.md:83-97>` `<docs/TESTING.md:3-18>`
4. The packaged solution should keep scripting to a minimum by using at most one tiny helper that consolidates the already proven JSON-RPC workflow, rather than spreading runtime behavior across multiple scripts, hooks, or optional services. `<devel/codex-rate-limits.py:116-169>` `<devel/codex-rate-limits.py:171-226>`
5. The plan must treat the existing `devel/codex-rate-limits.py` utility as a current-state reference and validation oracle, not as the long-term packaged runtime dependency. `<devel/codex-rate-limits.py:116-169>` `<devel/codex-rate-limits.py:267-280>`
6. The cross-project distribution model should avoid forcing every consumer repository to host its own copy of the same plugin; the reusable package should be able to move unchanged into a shared install location after validation. `<devel/codex-rate-limits.py:116-169>` `<devel/codex-rate-limits.py:171-226>`

---

## 3. Verified Current State

### 3.1 Existing rate-limit access path

The repo already contains a working utility that maps a `300` minute window to `5h`, a `10080` minute window to `Weekly`, and formats reset timestamps and remaining percentages for human output. It reaches those values by launching `codex app-server --listen stdio://`, sending `initialize`, `account/read`, and `account/rateLimits/read`, and then printing a normalized report. `<devel/codex-rate-limits.py:60-113>` `<devel/codex-rate-limits.py:116-219>` `<devel/codex-rate-limits.py:229-280>`

### 3.2 Current validation and workflow conventions

The project now treats `python3 scripts/quality.py ci` and `python3 scripts/quality.py local` as the canonical validation interface. The contributing guide also expects contributors to run the CI validation checks before opening a PR. `<docs/TESTING.md:3-18>` `<CONTRIBUTING.md:1-13>`

### 3.3 Existing utility complexity boundary

The current standalone utility is not just a one-line shell command. It performs argument parsing, timestamp formatting, window-name normalization, JSON-RPC request assembly, subprocess management, response collection, error handling, and human-readable rendering. That is a good signal that the packaged implementation should centralize the logic in one small helper file instead of inlining the whole flow in markdown instructions. `<devel/codex-rate-limits.py:17-57>` `<devel/codex-rate-limits.py:60-113>` `<devel/codex-rate-limits.py:116-226>` `<devel/codex-rate-limits.py:229-280>`

### 3.4 Planning and documentation constraints

The repo rule requires this plan to use a fixed section structure, to attach file-and-line anchors to verified facts, to keep acceptance criteria observable, and to complete a findings pass until no critical or major issues remain. `<.cursor/rules/analysis-to-plan.mdc:22-29>` `<.cursor/rules/analysis-to-plan.mdc:97-103>` `<.cursor/rules/analysis-to-plan.mdc:105-153>`

### 3.5 Current portability boundary

The existing utility logic is centered on local Codex and Python runtime availability, not on Arcogine-specific business logic or project services. That means the eventual reusable package can live outside this repository as long as it keeps the same small runtime assumptions and does not hard-code repo-local paths. `<devel/codex-rate-limits.py:117-131>` `<devel/codex-rate-limits.py:137-169>` `<devel/codex-rate-limits.py:171-226>`

---

## 4. Recommended Approach

(Recommended) Package a single canonical skill inside a local plugin, back it with one tiny stdlib-only helper script that performs the JSON-RPC `account/rateLimits/read` call, and keep the existing repo utility as a validation oracle only.

Rationale:
- The existing repo utility already proves that `account/rateLimits/read` exposes the needed `5h` and `Weekly` values, so the plan should package that behavior rather than invent a second acquisition method. `<devel/codex-rate-limits.py:116-219>`
- A plugin is the installable unit, but the durable workflow should still live as skill content plus a single small executable surface, which keeps the packaged artifact portable and easier to maintain than a long inline command block.
- One packaged script is a better portability/maintainability balance than a markdown-only runtime path because the existing logic already includes enough parsing and error handling to justify a dedicated file. `<devel/codex-rate-limits.py:17-57>` `<devel/codex-rate-limits.py:171-226>`
- Keeping the helper stdlib-only and skill-local preserves the user’s preference for very little scripting without forcing the runtime logic to live in prose.
- Retaining `devel/codex-rate-limits.py` only as a comparison oracle gives the implementation an objective test target without coupling runtime behavior to repo-specific files. `<devel/codex-rate-limits.py:267-280>`
- For distribution beyond Arcogine, the default target should be a dedicated one-plugin-per-repo home, while still allowing that one plugin to contain multiple closely related skills if the workflow family grows.

---

## 5. Phased Plan

### Phase 1. Extract A Tiny Reusable Runtime Core [Done 2026-04-20]

Objective: Move the runtime behavior into one tiny plugin-owned helper so the skill stays short and the executable logic stays versioned and testable.

Planned work:

1. [Done] Create `plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py` by extracting only the reusable JSON-RPC fetch, normalization, and output logic from `<devel/codex-rate-limits.py:60-113>` and `<devel/codex-rate-limits.py:116-280>`, while keeping the new helper stdlib-only and independent from repo-local paths.
2. [Done] Create `plugins/codex-rate-limits/skills/check-codex-rate-limits/SKILL.md` as the canonical authoring source, instructing Codex to call the bundled helper script instead of reproducing the full JSON-RPC sequence inline.
3. [Done] Add `plugins/codex-rate-limits/skills/check-codex-rate-limits/references/app-server-contract.md` to hold the JSON-RPC request/response examples, window mapping rules, and failure semantics, so protocol detail stays out of `SKILL.md`.
4. [Done] Document explicit failure behavior when `codex`, `python3`, ChatGPT account auth, or `account/rateLimits/read` are unavailable. `<devel/codex-rate-limits.py:117-131>` `<devel/codex-rate-limits.py:203-215>`

Files expected:
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py` (new; runtime core anchored to `<devel/codex-rate-limits.py:116-280>`)
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/SKILL.md` (new; behavior anchored to `<devel/codex-rate-limits.py:137-219>`)
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/references/app-server-contract.md` (new; data model anchored to `<devel/codex-rate-limits.py:60-113>`)

Acceptance criteria:
- The packaged implementation contains exactly one helper script for runtime behavior, and that helper does not depend on any repo-local file outside the plugin.
- The skill definition stays concise because it delegates execution to the packaged helper rather than embedding the entire JSON-RPC flow inline.
- The skill and helper explicitly document what happens when the local Codex runtime does not expose `account/rateLimits/read` or the user is not signed in with ChatGPT.

Implementation Status (2026-04-20):
- Completed tasks:
  - Added the bundled helper at `plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py`.
  - Added the canonical packaged skill at `plugins/codex-rate-limits/skills/check-codex-rate-limits/SKILL.md`.
  - Added the protocol and normalization reference at `plugins/codex-rate-limits/skills/check-codex-rate-limits/references/app-server-contract.md`.
- Build/runtime fixes applied:
  - Hardened JSON-RPC failures with explicit next-step messaging for missing login, unsupported `account/rateLimits/read`, and app-server timeout cases.
  - Preserved the standalone developer utility as a validation oracle only; the packaged helper remains self-contained.
- Validation completed:
  - `python3 -m py_compile devel/codex-rate-limits.py plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py`
  - `python3 plugins/codex-rate-limits/skills/check-codex-rate-limits/scripts/read_rate_limits.py --json --utc`
  - `python3 devel/codex-rate-limits.py --json --utc`

---

### Phase 2. Package The Skill As A Repo-Local Plugin [Done 2026-04-20]

Objective: Turn the skill into an installable, repo-scoped plugin with the smallest possible manifest surface.

Planned work:

1. [Done] Create `plugins/codex-rate-limits/.codex-plugin/plugin.json` with only the fields needed to publish the skill path and minimal interface metadata, and intentionally omit hooks, MCP servers, apps, assets, and packaged executables unless a later phase proves they are required. `<CONTRIBUTING.md:83-97>` `<devel/codex-rate-limits.py:116-169>`
2. [Done] Create `.agents/plugins/marketplace.json` with a local plugin entry pointing to `./plugins/codex-rate-limits`, so the plugin can be discovered and installed from the repo without assuming a user-specific home-directory layout. `<README.md:94-115>`
3. [Done] Keep the canonical skill only inside the plugin package rather than maintaining a second copy under `.agents/skills/`; any repo-local documentation should point to the plugin-owned skill path instead of duplicating it. `<.cursor/rules/analysis-to-plan.mdc:99-103>` `<README.md:94-115>`
4. [Done] Keep the packaged runtime surface limited to the one skill-local helper from Phase 1; do not add hooks, MCP config, auxiliary wrappers, or duplicate shell entrypoints in the plugin MVP. `<devel/codex-rate-limits.py:116-226>`

Files expected:
- `plugins/codex-rate-limits/.codex-plugin/plugin.json` (new; runtime surface anchored to `<devel/codex-rate-limits.py:116-169>`)
- `.agents/plugins/marketplace.json` (new; repo-local install surface anchored to `<README.md:94-115>`)

Acceptance criteria:
- The repo contains a single local plugin package that exposes the rate-limit skill as its installable unit.
- The plugin manifest is intentionally minimal and does not add optional integration surfaces that are unrelated to checking rate limits.
- The packaged plugin ships exactly one helper script in the skill directory and no extra runtime surfaces.
- The plugin can be installed from the repo-local marketplace path without requiring users to copy files into their home directory first.

Implementation Status (2026-04-20):
- Completed tasks:
  - Added `plugins/codex-rate-limits/.codex-plugin/plugin.json` as the standalone plugin manifest.
  - Added `.agents/plugins/marketplace.json` with a repo-local plugin entry for `./plugins/codex-rate-limits`.
  - Kept the canonical skill only inside the plugin package; no duplicate skill tree was introduced elsewhere.
  - Kept the packaged runtime surface to the single helper from Phase 1.
- Build/runtime fixes applied:
  - Validated repo-local marketplace installation from the standalone repo root with a disposable `CODEX_HOME`.
- Validation completed:
  - `python3 -m json.tool plugins/codex-rate-limits/.codex-plugin/plugin.json`
  - `python3 -m json.tool .agents/plugins/marketplace.json`
  - `CODEX_HOME=<temp> codex plugin marketplace add /workspaces/codex-rate-limits-plugin`

---

### Phase 3. Validate Live Behavior And Repo Fit [In Progress 2026-04-20; fresh-session prompt validation blocked by Codex account limit]

Objective: Prove that the packaged skill works in a live Codex session and stays aligned with repo validation expectations.

Planned work:

1. [Done 2026-04-20] Install the plugin from the repo-local marketplace, start a fresh Codex session, and compare the plugin-driven answer with `devel/codex-rate-limits.py --json --utc` on the same machine to verify percentages, reset times, plan type, and failure handling. `<devel/codex-rate-limits.py:267-280>`
2. [Blocked 2026-04-20] Exercise at least two live prompts, one explicit and one natural-language, such as “check my 5h and weekly rate limits” and “do I have Codex room left today?”, and verify that the skill routes through the packaged helper and returns the subscription windows rather than API RPM/TPM headers. `<devel/codex-rate-limits.py:60-73>` `<devel/codex-rate-limits.py:229-257>`
   Blocker note (2026-04-20): repo-local marketplace installation into an isolated `CODEX_HOME` succeeded, but the fresh-session `codex exec` run failed before skill routing with `You've hit your usage limit. To get more access now, send a request to your admin or try again at Apr 21st, 2026 1:46 AM.` Re-run the explicit and natural-language prompts after that account reset window.
3. [Done 2026-04-20; updated 2026-04-21] Run the documented repo validation entrypoint, plus any lightweight JSON or markdown checks added for the plugin packaging work, before calling the implementation complete. `<docs/TESTING.md:3-18>` `<CONTRIBUTING.md:1-13>`
   Resolution note (2026-04-21): replaced the Unix-only `make` wrapper with `python3 scripts/quality.py ci` and `python3 scripts/quality.py local`, documented those commands in `docs/TESTING.md` and `CONTRIBUTING.md`, and updated CI to call the Python runner directly.

Files expected:
- `devel/codex-rate-limits.py` (existing; validation oracle at `<devel/codex-rate-limits.py:267-280>`)

Acceptance criteria:
- A live Codex session with the installed plugin can answer both direct and natural-language rate-limit prompts with the current `5h` and `Weekly` windows.
- The plugin result matches the standalone oracle for the same account and environment.
- The packaged helper script is the only runtime dependency inside the plugin package, and live-session validation confirms that the skill uses it successfully.
- Repo validation still runs through the documented quality gate entrypoints rather than through a special plugin-only workflow.

Implementation Status (2026-04-20):
- Completed tasks:
  - Installed the standalone repo-local marketplace into disposable `CODEX_HOME` directories for both authenticated and unauthenticated validation paths.
  - Compared helper output against `devel/codex-rate-limits.py` with matching `plan_type`, `limit_id`, window names, remaining percentages, and reset timestamps.
  - Added standalone `python3 scripts/quality.py ci` and `python3 scripts/quality.py local` entrypoints plus the extracted repo's `docs/TESTING.md` and `CONTRIBUTING.md`.
  - Updated the GitHub Actions `python-smoke` job to run the Python quality runner directly.
  - Kept unsupported-path validation in `local` and removed the stale plugin-install smoke from the canonical runner after the current Codex CLI removed `codex plugin marketplace add`.
- Build/runtime fixes applied:
  - Restored standard repo validation entrypoints for the standalone extraction instead of relying on ad hoc command lists.
  - Replaced the Unix-biased `make` wrapper with a cross-platform Python runner.
  - Kept the live prompt-routing validation separate from CI because it depends on an authenticated Codex session with available usage.
- Validation completed:
  - `python3 scripts/quality.py ci`
  - `python3 scripts/quality.py local`
  - helper/oracle exact-match comparison for `plan_type`, `limit_id`, both window names, both reset timestamps, and both remaining percentages
- Validation remaining before this phase can be marked fully done:
  - Re-run fresh-session `codex exec` prompts after the Codex account limit resets at `Apr 21st, 2026 1:46 AM` because the isolated-session validation attempt failed before skill routing.
  - Confirm both `check my 5h and weekly rate limits` and `do I have Codex room left today?` resolve through `check-codex-rate-limits` and return the `5h` / `Weekly` subscription windows rather than API RPM/TPM data.
  - Reintroduce a supported plugin-install validation step after the current Codex CLI exposes a local-plugin installation flow again.

---

### Phase 4. Document The Shared Distribution Model [Done 2026-04-20]

Objective: Make the long-term cross-project packaging and rollout shape explicit so the plugin can move from repo-local validation to team-wide reuse without redesign.

Planned work:

1. [Done] Add `devel/codex-rate-limits-plugin-notes.md` with a short section stating that the default shared model is one dedicated repo per installable plugin, while allowing multiple closely related skills inside that single plugin package. `<devel/codex-rate-limits.py:117-131>` `<devel/codex-rate-limits.py:171-226>`
2. [Done] Document the recommended team install path as a home-local plugin clone plus `~/.agents/plugins/marketplace.json`, and treat repo-local marketplace wiring in Arcogine as a validation and development convenience rather than the primary distribution mechanism. `<devel/codex-rate-limits.py:137-169>`
3. [Done] Document when a multi-plugin repo is acceptable: only when plugins share ownership, release cadence, CI, and support boundaries; otherwise the default remains one plugin per repo.
4. [Done] Keep the plugin content under `plugins/codex-rate-limits/` free of Arcogine-specific assumptions so it can be copied or mirrored into a standalone `codex-rate-limits-plugin` repository without structural changes. `<devel/codex-rate-limits.py:117-131>` `<devel/codex-rate-limits.py:171-226>`

Files expected:
- `devel/codex-rate-limits-plugin-notes.md` (new; distribution guidance anchored to `<devel/codex-rate-limits.py:117-169>`)
- `plugins/codex-rate-limits/.codex-plugin/plugin.json` (existing from Phase 2; validated for repo independence against `<devel/codex-rate-limits.py:117-131>`)
- `plugins/codex-rate-limits/skills/check-codex-rate-limits/SKILL.md` (existing from Phase 1; validated for repo independence against `<devel/codex-rate-limits.py:137-169>`)

Acceptance criteria:
- The plan explicitly names the preferred shared distribution model as one dedicated repo per plugin, not one plugin copy per consumer repo.
- The documentation explains that one plugin may contain multiple related skills, but unrelated plugins should usually not share a repo.
- The distribution notes describe home-local installation as the default team rollout path for cross-project reuse.

Implementation Status (2026-04-20):
- Completed tasks:
  - Added `devel/codex-rate-limits-plugin-notes.md` to capture the shared distribution model for the extracted repo.
  - Documented home-local installation as the default team rollout path for reuse outside this repository.
  - Documented when multi-plugin repositories are acceptable and when they are not.
- Build/runtime fixes applied:
  - Clarified that the installable artifact remains `plugins/codex-rate-limits/`, while the repo-local marketplace file is for development convenience.

---

## 6. Validation Plan

1. Install the local plugin from `.agents/plugins/marketplace.json` in a clean repo checkout and confirm the plugin resolves to `./plugins/codex-rate-limits`.
2. Run the packaged helper script directly and confirm it returns the same normalized `5h` / `Weekly` values as `devel/codex-rate-limits.py --json --utc` for the same account.
3. Start a fresh Codex session, request the current `5h` and `Weekly` limits, and capture the response produced through the packaged skill.
4. Compare the live skill answer with both the packaged helper output and the existing developer oracle for percentages, reset times, `limitId`, and `planType`.
5. Repeat the live test with an indirect prompt to confirm the skill still activates for natural language instead of only for the exact phrase “rate limits”.
6. Verify the unsupported-path behavior by testing at least one failure mode in a disposable environment, such as missing ChatGPT auth or an older Codex build that does not return `account/rateLimits/read`, and confirm that the skill emits clear next steps rather than stale or guessed values.
7. Run `python3 scripts/quality.py ci` from the repo root and record any added markdown or JSON validation steps alongside it.
8. Review the distribution note and confirm it clearly distinguishes the short-term repo-local validation path from the long-term shared one-plugin-per-repo distribution path.

---

## 6.1 Platform And CLI Compatibility Matrix (Observed 2026-04-21)

### Native Windows-only or Windows-exposed issues

- The repo no longer depends on `make` for standard validation; the canonical runner is `python3 scripts/quality.py`.
- This machine exposes `bash.exe` but not a working `/bin/bash`, so the removed Unix-shell `Makefile` flow was not runnable through WSL on this host before the Python runner replaced it.
- The original helper and oracle implementation used `selectors` on subprocess pipes, which failed on native Windows with `WinError 10093`; both scripts now use thread-backed stream readers instead.
- Native Windows PATH resolution preferred an older `codex.CMD` shim from `@openai/codex 0.45.0`, while the working `app-server` endpoint lived behind a newer `codex.exe`; both scripts now prefer `codex.exe` on Windows when available.

### Cross-platform Codex CLI or protocol drift

- `codex plugin marketplace add` is no longer available in the current Codex CLI, so the Phase 2 and Phase 3 plugin-install validation steps are stale independently of operating system.
- `codex app-server --listen stdio://` is no longer accepted by the current Codex CLI; the current launch shape is `codex app-server`.
- The app-server JSON-RPC request contract changed: the old `initialize` payload and `account/read` request shape now fail against the current Codex build, so both helper scripts were updated to the current working request format.
- Fresh-session `codex exec` can still answer the user question in this repository, but that alone does not prove plugin installation or marketplace-driven skill routing in the current Codex build.

### Follow-up implications

- Treat native Windows support as a first-class runtime target for the helper and oracle scripts.
- Treat plugin installation and marketplace validation as blocked on current Codex CLI discovery/install semantics rather than as a Windows-only gap.
- Treat the Python runner as the canonical cross-platform validation entrypoint.

---

## 7. Implementation Order

1. Phase 1 first, because the packaged plugin should not exist until the skill contract, data model, and failure behavior are stable.
2. Phase 2 second, because plugin packaging is just the distribution wrapper around the canonical skill and should not force a second source of truth.
3. Phase 3 third, because live-session validation is only meaningful after both the skill content and the plugin packaging are in place.
4. Phase 4 last, because the shared distribution guidance should describe the validated artifact, not a hypothetical one.

---

## 8. Out of Scope

- Extending the skill to report OpenAI API RPM/TPM headers or other non-subscription rate-limit systems.
- Building a cloud service, daemon, or web UI for rate-limit monitoring.
- Packaging unrelated Codex helpers, MCP servers, hooks, apps, or assets into the same plugin.
- Replacing `devel/codex-rate-limits.py` before the packaged skill has been validated against it.
- Delivering a zero-script packaged implementation when that would require moving substantive runtime logic back into markdown instructions.
- Standardizing a shared multi-plugin monorepo for unrelated plugins as the default team model.

---

## Findings

### F1: Replace The Inline Runtime Idea With One Tiny Packaged Helper
<!-- severity: minor -->
<!-- dimension: best-practices -->

**Context:** The earlier version of the plan leaned toward a markdown-first runtime path with an inline `python3` snippet in `SKILL.md`, even though the proven workflow already spans request assembly, subprocess handling, normalization, and error paths. `<devel/codex-rate-limits.py:17-57>` `<devel/codex-rate-limits.py:116-226>`

**Issue:** Keeping that amount of runtime logic inline would make the reusable artifact harder to version, review, and validate than a single dedicated helper file.

**Recommendation:** Package one tiny stdlib-only helper script inside the skill and let the skill delegate execution to it.

**Choices:**
- [x] Use one bundled helper script as the runtime surface.
- [ ] Keep the runtime flow inline in `SKILL.md`.

Status: Applied.

### F2: Decouple The Packaged Skill From The Repo Utility
<!-- severity: minor -->
<!-- dimension: best-practices -->

**Context:** The current repo utility already proves the endpoint and output contract, but the user asked for a portable packaged skill/plugin rather than another repo-bound wrapper. `<devel/codex-rate-limits.py:116-219>` `<devel/codex-rate-limits.py:267-280>`

**Issue:** If the plan had treated `devel/codex-rate-limits.py` as a plugin runtime dependency, the skill would only be portable inside this repository and would no longer be a self-contained installable workflow.

**Recommendation:** Keep `devel/codex-rate-limits.py` as a validation oracle only, and make the packaged skill self-sufficient through its own bundled helper script plus concise markdown instructions.

**Choices:**
- [x] Treat `devel/codex-rate-limits.py` as validation-only and keep the plugin self-contained.
- [ ] Make the plugin shell out to `devel/codex-rate-limits.py` at runtime.

Status: Applied.

### F3: Make Unsupported Runtime Paths Explicit
<!-- severity: minor -->
<!-- dimension: testing -->

**Context:** The existing utility already has hard failure points for missing `codex`, missing pipes, timeouts, and API errors. A packaged skill must not silently degrade past those cases. `<devel/codex-rate-limits.py:117-131>` `<devel/codex-rate-limits.py:203-215>`

**Issue:** Without an explicit unsupported-path requirement, the skill could appear to work in happy-path sessions while still giving unclear or misleading results when the runtime lacks ChatGPT auth or the local Codex build does not expose the rate-limit endpoint.

**Recommendation:** Add explicit failure-behavior requirements to the skill design and validate at least one unsupported runtime path before calling the plugin complete.

**Choices:**
- [x] Require clear unsupported-path messaging and validate at least one failure mode.
- [ ] Limit validation to the success path and defer failure handling to later.

Status: Applied.

### F4: Name The Validation Documentation File Up Front
<!-- severity: minor -->
<!-- dimension: plan-hygiene -->

**Context:** The plan rule requires every task to name the files it will touch, but the initial validation phase described a note under a directory rather than an exact file path. `<.cursor/rules/analysis-to-plan.mdc:99-103>` `<README.md:94-115>`

**Issue:** A directory-level placeholder weakens implementation clarity and makes the validation/documentation step less testable than the rest of the plan.

**Recommendation:** Choose a single explicit fallback documentation file now and keep it conditional on validation revealing a real need.

**Choices:**
- [x] Reserve `devel/codex-rate-limits-plugin-notes.md` as the single repo-facing note for installation and distribution guidance.
- [ ] Leave the documentation target open between `devel/` and `docs/`.

Status: Applied.

### F5: Make The Shared Distribution Topology Explicit
<!-- severity: minor -->
<!-- dimension: gaps -->

**Context:** The earlier revision improved the packaged runtime design, but it still left the cross-project rollout shape implicit even after the user asked whether one-plugin-per-repo or a bigger multi-plugin repo was better.

**Issue:** Without an explicit distribution phase, implementers could finish the plugin and still make inconsistent rollout choices across teams and repositories.

**Recommendation:** Add a dedicated distribution phase and state the default clearly: one dedicated repo per installable plugin, with multiple related skills allowed inside that plugin.

**Choices:**
- [x] Add an explicit distribution phase and document one-plugin-per-repo as the default shared model.
- [ ] Leave distribution as an unwritten follow-up decision after implementation.

Status: Applied.

### Summary

| # | Title | Severity | Dimension | Depends on |
|---|-------|----------|-----------|------------|
| F1 | Replace The Inline Runtime Idea With One Tiny Packaged Helper | minor | best-practices | — |
| F2 | Decouple The Packaged Skill From The Repo Utility | minor | best-practices | — |
| F3 | Make Unsupported Runtime Paths Explicit | minor | testing | — |
| F4 | Name The Validation Documentation File Up Front | minor | plan-hygiene | — |
| F5 | Make The Shared Distribution Topology Explicit | minor | gaps | — |

Final sweep result: zero critical findings, zero major findings.
