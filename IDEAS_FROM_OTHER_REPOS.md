# Ideas de otros repos para aplicar a 9router-combo-advisor

> **Objetivo del proyecto**: "Buscar el modelo más capaz por el menor precio que esté accesible en el momento dado" — automatización de selección costo-calidad con fallback real entre pools de cuota.

> **Clarificación arquitectura**: 
> - **9router** = Gateway/unificador de proveedores (fallback + unificación en 1 tool)
> - **JEV (TypeSafe System One)** = Responsable de ELEGIR el modelo
> - **advisor.py** = Pipeline: catálogo → clasificación → JEV → propuesta → apply → 9router

---

## Resumen de repos analizados

| Repo | Stars | Enfoque principal | Diferenciador clave |
|------|-------|-------------------|---------------------|
| **iamadhitya1/llm-router** | ~2k | Librería Python, scoring complejidad (0-1), ruta al más barato capaz | Scoring heurístico ligero, per-call cost tracking |
| **pruthvep/ai-router** | ~1k | Pipeline completo: benchmarks offline → políticas → API live + dashboard Next.js | Separación offline/online, quality-vs-cost tradeoff explícito |
| **NVIDIA-AI-Blueprints/llm-router** | ~500 | Enterprise, multimodal (texto+imagen), 2 estrategias (intent/auto) | Multimodal, CLIP+NN, OpenAI API compatible |
| **ayush-s-tomar/llm-cost-router** | ~500 | Streamlit demo, heurístico (sin LLM call), Groq-focused | Demo interactiva, dashboard de costes en vivo |
| **pruthvep/ai-router** | ~300 | Benchmarks offline → políticas → API live + dashboard Next.js | Quality-vs-cost tradeoff explícito, dashboard |

---

## Qué podemos aplicar (priorizado)

### 1. Separación Offline/Online (ai-router) ⭐⭐⭐
**Problema actual**: JEV + smoke tests + apply todo en un mismo comando. Lento, costoso (402 créditos), no repetible.
**Solución**:
- **Fase Offline** (cron/ci): 
  - Fetch catálogo → clasificación → benchmarks → JEV eval → genera `policy.json`
  - Guarda `policy.json` + `benchmark_results.json` + timestamp
- **Fase Online** (advisor --apply):
  - Lee `policy.json` → smoke test rápido → apply a 9router
- **Ventaja**: JEV no corre en producción, solo smoke test + apply = rápido, barato, repetible

### 2. Heurístico de complejidad ligero (llm-router) ⭐⭐
**Problema**: JEV caro (402 créditos) para decidir qué modelo usar.
**Idea**: Heurístico ligero (sin LLM call) para pre-filtrar/ordenar antes de JEV:
```python
def complexity_score(prompt: str) -> float:
    score = 0.0
    score += min(len(prompt) / 4000, 0.3)           # longitud
    score += 0.15 * sum(kw in prompt.lower() for kw in 
        ["analyze", "compare", "design", "debug", "refactor", "architect"])
    score += 0.1 * prompt.count("```")               # bloques código
    score += 0.05 * prompt.count("?")                # preguntas
    return min(score, 1.0)
```
**Uso**: Pre-ordenar candidatos para JEV → JEV solo evalúa top-N → ahorra créditos.

### 3. Dashboard de monitorización (ai-router/llm-cost-router) ⭐⭐
**Falta**: Visibilidad de qué modelos se usan, costes, fallbacks, latencia.
**Idea**: Dashboard simple (Streamlit/FastAPI + HTMX):
- Combos activos en 9router + última actualización
- Últimos smoke tests (OK/FAIL + latencia)
- Coste estimado por combo (basado en pricing + uso)
- Fallback chain visual (Codex → Codex → GitHub → Ranked)
- Alertas: modelo DEAD > 5min, créditos < threshold

### 4. Benchmarks offline separados (ai-router) ⭐⭐
**Actual**: JEV + benchmarks en mismo run → lento, 402 créditos.
**Separar**:
```bash
# Offline (cron nocturno)
python3 advisor.py --benchmark-only --output benchmarks.json

