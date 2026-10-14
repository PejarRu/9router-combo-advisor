# 9Router Combo Advisor

Prototipo local. Consulta conexiones, modelos, precios, uso y combos del 9Router remoto mediante SSH. Genera `proposal.json`; solo modifica el servidor con `--apply` (confirmación escrita + backup).

## Ejecutar

```bash
python3 advisor.py
```

Claves en `.env` junto al script (está en `.gitignore`; nunca se commitea):

```bash
echo 'OPENROUTER_API_KEY=sk-or-...' > .env   # para --jev / --llm
```

Opciones:

```bash
python3 advisor.py --ssh hetzner --container 9router --output proposal.json --raw
```

Requisitos: Python 3.10+, acceso `ssh hetzner`, Docker remoto y 9Router activo.

## Flujo

1. Script entra por SSH.
2. Dentro del contenedor calcula token CLI local de 9Router.
3. Consulta `/api/providers`, `/api/providers/{id}/models`, `/api/models`, `/api/pricing`, `/api/usage/stats` y `/api/combos`.
4. Clasifica candidatos por precios, proveedor, catálogo live y benchmarks disponibles. Los nombres, tamaño y contexto no prueban capacidad.
5. Propone contenido para 8 combos: `main`, `extra-smart`, `free-smart`, `free-fast`, `venice-smart`, `venice-cheap`, `gemini`, `mistral`.

## Benchmarks y LLM razonador

Añade puntuaciones externas de calidad (0–100):

```bash
python3 advisor.py --benchmarks benchmarks.json
```

Formato:

```json
{
  "openrouter/deepseek/deepseek-v4-flash": 88,
  "deepseek/deepseek-v4-flash": 88
}
```

Filtros deterministas reducen catálogo a un máximo de 20 candidatos por combo. Elige y ordena **JEV** (`--jev`, System One: elige el modelo más listo y mejor encajado posición a posición, confianza < 0.6 → backfill) o el LLM razonador (`--llm`). Tamaños: `main` = hasta sus rutas conocidas, `extra-smart` = 8, `free-smart` = 10, `venice-smart` = 6, `venice-cheap` = 5, `free-fast` = 8, `gemini` = 8 y `mistral` = 6. Después, **smoke test** (activado por defecto, `--no-smoke` para omitir): cada candidato se puntea contra 9Router público. Un `404`, modelo no soportado o saldo insuficiente lo excluye. `free-smart` y `free-fast` son estrictos: solo conservan respuestas `alive`; ante agotamiento (`429`) o fallo total quedan vacíos en vez de redirigir silenciosamente a un modelo débil. `extra-smart` conserva sus fallbacks paid de forma intencional aunque la cuenta OpenRouter del gateway esté sin crédito. 

```bash
python3 advisor.py --jev    # selección con JEV (requiere OPENROUTER_API_KEY o TYPESAFE_API_KEY)
```

Guarda clave una vez, fuera del repo y con permisos `0600`:

```bash
python3 advisor.py --save-key
python3 advisor.py --llm
```

Ubicación: `~/.config/9router-combo-advisor/credentials.json`. `OPENROUTER_API_KEY` sigue teniendo prioridad si está definida.

Fallback predeterminado: `deepseek/deepseek-v4-flash` → `openrouter/auto` → `openrouter/free`. Puedes definir orden propio repitiendo opción:

```bash
python3 advisor.py --llm \
  --llm-model google/gemini-2.5-flash \
  --llm-model openrouter/free \
  --benchmarks benchmarks.json
```

Si todos fallan, script termina sin generar/aplicar propuesta nueva. Acceso SSH usa alias `hetzner` porque gestión `/api/*` requiere autenticación interna; dominio público `/v1/*` solo ofrece inferencia.

LLM recibe objetivos, disponibilidad, descripción, contexto, precio, moderación y benchmarks disponibles. Debe elegir IDs exactos del catálogo. `proposal.json` registra modelo solicitado/real, tokens, coste reportado y razones.

## Aplicar

```bash
python3 advisor.py --jev --apply
```

Benchmarks OpenRouter (índices intel/coding/agentic/elo) se descargan por defecto; `--no-or-scores` los omite.

Antes de escribir:

- guarda `combos-backup-<fecha>.json` local;
- muestra propuesta;
- exige escribir `APPLY` exactamente;
- actualiza combos existentes (`PUT`) y crea los nuevos (`POST`, p. ej. `venice-smart`, `venice-cheap`) mediante API interna;
- si falla una operación, restaura combos modificados y borra los recién creados.

Clasificación heurística sin benchmarks sigue siendo experimental. Revisa siempre `proposal.json`; especialmente disponibilidad, precios desconocidos y modelos Venice sin saldo.
