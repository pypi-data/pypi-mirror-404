# Project Log

## Quick Start for Next Session
- Repo: /Users/blabaschin/Documents/GitHub/mltrack
- Context: MLTrack is a drop-in MLflow enhancement with CLI, deployment, UI, and marketing site.
- Latest summary: /tmp/mltrack_review_summary.md
- Active issues to address:
  - Config validation + YAML error handling in `src/mltrack/config.py`.
  - README API examples vs. actual public API (`get_last_run`, `deploy`).
  - DataStore MLflow logging should avoid run mis-attribution.
  - UI experiment detail actions (new run/export/share) are TODOs.

## 2025-02-14 Session
- Start: Received request to proceed with fixes from review.
- Plan:
  - Align config validation with tests and Pydantic v2.
  - Update README to reflect actual API or add wrapper functions.
  - Add MLflow logging guard in DataStore with tests.
  - Implement lightweight UI actions for export/share/new run.
- Status: In progress.

- Work completed:
  - Updated config validation to keep relative file URIs, handle invalid YAML, and create parent directories on save.
  - Added MLflow logging guard in DataStore; added tests for active-run matching.
  - Hardened doctor command when config load fails; config command now uses model_dump; added test.
  - Updated README deployment examples to CLI usage; implemented export/share/new run actions in UI.
- Tests:
  - uv run pytest tests/test_config.py -q
  - uv run pytest tests/test_data_store.py -q
  - uv run pytest tests/test_doctor_command.py -q
- Notes:
  - uv.lock was updated by uv run.
  - CLI deploy commands remain documented but not implemented.

## 2025-02-14 Session (continued)
- Work completed:
  - Added public API helpers `get_last_run` and `deploy` in `src/mltrack/api.py` and exported via `src/mltrack/__init__.py`.
  - Added CLI commands for `save`, `ship`, `serve`, `try`, `list`, and `deploy` using SmartCLI + API helpers.
  - Restored Python API examples in `README.md` and added deployment API snippet in `docs/deployment.md`.
  - Added tests for public API and new CLI commands.
- Tests:
  - uv run pytest tests/test_public_api.py tests/test_cli_deploy_commands.py -q
- Notes:
  - uv.lock still updated by uv run.

## 2025-02-14 Session (docker/lambda)
- Work completed:
  - Added Lambda package builder (`src/mltrack/deploy/lambda_deploy.py`) and exported via `src/mltrack/deploy/__init__.py`.
  - Extended public deploy API to support `platform="docker"` and `platform="lambda"` with new options.
  - Wired CLI deploy flags for docker/lambda options.
  - Added tests for docker/lambda API + CLI paths.
  - Updated docs with docker/lambda deploy commands and lambda packaging note.
- Tests:
  - uv run pytest tests/test_public_api.py tests/test_cli_deploy_commands.py -q

- Work completed:
  - Added CLI deploy output messages for docker images and lambda packages.
- Tests:
  - uv run pytest tests/test_cli_deploy_commands.py -q

## 2025-02-14 Session (docs + OSS)
- Work completed:
  - Drafted docs + OSS strategy outline in `docs/STRATEGY_OUTLINE.md`.

## 2026-01-18 Session
- Start: Plan LLM tracking schema normalization (no code changes).
- Work completed:
  - Initialized Beads (`bd init`).
  - Created LLM normalization plan beads `mltrack-1` through `mltrack-5` with dependencies.
  - Copied global and local `AGENTS.md` from `/Users/blabaschin/Documents/GitHub/monohelix/projects/data_generation/AGENTS.md`.
  - Documented canonical LLM schema and audit in `.projects/specs/mltrack/llm-schema.md`.
  - Closed bead `mltrack-1` (canonical schema audit).
  - Marked bead `mltrack-2` as in progress and added failing canonical schema tests in `tests/test_llm_normalization.py`.
  - Added `.beads/*.db` to `.gitignore` and ran `bd sync -m "Update beads"`.
  - Implemented canonical LLM normalization + tagging in `src/mltrack/llm.py`.
  - Closed bead `mltrack-2` (tests complete) and set `mltrack-3` to in progress.
  - Investigated Beads JSONL label drops; `bd export -o .beads/issues.jsonl` restores labels after `bd update/close`.
  - Removed LLM param/error logging and legacy mltrack tags from LLM tracking.
  - Expanded provider detection for Gemini/Bedrock and tightened token normalization edge cases.
  - Simplified `track_llm_context` to remove unused aggregation logic.
  - Updated legacy LLM tests to match canonical tagging/metrics.
