# Propósito de este repo

## Qué es

**9Router Combo Advisor** — script local (Python stdlib, sin dependencias) que decide qué modelos componen cada combo de 9Router (Hetzner). No es un orquestador en tiempo real: es mantenimiento periódico (cada 2–3 días).

## Qué debe hacer

1. **Consultar** por SSH (`ssh hetzner`) el estado real de 9Router: conexiones, modelos vivos, precios, uso y combos actuales. La API `/api/*` solo funciona dentro del contenedor (token CLI interno); el dominio público solo sirve inferencia `/v1/*`.
2. **Filtrar** deterministamente: excluir modelos caídos, sin saldo, caros o incompatibles con cada combo. Un modelo ausente de un catálogo live correcto no se rescata desde un combo antiguo.
3. **Proponer** con **JEV** (`--jev`, elige el modelo más listo y mejor encajado para cada posición de cada combo) o con UN LLM razonador (`--llm`), sobre los candidatos ya filtrados:
    - `main` → cadena robusta de suscripción: Codex y un fallback GitHub soportado, sin OpenRouter
    - `extra-smart` → máxima capacidad: Codex frontier y fallbacks OpenRouter de pago, nunca modelos free
    - `free-smart` → 10 modelos **realmente gratis** (`price.free=true`), de más capaz a menos; si ninguno pasa smoke, falla en vez de responder con un fallback débil
   - `venice-smart` → 6 modelos Venice más capaces para tareas complejas/agencia
   - `venice-cheap` → 5 modelos Venice más baratos (precio oficial docs.venice.ai) para tareas rutinarias
    - `free-fast` → 8 modelos gratis para tareas ligeras; requiere smoke `alive`, no usa un modelo agotado como fallback
   - `gemini` → 8 modelos Gemini (cuota gratuita estudiante)
   - `mistral` → 6 modelos Mistral (cuota Mistral propia)
4. **Smoke test** (por defecto, `--no-smoke` lo omite): puntear cada candidato contra 9Router público; excluir muertos (404, `model_not_supported`, `free_tier limit: 0`, saldo insuficiente). En cadenas free estrictas (`free-smart`, `free-fast`), un `429` también impide usar ese candidato para no disfrazar una cadena degradada como disponible.
5. **Escribir** `proposal.json` (nunca tocar producción en modo normal).
6. **Aplicar solo con `--apply`** y confirmación escrita `APPLY`: backup local → `PUT` combos existentes / `POST` combos nuevos (`venice-smart`, `venice-cheap`) → rollback automático si algo falla.

## Qué NO hace

- **No hace routing por petición** (eso es JEV runtime en Jevonian); aquí solo decide el contenido de los combos. `--jev` usa JEV como *selector* de modelos, barato y por baja frecuencia.
- **No se ejecuta solo en el VPS**: el control plane es local; VPS no corre IA.
- **No se auto-aplica**: el humano revisa `proposal.json` y teclea `APPLY`.
- **No borra combos** salvo rollback de combos creados en esa misma ejecución fallida.

## Comandos

```bash
python3 advisor.py --help          # ayuda con todos los comandos
python3 advisor.py --jev           # propuesta eligiendo con JEV (System One)
python3 advisor.py --llm           # propuesta con LLM razonador
python3 advisor.py --jev --apply   # aplicar (teclear APPLY)
python3 advisor.py --save-key      # guardar OPENROUTER_API_KEY (0600, fuera del repo)
```

Clave JEV: `TYPESAFE_API_KEY` (canal typesafe) o bien `OPENROUTER_API_KEY` (canal `typesafe/jev-1.13` vía OpenRouter).

## Reglas del repo

- Eficiencia > exhaustividad; suficiente > perfecto.
- Nunca secretos en el repo (clave en `~/.config/9router-combo-advisor/credentials.json`, modo 0600).
- 1 proyecto = 1 repo = 1 remote; vive en `_activos/`.
