# tmux — Chuleta rápida S10dev (chroot)

## Prefix
**`Ctrl-a`** (era `Ctrl-b`)

## Conceptos clave
- **sesión** — entorno persistente con ventanas y procesos
- **attach** — entrar desde fuera de tmux en una sesión existente
- **switch** — cambiar de sesión cuando ya estás dentro de tmux
- **detach** — salir de la vista sin cerrar procesos: `Ctrl-a`, luego `d`
- **ventana** — terminal completa dentro de una sesión
- **panel** — división de una ventana

## Sesiones
```bash
tmux new -s NOMBRE         # crear y entrar en sesión nueva
tmux ls                    # listar sesiones
tmux attach -t NOMBRE      # entrar en sesión existente (desde fuera)
tmux kill-session -t NOMBRE # cerrar sesión y sus procesos
```

**Dentro de tmux (cambio de sesión):**
```bash
tmux switch-client -t NOMBRE  # cambiar a otra sesión
tmux new -d -s NOMBRE         # crear sesión independiente
tmux rename-session -t VIEJO NUEVO
```

**Si no haces attach:** no ves la sesión existente; sus procesos siguen funcionando. Crea otra con nombre distinto o entra con `tmux attach -t NOMBRE`.

## Atajos (primero `Ctrl-a`, soltar, luego tecla):

### Sesiones
- `d` — detach (salir sin cerrar)
- `s` — selector de sesiones (lista interactiva)
- `(` / `)` — sesión anterior / siguiente
- `$` — renombrar sesión actual

### Ventanas
- `c` — crear ventana nueva
- `n` / `p` — ventana siguiente / anterior
- `0-9` — ir a ventana por número
- `,` — renombrar ventana actual
- `w` — selector de ventanas (lista interactiva)
- `&` — cerrar ventana (con confirmación)

### Paneles
- `"` — dividir horizontal (panel arriba/abajo)
- `%` — dividir vertical (panel izquierda/derecha)
- `o` — siguiente panel
- `;` — panel anterior
- `q` — mostrar números de panel (luego pulsar número)
- `{` / `}` — mover panel actual
- `z` — ampliar/restaurar panel (zoom)
- `x` — cerrar panel (con confirmación)
- `Space` — cambiar layout

### Copia / Scroll
- `[` — entrar en modo copia/scroll
- `]` — pegar buffer
- `Space` — iniciar selección (en modo copia)
- `Enter` — copiar selección
- `q` — salir modo copia

### Otros
- `?` — ayuda nativa completa (lista todos los atajos)
- `:` — escribir comando tmux (ej: `:rename-session nuevo`)
- `t` — mostrar reloj

## tmux-resurrect (instalado)
- **Guardado manual:** `Ctrl-a S` (guarda sesión actual en `~/.tmux/resurrect/`)
- **Restaurar manual:** `Ctrl-a R` (restaura última sesión guardada)
- **Auto-restore:** al iniciar tmux, restaura automáticamente última sesión
- **Dir guardado:** `~/.tmux/resurrect/`
- **Procesos restaurados:** vim, nvim, ssh, mosh, opencode, etc.

## Sesiones por defecto (creadas al iniciar tmux)
- `work1` — trabajo principal
- `work2` — trabajo secundario
- `work3` — tareas varias
- `work4` — reserva
- `meta` — meta-tareas / admin

## Mosh (escape key)
- **Salir de mosh:** `Ctrl-]` (luego `.` para desconectar)
- Configurado en `~/.local/bin/mosh-s10dev` con `MOSH_ESCAPE_KEY=^]`

## Acceso rápido
```bash
tmux-help          # esta ayuda
mosh-s10dev        # conexión Mosh resiliente
tmux new -s NOMBRE # sesión independiente
tmux ls            # listar sesiones
tmux attach -t work # entrar en work
```

## Notas
- Al entrar por SSH/Mosh ya estás dentro de tmux sesión `work`.
- No uses `tmux attach` desde dentro: produciría "sessions should be nested".
- `Ctrl-a d` = detach (sesión persiste). `exit` en shell = cierra panel/ventana.
- `s10dev-login` guarda sesión automáticamente al salir (`trap EXIT`).