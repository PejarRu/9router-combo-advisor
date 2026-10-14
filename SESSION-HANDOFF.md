# Handoff: JEV, 9Router, OpenCode local y S10dev

Fecha: 2026-10-01

## Lee primero

1. `PROPOSITO.md`
2. `README.md`
3. `CONTEXT.md`
4. Este archivo completo.
5. `~/notes/red-infra/s10/s10dev-opencode-operations.md` para infraestructura móvil.
6. `session-handoff-full.json` contiene el export nativo completo, sin modificar, de la sesión anterior.

## Objetivo actual

Convertir `9router-combo-advisor` (JEV) en controlador declarativo único. Debe:

1. Descubrir modelos/proveedores vivos.
2. Proponer y aplicar combos al gateway público 9Router.
3. Reconciliar secciones gestionadas de OpenCode local.
4. Reconciliar esas mismas secciones en S10dev dentro de la chroot.
5. Crear backup, validar, comprobar y hacer rollback si falla algún destino.
6. Mantener secretos fuera del repo.

El usuario pidió primero planificación. No implementar migración multi-target hasta revisar diseño y confirmar alcance.

## Decisión arquitectónica recomendada

Usar controlador central local, no clonar ni ejecutar JEV independientemente en cada máquina.

Interfaz prevista:

```bash
python3 advisor.py --apply --targets gateway,local,s10dev
```

Separar:

- Estado deseado de combos.
- Plantilla parcial de OpenCode.
- Targets y transportes.
- Secretos por entorno/almacén local.

Reconciliar únicamente secciones gestionadas, nunca sobrescribir `opencode.json` completo:

- `provider.9router.models`
- `model` y `small_model` cuando estén bajo gestión
- referencias de agentes a combos renombrados/eliminados
- MCP explícitamente gestionados

Preservar configuraciones específicas de cada máquina. Flujo esperado: generar → validar → backup → gateway → local → S10dev → comprobar → rollback.

## Estado del repo y advisor

Repo:

```text
/home/tonb/Desktop/Workspace/Proyectos de trabajo/_activos/9router-combo-advisor
```

Archivos centrales:

- `advisor.py`
- `test_advisor.py`
- `proposal.json`
- `PROPOSITO.md`
- `README.md`
- `CONTEXT.md`

Cambios ya realizados:

- Combo `smart` renombrado a `main` en advisor.
- Combo redundante `free` eliminado.
- Preferencia prevista para `main`: Codex primero, GitHub Copilot antes de OpenRouter de pago.
- `free-smart`: Qwen free primero, North Mini Code free segundo, después Gemini flash.
- Combo `copilot` fue explorado; revisar estado real en gateway/advisor antes de asumir que sigue activo.
- Tests alcanzaron `13/13 OK` durante cambios anteriores; volver a ejecutar tras desarrollo.

## Estado actual de OpenCode en S10dev

Config efectiva:

```text
/home/tonb/.config/opencode/opencode.json
```

default:

```text
9router/free-smart
```

small model:

```text
9router/free-fast
```

Modelos 9Router visibles y correctos tras desactivar config antigua:

```text
9router/free-fast
9router/free-smart
9router/gemini
9router/main
9router/mistral
9router/venice-cheap
9router/venice-smart
```

Causa de modelos antiguos duplicados: coexistía `/home/tonb/.config/opencode/opencode.jsonc` con `smart`, `value` y `venice-only`. Se movió a:

```text
/home/tonb/.config/opencode/opencode.jsonc.disabled-20261001
```

Backup creado antes de reparar JSON:

```text
/home/tonb/.config/opencode/opencode.json.bak-fix-20261001T085648
```

`free-smart` fue probado directamente contra gateway y devolvió HTTP 200 usando `cohere/north-mini-code:free`.

## GitHub MCP en S10dev

Problema inicial: se creó `mcp.json`, pero OpenCode no lo carga. OpenCode lee clave `mcp` dentro de `opencode.json`.

Paquete instalado localmente:

```text
/home/tonb/.config/opencode/node_modules/@modelcontextprotocol/server-github
```

Entrada añadida a `opencode.json` con `type: local`, comando `node` y ruta absoluta a `dist/index.js`.

Verificación:

```text
✓ github connected
✓ wordpress-anton connected
✓ google-search-console connected
✓ google-analytics-ga4 connected
✓ context7 connected
✗ n8n-anton failed: HTTP 503
```

El paquete npm GitHub MCP está deprecado. Migrar después al binario oficial `github-mcp-server` cuando esté instalado en chroot.

## SSH S10dev

Causa de `Cannot execute command-line and remote command`: alias `s10dev` usa `RemoteCommand` para montar/entrar en chroot. OpenSSH no admite además un comando pasado por CLI.

Se añadió alias `s10dev-cmd` sin `RemoteCommand`:

- `ssh s10dev`: sesión interactiva chroot.
- `ssh s10dev-cmd 'comando'`: automatización en Termux.

Para entrar programáticamente en chroot se usa `su -c`, `chroot /data/local/chroot-poc/rootfs` y entorno explícito. Detalles en nota global indicada arriba.

## Migración de esta conversación

OpenCode soporta:

```bash
opencode export SESSION_ID --sanitize > session-handoff-sanitized.json
opencode import session-handoff-sanitized.json
```

La sesión original local fue:

```text
ses_f30db23c5ffeEIbh8IGJrx46Is
JEV: clasificación y routing 9Router
```

Se exportó con `--sanitize` para no transportar secretos expuestos. No sustituir este archivo por export sin sanitizar.

## Seguridad urgente

Durante conversación se publicaron PAT GitHub y claves OpenRouter. Considerarlos comprometidos:

1. Revocar PAT GitHub publicado.
2. Crear token nuevo con mínimo alcance.
3. Rotar claves OpenRouter expuestas.
4. No guardar secretos en Markdown, Git ni exports sin sanitizar.
5. Revisar `opencode.json` remoto: actualmente puede contener PAT literal añadido durante diagnóstico; migrarlo a variable de entorno/almacén seguro.

## Próximos pasos sugeridos

1. Confirmar sesión importada y leer este handoff.
2. Verificar `git status`, `git diff`, `git log --oneline -10` sin modificar.
3. Auditar `advisor.py`, tests y documentación contra estado real del gateway.
4. Proponer diseño concreto de targets/adaptadores y rollback; todavía sin implementar si usuario mantiene fase de planificación.
5. Acordar formato declarativo y ownership exacto de secciones OpenCode.
6. Implementar incrementalmente con tests.
7. Probar dry-run local y S10dev.
8. Aplicar únicamente con confirmación explícita.

## Restricciones de trabajo

- No commit/push salvo petición explícita.
- No clonar repo: Workspace PC ↔ S10 ya está compartido.
- No sobrescribir configuración completa de otra máquina.
- No documentar secretos.
- Tras editar código, ejecutar tests, lint y typecheck disponibles.
