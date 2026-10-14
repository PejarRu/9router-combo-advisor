# S10dev móvil — Infraestructura completa (oct 2026)

## Acceso
- `ssh s10dev`: SSH por Tailscale (100.127.50.109:2222). Entra al chroot y adjunta tmux `work`.
- `ssh s10dev-cmd 'COMANDO'`: ejecuta comandos en Termux host; útil para automatización.
- `mosh-s10dev`: alternativa interactiva resiliente a suspensión, cambios Wi-Fi/datos y cambios de IP. Entra al mismo chroot y tmux `work`.

Mosh usa SSH únicamente para autenticación inicial y después UDP sobre Tailscale. No reemplaza ni modifica SSH, SCP, claves, puertos o aliases existentes.

## Mosh
**Cliente local (instalado sin root):**
- `~/.local/bin/mosh-s10dev` — wrapper principal
- `~/.local/bin/mosh.pl` — cliente Perl
- `~/.local/bin/mosh-client` — binario cliente

**Escape key:** `Ctrl-]` (configurado via `MOSH_ESCAPE_KEY=^]` en `~/.local/bin/mosh-s10dev`). Accesible en teclado español (era `Ctrl-^`, inaccesible).

**Servidor Termux:**
- Paquete `mosh` 1.4.0 instalado
- Wrapper: `/data/data/com.termux/files/home/scripts/mosh-s10dev-server` — monta chroot y ejecuta `chroot-poc-shell.sh`

El wrapper remoto monta el chroot y ejecuta `chroot-poc-shell.sh`; este inicia `s10dev-login`, Zsh y tmux `work` igual que SSH.

## Tmux + tmux-resurrect (en chroot)
- **Prefix:** `Ctrl-a` (era `Ctrl-b`)
- **Mouse:** ON
- **History limit:** 50000
- **tmux-resurrect:** instalado en `/data/local/chroot-poc/rootfs/home/tonb/.tmux/plugins/tmux-resurrect`
- **Auto-restore** al iniciar tmux: `run-shell ~/.tmux/plugins/tmux-resurrect/scripts/restore.sh`
- **Sesiones por defecto** (creadas al iniciar tmux): `work1`, `work2`, `work3`, `work4`, `meta`
- **Guardado manual:** `Ctrl-a S` | **Restaurar:** `Ctrl-a R`
- **s10dev-login** actualizado con `trap EXIT` → `tmux save-session -t work -p /tmp/work-session`

**Ayuda rápida:** `tmux-help` (instalado en chroot `/usr/local/bin/tmux-help`)

**Sesiones independientes dentro de tmux:**
```bash
tmux new -d -s NOMBRE        # crear sesión independiente
tmux switch-client -t NOMBRE # cambiar a sesión existente
```

## Diagnóstico y auto-reparación — s10-doctor.sh
- **Ubicación:** `~/scripts/s10-doctor.sh` (copia en `~/tonb/scripts/`)
- **29 checks** cubriendo: Termux base, SSH, runsvdir+servicios, syncthing OFF, sync periódico, mosh, tmux+resurrect, chroot/VM mounts
- **Modos:** `--fix` (auto-fix), `--full` (incluye chroot/VM)
- **Shortcut widget:** `~/.shortcuts/s10-doctor` → `~/scripts/s10-doctor.sh --fix --full`
- **Estado actual:** 29 checks pasan (0 fixes necesarios)

## Sync periódico (reemplaza Syncthing)
- **sync-daemon.sh:** bucle cada 60s, ejecuta `sync-periodic.sh`
- **sync-periodic.sh:** rsync dry-run → sync real solo si hay cambios
- **Termux:Boot:** `~/.termux/boot/sync-daemon` (auto-start al encender móvil)
- **Log:** `~/sync-periodic.log`
- **Ejecución manual:** `~/scripts/sync-daemon.sh &`

## Syncthing — ELIMINADO (oct 2026)
- **Problema:** 96% CPU sostenido → batería drenada, thermal throttling, móvil se apagaba
- **Acción:** Eliminado `/var/service/syncthing` (runsvdir), procesos kill -9, servicio deshabilitado
- **Sustituto:** Sync periódico ligero (ver arriba)

## Shortcuts para widget (Termux:Widget)
- `~/.shortcuts/s10-doctor` → `~/scripts/s10-doctor.sh --fix --full` (diagnóstico completo)
- `~/.shortcuts/start-s10-server.sh` → sshd + start-phone-server + sync-daemon

## Wake lock persistente
- `termux-wake-lock` en `~/.bashrc`
- **Termux:Boot** (instalar desde F-Droid/Play Store) → abrir una vez → permitir auto-start

## Documentación relacionada
- `notes/2026-10-07-maintenance.md` — log detallado mantenimiento oct 2026
- `notes/S10-SERVER-RUNBOOK.md` — runbook actualizado con cambios oct 2026
- `notes/tmux-help.md` — chuleta tmux completa

## Acceso rápido
```bash
# Diagnóstico completo (widget o terminal)
~/scripts/s10-doctor.sh --fix --full

# Mosh resiliente
mosh-s10dev

# Ayuda tmux
tmux-help

# Sesiones tmux independientes
tmux new -d -s NOMBRE
tmux switch-client -t NOMBRE
```