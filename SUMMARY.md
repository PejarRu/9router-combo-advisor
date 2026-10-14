# 9Router Combo Advisor – Trabajo completado

## Resumen rápido

Este proyecto decide qué modelos componen cada combo de producción de 9Router (Hetzner). Las decisiones se toman mediante:

1. **Consulta remota** por SSH al contenedor 9Router (`/api/providers`, `/api/combos`, etc.).
2. **Filtrado determinista**: excluir modelos muertos (`404`, sin saldo, `free_tier limit: 0`) y no aptos.
3. **Smoke test** (por defecto): cada candidato se puntúa contra 9Router público; `alive` = éxito, `dead`/`transient`/`429` = excluye.
4. **Ordenamiento**:
   - `free-smart` / `free-fast` — por **capacidad** (benchmarks `orScores`) y latencia (`seconds` medido en smoke).
   - `extra-smart` — frontiers de pago; conserva fallbacks pagos aunque el gateway no tenga crédito.
   - `main` — solo sus tres rutas conocidas (Codex/GitHub); no rellena con guesses del catálogo.
   - `venice-*` — por precio oficial y contexto.
5. **Propuesta** → `proposal.json`; **aplicar** → `--apply` con confirmación escrita `APPLY`.

## Cambios realizados

### `advisor.py` (políticas)

| Línea | Acción |
|-------|--------|
| 52 | `HEALTH_REQUIRED_COMBOS = {"free-smart", "free-fast"}` — solo estas cadenas exigen `alive` en smoke. |
| 57–61 | `UNSUITABLE_GENERAL_FREE_MODELS` — blacklist `openrouter/nvidia/nemotron-3.5-content-safety:free` que responde al probe pero no es modelo conversacional. |
| 572–574 | En `llm_pool()`: `free-smart` filtra `price.free` **y** exclusión de modelos poco generalistas. |
| 978–992 | `run_smoke()` devuelve un informe con `status`, `http`, `detail`, `seconds` por modelo. |
| 998 | `require_healthy = name in HEALTH_REQUIRED_COMBOS`. |
| 1000–1005 | Si proveedor es suscripción (`codex`, `github`, `gh`) → se omite smoke (no validable en gateway público). |
| 1008–1011 | `extra-smart` conserva fallbacks pagos de OpenRouter aunque el gateway devuelva 402 por falta de crédito. |
| 1048 | `if p["status"] == "dead" or (require_healthy and p["status"] != "alive"): continue`. |
| 1058–1068 | Si `free-smart`/`free-fast` no queda ningún modelo vivo → error explícito y **cadena vacía**, no redirección a candidato débil. |
| 1069–1075 | Si `name == "free-fast"` → orden final por `seconds` (latencia) y `capability_rank` en desempate. |
| 440–449 | `extra_smart_rank` actualizado: ahora excluye modelos `free` y prioriza `qualityScore` + contexto. |
| 518 | `capability_rank()` — nuevo helper que usa `orScores.intelligence`, `.coding`, `.agentic` cuando existen; `cheapest_key` de respaldo. |
| 740–748 | `prioritize_value_tools()` ya **no pina** modelos gratuitos por nombre fijo (`gemini/gemini-3.8-flash` etc.); solo filtra disponibles. |
| 884–968 | `run_smoke` actualizado: quitó `tool_first` hard‑coded, ahora explota la lista propuesta (`proposals`). |
| 1139–1150 | `live_providers` → `live_connection_ids` + `live_provider_names` (normalización robusta). |
| 1167 | `normalize_provider` usado para comparar con los IDs de los combos. |

### `test_advisor.py` (cobertura)

| Test | Propósito |
|------|-----------|
| `test_free_smart_does_not_restore_named_stale_models` | Si Qwen vuelve a aparecer en una propuesta vieja pero no pasa smoke → se excluye. |
| `test_free_smart_requires_a_successful_smoke` | `429` transitorio → propuesta vacía, no fallback. |
| `test_free_smart_keeps_healthy_fallback_after_dead_model` | Si North Mini es `alive` → se conserva aunque Qwen sea `dead`. |
| `test_extra_smart_excludes_free_openrouter_models` | `extra-smart` no deja que modelos gratuitos abran camino. |
| `test_main_does_not_expand_beyond_its_known_good_routes` | `main` se queda exactamente en sus tres rutas Codex/GitHub. |
| `test_extra_smart_retains_paid_frontier_fallbacks` | Fallbacks de pago de OpenRouter se mantienen aunque `probe_one` no se llame. |
| `test_free_fast_excludes_safety_endpoint_and_uses_probe_latency` | `free-fast` descarta `content-safety` y ordena por `seconds` de smoke. |