# Online (rápido)
python3 advisor.py --apply --policy policy.json
```
Benchmarks corren 1x/día, JEV usa resultados cacheados.

### 5. Scoring de complejidad para JEV (llm-router) ⭐
**Idea**: Pasar `complexity_score(prompt)` a JEV como feature → JEV aprende a preferir modelos baratos para prompts simples.
```json
{
  "prompt": "What is FastAPI?",
  "complexity_score": 0.12,
  "preferred_tier": "free"
}
```

### 6. Estrategias de routing configurables (NVIDIA/llm-router) ⭐
**Actual**: Solo JEV. **Añadir estrategias**:
```python
STRATEGIES = {
    "jev": "JEV completo (TypeSafe)",           # actual
    "cheapest": "Siempre el más barato vivo",   # free-smart/free-fast
    "fastest": "Menor latencia (smoke test)",   # free-fast
    "smartest": "Mayor qualityScore vivo",      # premium
    "auto": "JEV + heurístico complejidad",     # futuro
}
```
CLI: `advisor.py --strategy cheapest --apply`

### 7. Dashboard de combos activos (ai-router/llm-cost-router) ⭐
**Idea**: Endpoint `/combos/status` + UI simple:
- Tabla: Combo | Modelos | Último smoke | Latencia | Coste estimado | Fallback chain
- Alertas: Modelo DEAD > 5min, créditos OpenRouter < $10, smoke FAIL > 3 seguidos

### 8. Fallback chain visual + alertas ⭐
**Actual**: Fallback implícito en orden de modelos.
**Mejora**: `fallback_chain` explícito en config:
```json
{
  "main": {
    "models": [...],
    "fallback_chain": [
      {"pool": "codex_plus", "models": ["codex/gpt-5.6-terra", "codex/gpt-5.6-luna"]},
      {"pool": "codex_go", "models": ["codex/gpt-5.6-sol", "codex/gpt-5.6-luna"]},
      {"pool": "github_copilot", "models": ["github/gpt-6-luna", "github/gpt-5.6-luna"]},
      {"pool": "ranked", "models": "auto"}
    ]
  }
```
UI: Visualización cadena + estado de cada pool (OK/DEGRADED/DEAD).

### 9. Multimodal routing (NVIDIA) - futuro
Si 9router soporta imágenes → auto-router con CLIP embeddings.

---

## Qué NO aplicar (diferencia de arquitectura)

| Feature | Otros repos | Por qué NO en nuestro caso |
|---------|-------------|----------------------------|
| Client-side library | llm-router, ai-router | Nosotros somos gateway-side (9router config) |
| Single-provider routing | llm-router | Tenemos multi-pool con fallback explícito |
| LLM-based routing | NVIDIA auto-router | JEV ya hace esto mejor (TypeSafe) |
| Multimodal routing | NVIDIA | 9router no soporta imágenes aún |
| Client SDK | ai-router, llm-router | 9router es gateway, clientes usan OpenAI SDK estándar |

---

## Plan de implementación sugerido

| Sprint | Entregable |
|--------|------------|
| 1 | Separar `--benchmark-only` → genera `benchmarks.json` + `policy.json` |
| 2 | `--apply` usa `policy.json` + smoke test rápido (sin JEV en prod) |
| 3 | Heurístico `complexity_score()` para pre-ordenar antes de JEV |
| 4 | Endpoint `/status` + dashboard simple (HTMX/Streamlit) |
| 5 | `fallback_chain` explícito en config + visualización |
| 6 | Estrategias `--strategy` (cheapest/fastest/smartest/auto) |

---

## Referencias de código útil

| Repo | Archivo clave | Qué copiar/adaptar |
|------|---------------|-------------------|
| ai-router | `src/ai_router/benchmark/` | Pipeline benchmarks offline |
| ai-router | `src/ai_router/policy/` | Generación policy.json |
| ai-router | `dashboard/` | Next.js dashboard → adaptar a HTMX |
| llm-router | `llmrouter/scoring.py` | Heurístico complejidad |
| llm-router | `llmrouter/router.py` | Estrategias routing |
| NVIDIA | `src/nat_sfc_router/` | Auto-router CLIP+NN (futuro) |
| llm-cost-router | `app.py` | Heurístico complejidad simple |

---

## Próximos pasos inmediatos

1. **Fix inmediato**: Main combo tiene duplicados (`codex/gpt-5.6-sol` x2) y modelos dead → fix `propose()` + re-run `--apply`
2. **Sprint 1**: `--benchmark-only` + `policy.json` + `--apply --policy policy.json`
3. **Sprint 2**: Heurístico `complexity_score()` + `--strategy cheapest/fastest/smartest`
4. **Sprint 3**: Dashboard HTMX + endpoint `/status`

---

## Notas finales

> **Nuestra fortaleza única**: Gestión explícita de pools de cuota (Codex×2, GitHub, OpenAI) con fallback real entre cuentas. Los otros repos no hacen esto — su fallback es "otro modelo" no "otra cuenta con pool distinto".

> **No copiar ciegamente**: Nuestra arquitectura gateway-side + JEV + multi-pool es única. Adaptar ideas, no copiar arquitectura.