- Tests:
  - uv run pytest tests/test_llm_normalization.py -q
  - uv run pytest tests/test_llm.py tests/test_llm_normalization.py -q
- Notes:
  - No ready beads; `mltrack-3` in progress.
  - Use `bd --no-auto-flush` for updates and then `bd export -o .beads/issues.jsonl` to preserve labels.

## 2026-01-18 Session (continued)
- Work completed:
  - Removed legacy LLM helpers (LLMMetrics/LLMRequest/LLMResponse, extract_llm_params, extract_token_usage).
  - Added provider inference for model prefixes and langchain/litellm edge cases.
  - Expanded normalization for Gemini totalTokenCount and Bedrock token count variants.
  - Closed bead `mltrack-3` (normalization implementation).
- Tests:
  - uv run pytest tests/test_llm.py tests/test_llm_normalization.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead update.
  - `bd ready` shows `mltrack-4` and `mltrack-5` ready (not started).

## 2026-01-18 Session (continued)
- Work completed:
  - Completed T4: aligned UI analytics to canonical LLM schema.
  - Added shared LLM metric/tag helpers in `ui/lib/utils/llm-metrics.js`.
  - Updated dashboards + API routes to use canonical llm.* tags/metrics (cost, tokens, latency, provider/model).
  - Updated MLflow client LLM run filtering to detect llm tags/metrics.
  - Extended run tag extraction to include `llm.model`/`llm.provider` and run type detection via helper.
- Tests:
  - node --test ui/tests/llm-metrics.test.js
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead update.
  - `mltrack-5` is ready (not started).

## 2026-01-18 Session (continued)
- Work completed:
  - Completed T5: pruned legacy LLM API surface and examples.
  - Removed `LLMTracker` stub and exported `track_llm` + `track_llm_context` at top-level.
  - Updated LLM docs/examples to match canonical LLM tags/metrics and real APIs.
  - Reworked `examples/llm_demo_simple.py` to avoid non-existent helpers and config claims.
- Tests:
  - uv run pytest tests/test_llm.py tests/test_public_api.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead updates.

## 2026-01-18 Session (continued)
- Work completed:
  - Created new LLM tracking beads (T6-T11) for telemetry spec, provider adapters, pricing, streaming/async, UI enhancements, and data quality tests.
  - Added dependencies: T7->T6, T8->T6, T9->T7, T10->T6/T7/T8, T11->T7/T8/T9.
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead creation.

## 2026-01-18 Session (continued)
- Work completed:
  - Completed T6: updated canonical LLM telemetry spec with metadata tags and artifacts.
  - Documented provider mappings for finish reason and request/response IDs.
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead update.

## 2026-01-18 Session (continued)
- Work completed:
  - Completed T7: added provider metadata normalization for finish reason and request/response IDs.
  - Added tests for OpenAI/Anthropic/Gemini/Bedrock metadata tags.
- Tests:
  - uv run pytest tests/test_llm_normalization.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead update.

## 2026-01-19 Session
- Start: Investigate MCP web-search startup handshake failure.
- Work completed:

## 2026-01-25 Session
- Start: Smoke-test analytics page.
- Work completed:
  - Started Next dev server on port 3001 and requested `/analytics` (HTTP 200).
  - Captured dev server log; observed Watchpack EMFILE (too many open files) warnings.
