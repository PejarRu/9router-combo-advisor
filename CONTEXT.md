# 9Router Combo Advisor: Session Handoff

Read this file before making changes. It is the current operational context for this repository.

## Goal

Maintain the model fallback combos served by the public 9Router gateway at `https://9router.antonberzins.com/v1`.

The user wants logical, purpose-specific chains, not generic model lists:

- `main`: reliable autonomous coding/reasoning using paid subscriptions, never OpenRouter.
- `extra-smart`: maximum capability for exceptionally difficult work; cost/latency are secondary.
- `free-smart`: strongest practical free chain for agentic work.
- `free-fast`: free, lightweight/quick work.
- `gemini`, `mistral`, `venice-smart`, `venice-cheap`: provider-specific chains.

The gateway is production on Hetzner, container `9router`. Do not confuse it with local OpenCode configuration or the unrelated mobile S10dev setup.

## Source Of Truth

- Live combo contents: gateway `GET /api/combos`, queried from inside the container with the CLI token.
- Models and active connections: `GET /api/providers` and `GET /api/providers/{connectionId}/models`.
- Local proposal: `proposal.json` is generated output, not source of truth after a later apply.
- Gateway commands use SSH alias `hetzner` and container name `9router`.
- `advisor.py` contains `REMOTE_SCRIPT`, which calculates the CLI token from `/app/data/machine-id` and `/app/data/auth/cli-secret`; never put either value in docs or chat.

## Current Production Combos

Applied on 2026-10-14. The latest backup before apply is `combos-backup-20261014T095823Z.json`.

### main

```text
codex/gpt-5.6-terra
codex/gpt-5.5
github/gpt-4.1
```

Purpose: dependable subscription-backed work. It deliberately excludes OpenRouter because that account currently has no usable credit.

### extra-smart

```text
codex/gpt-6.1-sol
codex/gpt-6-astra
codex/gpt-6-sol
openrouter/anthropic/claude-fable-5.1
openrouter/anthropic/claude-opus-5
openrouter/gpt-6-astra
codex/gpt-5.6-terra
codex/gpt-5.5
```

Purpose: hardest work, such as difficult reasoning, research and high-stakes engineering. The OpenRouter entries are intentional frontier fallbacks, but will currently return 402 until that gateway account has credit.

### free-smart

```text
gemini/gemini-3.8-flash
gemini/gemini-3.7-flash
gemini/gemini-3.6-flash
openrouter/qwen/qwen3.8-27b:free
openrouter/cohere/north-mini-code:free
gemini/gemini-3.1-pro-preview
gemini/gemini-3.5-flash
gemini/gemini-3.5-flash-lite
gemini/gemini-3-flash-preview
gemini/gemini-3.1-flash-lite-preview
```

Order is intentional: Gemini 3.8/3.7/3.6 have materially better OpenRouter benchmark evidence than North Mini. Qwen is kept before North Mini as the user-preferred general fallback.

### free-fast

```text
openrouter/thinkingmachines/inkling-small:free
openrouter/thinkingmachines/inkling:free
openrouter/cohere/north-mini-code:free
openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
openrouter/google/gemma-4-31b-it:free
openrouter/nvidia/nemotron-3-super-120b-a12b:free
openrouter/nvidia/nemotron-3.5-lightning:free
openrouter/dots-studio/dots-3-note-preview:free
```

### gemini

Only `gemini/gemini-*` models. `gemma-*` must never enter this combo. The current ordering uses available intelligence, coding and agentic scores, not version number alone.

```text
gemini/gemini-3.8-flash
gemini/gemini-3.6-flash
gemini/gemini-3.7-flash
gemini/gemini-3.1-pro-preview
gemini/gemini-3.5-flash-lite
gemini/gemini-4-argon
gemini/gemini-3.1-flash-lite-preview
gemini/gemini-2.5-pro
```

### mistral

```text
mistral/mistral-medium-3-5
mistral/codestral-2508
mistral/codestral-latest
mistral/mistral-code-latest
mistral/mistral-code-fim-latest
mistral/mistral-small-2603
```

### Venice

