# CLI Simplification & Developer Experience Roadmap

**Status**: Open
**Priority**: High
**Created**: 2026-01-26

## Vision

Prism's værdi ligger i at generere en komplet enterprise/SaaS-løsning "out of the box" som udviklere kan fylde ud. Den nuværende CLI har ~37 kommandoer, hvilket er overvældende for nye brugere.

**Målsætning**: Gør `prism init` + `prism dev` til den primære workflow - alt andet er opt-out eller power-user funktionalitet.

## Problem

### Nuværende CLI Struktur (~37 kommandoer)

```
prism create|generate|dev|install|validate|schema|test
prism ci (init|status|validate|add-docker)
prism db (init|migrate|reset|seed)
prism deploy (init|plan|apply|destroy|ssh|logs|status|ssl)
prism docker (init|init-prod|build-prod|down|logs|shell|backup-db|restore-db|reset-db)
prism projects (list|down-all)
prism review (list|show|diff|clear|mark-reviewed|mark-all-reviewed|summary|restore)
```

### Issues med nuværende tilgang

1. **For mange valg**: Nye brugere ved ikke hvor de skal starte
2. **Manuel regenerering**: `prism generate` skal køres manuelt efter spec-ændringer
3. **Ingen version-tracking**: Ingen notifikation om nye Prism-versioner
4. **Opt-in for fuld stack**: Docker, docs, deploy skal aktiveres eksplicit

## Løsningsdesign

### 1. Interaktiv Wizard (`prism init`)

Erstatter `prism create` med en interaktiv wizard der:
- Spørger om projekt-navn og beskrivelse
- Vælger komponenter (med "alle" som default)
- Gemmer valg til `.prism/config.yaml`

```yaml
# .prism/config.yaml (auto-genereret af wizard)
prism_version: "0.8.0"
components:
  backend: true
  frontend: true
  docker: true      # Default: true (opt-out)
  deployment: true  # Default: true (opt-out)
  mcp: true         # Default: true (opt-out)
  ci: true          # Default: true (opt-out)
  docs: false       # User valgte fra
regeneration:
  auto: true        # Auto-regen når spec ændres
  watch_files:
    - "prism.yaml"
    - "spec/*.yaml"
```

**Wizard flow**:
```
$ prism init my-app

? Project name: my-app
? Description: My awesome SaaS application

Prism generates a full-stack enterprise solution by default.
You can opt-out of components you don't need.

? Generate all components? (Docker, Deployment, MCP, CI/CD, Docs)
  > Yes, give me everything (Recommended)
    No, let me choose

Creating project...
✓ Generated backend (FastAPI + SQLAlchemy)
✓ Generated frontend (React + TypeScript)
✓ Generated Docker configuration
✓ Generated deployment templates
✓ Generated MCP server
✓ Generated CI/CD workflows

Your project is ready! Run:
  cd my-app
  prism dev
```

### 2. Smart Development Mode (`prism dev`)

`prism dev` bliver "one-stop-shop" der:

1. **Starter services** (backend, frontend, docker if configured)
2. **Watcher på spec-filer** - auto-regenererer ved ændringer
3. **Version check** - notificerer om nye Prism-versioner
4. **Kører migrationer** automatisk efter regenerering

```
$ prism dev

Starting Prism development environment...
✓ Watching prism.yaml for changes
✓ Backend running at http://localhost:8000
✓ Frontend running at http://localhost:5173
✓ MCP server at http://localhost:8001

[Auto-regen] Detected changes in prism.yaml
[Auto-regen] Regenerating... done (2.3s)
[Auto-regen] Running migrations... done
[Auto-regen] Hot reload triggered

💡 Prism 0.9.0 is available! Run: prism self-upgrade
```

### 3. Protected Regions (Inline kommentarer)

Bevar brugerens kode ved regenerering med inline markers:

**Python (backend)**:
```python
# PRISM:PROTECTED:START - Custom imports
from myapp.custom import MyService
# PRISM:PROTECTED:END

# PRISM:PROTECTED:START - Custom routes
@router.get("/custom")
async def custom_endpoint():
    return {"custom": True}
# PRISM:PROTECTED:END
```

**TypeScript (frontend)**:
```tsx
// PRISM:PROTECTED:START - Custom imports
import { MyCustomComponent } from './custom';
// PRISM:PROTECTED:END

// PRISM:PROTECTED:START - Custom routes
<Route path="/custom" element={<MyCustomComponent />} />
// PRISM:PROTECTED:END
```

**Jinja2 templates**:
```jinja2
{# PRISM:PROTECTED:START - Custom content #}
{{ user_custom_code }}
{# PRISM:PROTECTED:END #}
```

### 4. Self-Upgrade kommando

```
$ prism self-upgrade

Current version: 0.8.0
Latest version: 0.9.0

Changelog:
- Added background jobs support
- Improved protected regions
- Bug fixes

? Upgrade to 0.9.0? [Y/n] y

Upgrading...
✓ Updated prism to 0.9.0
✓ Regenerating project with new version... done

Note: Review .prism/config.yaml for any new options.
```

### 5. CLI Reorganisering

**Primære kommandoer** (hovedflow):
| Kommando | Beskrivelse |
|----------|-------------|
| `prism init [name]` | Interaktiv wizard → opretter projekt |
| `prism dev` | Start development (med auto-regen) |
| `prism build` | Build til produktion |
| `prism deploy` | Deploy til prisme.dev eller self-hosted |
| `prism self-upgrade` | Opgradér Prism CLI |