- Notes:
  - `nice(5) failed: operation not permitted` appeared but did not block startup.
  - Playwright headless browser launch failed (Mach port permission denied in Chromium; WebKit abort trap), so automated visual screenshots could not be captured.
  - Headless Chrome screenshot workaround succeeded; forced dev auth via localStorage and captured analytics page. Page renders layout + filters but no data panels (empty state). Dev auth banner remains.
  - Redirected web-search MCP logs to stderr to keep stdout clean for MCP JSON-RPC.
  - Updated the web-search `mcp.json` to point at the local dist entrypoint.
- Tests:
  - Manual: ran the MCP server with stdout/stderr capture (stdout empty).
- Notes:
  - Changes live under `/Users/blabaschin/.config/claude/mcp-servers/web-search/`; restart the MCP client to reload.

## 2026-01-19 Session (continued)
- Work completed:
  - Completed T8: LiteLLM-based pricing snapshot normalization and cost engine (`src/mltrack/pricing.py`).
  - Added Vertex AI as a distinct provider for detection, usage normalization, and metadata tags.
  - Integrated cost logging to skip missing pricing; updated LLM docs and schema spec.
  - Added `scripts/refresh_pricing_snapshot.py` and generated `src/mltrack/data/litellm_snapshot.json`.
  - Added pricing unit tests and updated LLM cost tests.
  - Closed bead `mltrack-8` (pricing + cost engine).
- Tests:
  - uv run pytest tests/test_pricing.py tests/test_llm.py tests/test_llm_normalization.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead update.

## 2026-01-20 Session
- Work completed:
  - Added snapshot refresh helpers (`build_litellm_snapshot`, `needs_snapshot_refresh`) and tests.
  - Updated `scripts/refresh_pricing_snapshot.py` to skip writes when the LiteLLM hash is unchanged.
  - Hooked snapshot refresh into the publish workflow so releases always carry the latest snapshot.
  - Closed bead `mltrack-12` (pricing snapshot refresh hook).
- Tests:
  - uv run pytest tests/test_pricing.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead updates.

## 2026-01-20 Session (continued)
- Work completed:
  - Added async + streaming tracking for `track_llm` with safe run finalization.
  - Added streaming/async tests and pinned anyio backend to asyncio for these tests.
  - Documented streaming + async tracking in `docs/llm-tracking.md`.
  - Closed bead `mltrack-9` (streaming + async tracking).
- Tests:
  - uv run pytest tests/test_llm_streaming.py -q
  - uv run pytest tests/test_llm.py tests/test_llm_normalization.py -q
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead updates.

## 2026-01-20 Session (continued)
- Work completed:
  - Completed T10: added provider filter UI for analytics and scoped LLM dashboards to provider/LLM runs.
  - Added optional token breakdown helpers and cache/tool token visibility in the token dashboard.
  - Switched token dashboard cost aggregation to `llm.cost_usd` metrics.
  - Added UI helper tests for provider filtering and optional token metrics.
  - Closed bead `mltrack-10` (UI LLM analytics enhancements).
- Tests:
  - node --test ui/tests/llm-metrics.test.js
- Notes:
  - Used `bd --no-auto-flush` and `bd export -o .beads/issues.jsonl` after bead updates.

## 2026-01-20 Session (continued)
- Work completed:
  - Smoke-tested analytics build via `next build` for the UI.
- Tests:
  - npm --prefix ui run build (failed: missing `@/components/deployments/DeployButton` in `ui/app/(dashboard)/runs/[runId]/page.tsx`).

## 2026-01-20 Session (continued)
- Work completed:
  - Fixed run detail page import to use app-scoped `DeployButton`.
  - Retried UI build to smoke-test analytics.
- Tests:
  - npm --prefix ui run build (failed: ESLint/TS errors across multiple UI files, including `ui/app/(dashboard)/analytics/page.tsx` unused imports).