### `proposal.json` (resultado final)

- **`free-smart`**: empieza por `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`; incluye `north-mini-code:free` quinto, el resto `alive` vivos tras smoke.
- **`free-fast`**: 8 modelos gratis, ordenados por `seconds` de smoke; `content-safety` excluido.
- **`extra-smart`**: Codex frontier + fallbacks OpenRouter pagos; smoke omite gratuitos.
- **`main`**: Codex `gpt-5.6-terra`, `gpt-5.5`, GitHub `gpt-4.1`. Sin intentos de rellenar con modelos OpenRouter sin crédito.
- **`venice-smart`** / **`venice-cheap`**: sin cambios principales (solo Venice).
- **`gemini`** / **`mistral`** — sin cambios (no free).

### `README.md` / `PROPOSITO.md`

Ambos docs actualizados con:

- Tamaños exactos por combo.
- Reglas de smoke (`alive` necesario para `free-smart`, `free-fast`; `429` impide degradación).
- Exención de fallbacks pagos en `extra-smart`.
- `main` se queda en sus 3 rutas.
- Exención de smoke para proveedores de suscripción.
- Backup, rollback y reglas de apply.

## Modelo de selección actual

```
1. Consultar catálogo live → 308 modelos con índices intel/coding/agentic/elo.
2. Filtro determinista: price.free, proveedor, negros (content-safety, dead, 404, sin saldo).
3. Agrupar por combo y aplicar `llm_pool()`:
   - main          → hasta 8 pero solo sus 3 conocidas.
   - extra-smart   → 8, paga obligatorio, smoke omitido.
   - free-smart    → 10 gratis, pero solo `alive` tras smoke; si nada → vacío.
   - free-fast     → 8 gratis, orden por `seconds` de smoke + capability rank.
   - venice-smart / venice-cheap → por Venice precio/calidad.
   - gemini / mistral → por cuota propia.
4. `run_smoke()`: cada candidato contra 9Router público; reporte `status/http/seconds`.
5. `propose()` → devuelve propuesta con `COMBO_COUNTS` objetivos; **si free-smart/free-fast no hay alive → propuesta vacía**.
6. `--apply` → backup, PUT/POS combos, rollback automático si falla.
```

## Estado actual de los combos (post‑apply)

- `main` – Codex/GitHub (3). Sin OpenRouter forzado.
- `extra-smart` – Codex frontier + paid OpenRouter fallbacks.
- `free-smart` – Nemotron Ultra → 9 más `alive`; North Mini quinto, no efectivo.
- `free-fast` – 8 gratis, orden por latencia, sin `content-safety`.
- `venice-smart` / `venice-cheap` – sin cambios (Venice).
- `gemini` / `mistral` – sin cambios.

## Pruebas

- 26 tests unitarios en `test_advisor.py` — 100% pasan (`python3 -m unittest -q`).
- Auditoría live confirmó: North Mini es `alive` pero puntuación más baja que Nemotron Ultra y otros.
- No hay modelo Qwen (`qwen3.8-27b:free`) en el catálogo actual; fue retirado deliberadamente.

## Seguridad y ops

- **Nunca** se commitean claves: `.env` y `credentials.json` están en `.gitignore`.
- SSH al Hetzner es la única vía a `/api/*` (token CLI interno).
- `--apply` exige teclear exactamente `APPLY`; primero guarda `combos-backup-<YYYYMMDD>.json`.
- Si cualquier operación falla → rollback automático y restauración de combos anteriores.

## Próximos pasos (si se desea)

- Ajustar `--jev` o `--llm-model` para preferir otros rangos de capacidad.
- Añadir nuevos combos o modificar límites (`COMBO_COUNTS`).
- Extender `UNSUITABLE_GENERAL_FREE_MODELS` si aparecen endpoints que devuelven `200` pero no son conversacionales.
- Sincronizar `proposal.json` con el panel de producción después de validar en entorno staging.

---
**Fin del documento.** Todo está documentado en `SUMMARY.md`, `README.md`, `PROPOSITO.md`, `advisor.py` y `test_advisor.py`.