**Sekundære kommandoer** (power users):
| Kommando | Beskrivelse |
|----------|-------------|
| `prism generate` | Manuel regenerering (sjældent nødvendigt) |
| `prism validate` | Validér spec |
| `prism test` | Kør tests |

**Admin-kommandoer** (avanceret):
```
prism db [init|migrate|reset|seed]
prism docker [init|build|down|logs|shell|backup|restore]
prism ci [init|status|validate]
prism deploy [init|plan|apply|destroy|ssh|logs|ssl]
prism review [list|diff|restore|clear]
```

## Implementeringsplan

### Fase 1: Protected Regions (Forudsætning)

**Status**: Delvist implementeret

Allerede implementeret for:
- `router.tsx` (custom routes, imports, nav links)
- `App.tsx` (providers)

Mangler:
- [ ] Backend services (`services.py`)
- [ ] GraphQL resolvers
- [ ] FastAPI routes (`main.py`)
- [ ] Docker Compose files
- [ ] Template system for at definere protected regions

**Opgaver**:
1. Definer standard protected regions for alle genererede filer
2. Implementér region-parsing i template engine
3. Test at regenerering bevarer custom kode

### Fase 2: Config-fil System

**Status**: Ikke startet

**Opgaver**:
1. Design `.prism/config.yaml` schema
2. Implementér config loading i alle generatorer
3. Opdatér generatorer til at respektere opt-out valg
4. Migrationsstrategi for eksisterende projekter

### Fase 3: Interaktiv Wizard

**Status**: Ikke startet

**Opgaver**:
1. Implementér `prism init` med questionary/rich
2. Generér `.prism/config.yaml` fra wizard
3. Opdatér dokumentation
4. Deprecate `prism create` (redirect til `prism init`)

### Fase 4: Auto-regenerering i `prism dev`

**Status**: Ikke startet

**Opgaver**:
1. Tilføj file watcher (watchdog) til `prism dev`
2. Implementér incremental regenerering
3. Auto-kør migrationer efter schema-ændringer
4. Hot reload integration

### Fase 5: Version Management

**Status**: Ikke startet

**Opgaver**:
1. Version check ved `prism dev` start
2. `prism self-upgrade` kommando
3. Changelog display
4. Breaking change warnings

## Tekniske Overvejelser

### Protected Regions Implementation

```python
# prism/generators/base.py

class ProtectedRegionParser:
    """Parse and preserve protected regions in generated files."""

    MARKERS = {
        'python': ('# PRISM:PROTECTED:START', '# PRISM:PROTECTED:END'),
        'typescript': ('// PRISM:PROTECTED:START', '// PRISM:PROTECTED:END'),
        'tsx': ('// PRISM:PROTECTED:START', '// PRISM:PROTECTED:END'),
        'html': ('{/* PRISM:PROTECTED:START', 'PRISM:PROTECTED:END */}'),
        'yaml': ('# PRISM:PROTECTED:START', '# PRISM:PROTECTED:END'),
    }

    def extract_regions(self, content: str, file_type: str) -> dict[str, str]:
        """Extract named protected regions from existing file."""
        ...

    def merge_regions(self, new_content: str, old_regions: dict[str, str]) -> str:
        """Merge preserved regions into newly generated content."""
        ...
```

### Config Schema

```yaml
# .prism/config.yaml
version: 1
prism_version: "0.8.0"

project:
  name: my-app
  description: My SaaS application

components:
  backend:
    enabled: true
    framework: fastapi
  frontend:
    enabled: true
    framework: react
  docker:
    enabled: true
    include_prod: true
  deployment:
    enabled: true
    provider: hetzner
  mcp:
    enabled: true
  ci:
    enabled: true
    provider: github-actions
  docs:
    enabled: false  # User opted out

regeneration:
  auto: true
  on_spec_change: true
  run_migrations: true
  watch_patterns:
    - "prism.yaml"
    - "spec/**/*.yaml"

notifications:
  new_version: true
  breaking_changes: true
```

### File Watcher Integration

```python
# prism/cli.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SpecChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.yaml', '.yml')):
            console.print("[Auto-regen] Detected changes...")
            regenerate_project()
            run_migrations_if_needed()
            trigger_hot_reload()

def dev_command():
    # Start services
    start_backend()
    start_frontend()

    # Watch for spec changes
    observer = Observer()
    observer.schedule(SpecChangeHandler(), '.', recursive=True)
    observer.start()

    # Version check
    if new_version_available():
        console.print(f"💡 Prism {latest} available! Run: prism self-upgrade")
```

## Success Metrics

1. **Onboarding tid**: Fra 15+ minutter → under 5 minutter
2. **Kommando-brug**: 90% af workflows bruger kun `init` + `dev`
3. **Regenererings-fejl**: Ingen tab af custom kode
4. **Version adoption**: 80% af brugere på seneste version

## Risici

| Risiko | Sandsynlighed | Impact | Mitigation |
|--------|---------------|--------|------------|
| Protected regions parser fejl | Medium | Høj | Omfattende tests, backup før merge |
| Breaking changes i config format | Lav | Medium | Versioneret config schema, migration scripts |
| File watcher performance | Lav | Lav | Debounce, ignore patterns |

## Dependencies

- **watchdog**: File system monitoring
- **questionary** eller **rich**: Interaktiv wizard
- **packaging**: Version comparison

## Relaterede Issues

- [Custom routes not preserved](custom-routes-not-preserved.md) - ✅ Løst med protected regions
- [App.tsx overwrites providers](app-tsx-overwrites-providers.md) - ✅ Løst med protected regions

---

**Næste skridt**: Start med Fase 1 - udvid protected regions til alle genererede filer.