- `venice-smart`: capability-oriented, Venice-only.
- `venice-cheap`: price-oriented, Venice-only.
- Venice is not currently desired for normal work, but those combos remain intentionally available.

## Critical Architecture: Codex Accounts

There are two active Codex OAuth connections:

- Plus: `berzinsanton@gmail.com`, priority 1.
- Go: `karenamaya1086@gmail.com`, priority 2.

**9Router only recognizes the real provider ID `codex`.** It does not recognize made-up routing prefixes such as `codex_1` or `codex_2`.

Correct behavior for `codex/gpt-5.6-terra`:

1. 9Router picks the Plus connection first.
2. On quota/error, it marks that account/model unavailable and retries another active `codex` connection, i.e. Go.
3. If Go does not support that model, the combo proceeds to the next model, notably `codex/gpt-5.5`.

The previous `codex_1/...` and `codex_2/...` combo design produced `404 No credentials for codex_1/2` even though OAuth status in the UI was active. This is resolved; never reintroduce those prefixes.

## Known Current Constraints

- OpenRouter account configured in the gateway has insufficient credit: paid OpenRouter models return HTTP 402. Do not put them in `main`; their presence in `extra-smart` is an intentional future fallback.
- Gemini may return 429 when its student/free quota is exhausted.
- Mistral may return 429 when its quota is exhausted.
- `github/gpt-5.6-luna` is rejected by GitHub Copilot Responses (`400 model_not_supported`); use `github/gpt-4.1` in `main` instead.
- `--no-smoke` is deliberately used when applying `extra-smart`: public smoke probes cannot prove subscription models and would remove paid models merely because the gateway's OpenRouter account has no funds.

## Advisor Workflow

```bash
cd "/home/tonb/Desktop/Workspace/Proyectos de trabajo/_activos/9router-combo-advisor"
python3 -m unittest -q
python3 advisor.py                 # proposal + smoke
printf 'APPLY\n' | python3 advisor.py --apply
```

For `extra-smart`, preserve its paid frontier models even while OpenRouter lacks funds:

```bash
printf 'APPLY\n' | python3 advisor.py --no-smoke --apply
```

`--jev` is optional. The user values JEV as an informed selector but does not want fabricated claims or blindly deterministic rankings. OpenRouter benchmark data fetched by `fetch_or_benchmarks()` is evidence, not an excuse to infer capability solely from a model name, context window or parameter count.

Before any apply:

1. Run tests.
2. Read the printed proposed ordering.
3. Confirm every provider prefix is a real 9Router provider.
4. Do not accidentally restore removed combos: `no-filter`, `premium`, `reason`, `venice-only`, `smart`, `value`, `fast`.

## Local OpenCode Configuration

Path: `/home/tonb/.config/opencode/opencode.json`.

- Default: `9router/free-smart`.
- `9router/extra-smart` is registered as `Extra Smart`.
- The local custom agents were fixed to stop referring to removed combos:
  - explorer → `9router/free-smart`
  - scout → `9router/main`
  - hunter → `9router/extra-smart`

OpenCode only reads config at startup. Restart it after changing the JSON. Other machines need their own `extra-smart` model entry if the user wants it selectable there.

## Code Map

- `advisor.py`: catalog fetch, normalization, benchmark enrichment, selection, smoke test and remote apply.
- `test_advisor.py`: unit tests; current expected result is `11 tests OK`.
- `proposal.json`: latest generated proposal.
- `combos-backup-*.json`: automatic pre-apply backups.
- `README.md` and `PROPOSITO.md`: user-facing usage/purpose docs; update if combo names/objectives change.

## Do Not Repeat These Mistakes

- Do not treat 9Router connection UUIDs as callable provider prefixes.
- Do not infer an account is broken merely from UI status; inspect live gateway logs. Conversely, do not claim auth is broken when the actual issue is a fake provider prefix.
- Do not use old logs without a precise `--since` window; they led to a false cache diagnosis.
- Do not make `free-smart` start with a weaker fallback purely because it is a tool model.
- Do not include `gemma-*` in the `gemini` combo.
- Do not copy or record API keys, OAuth codes, passwords or tokens in project docs.
