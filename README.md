# meritum-core

Kod wspólny dla [meritum-backend](https://github.com/Meritum-HackNation2026/meritum-backend) i [meritum-worker](https://github.com/Meritum-HackNation2026/meritum-worker): kontrakty zadań, porty i adaptery. Nie zawiera aplikacji, tylko bibliotekę `meritum_core`.

| Moduł | Zawartość |
| --- | --- |
| `meritum_core.jobs.contracts` | nazwa aplikacji DBOS, kolejki, workflowy (`WorkflowSpec`) i ich modele wejścia/wyjścia (Pydantic) |
| `meritum_core.jobs.ports` | port `JobQueue`, przez który backend zleca zadania |
| `meritum_core.jobs.adapters` | `DbosJobQueue`: implementacja portu na `DBOSClient` |

Zasady kontraktu:

- Backend zleca zadania tylko przez `JobQueue`, worker wykonuje je jako workflowy DBOS o nazwie i kolejce z `WorkflowSpec`.
- Argument i wynik workflowu to jeden obiekt JSON (`model_dump(mode="json")`), serializowany jako `PORTABLE`, więc worker nie potrzebuje klas backendu, a backend klas workera.
- Każde wejście i wyjście ma `contract_version`. Zmiana niezgodna wstecz podnosi `CONTRACT_VERSION`.
- Worker przyjmuje tylko zadania ze swoim `application_version`, czyli nazwą środowiska (`dev`, `prd`, lokalnie `local`). Backend zleca z tą samą wartością.

## Użycie w innym repo

Repozytorium jest prywatne, więc zależność idzie przez SSH:

```toml
[project]
dependencies = ["meritum-core"]

[tool.uv.sources]
meritum-core = { git = "ssh://git@github.com/Meritum-HackNation2026/meritum-core.git", branch = "main" }
```

`uv.lock` przypina konkretny commit. Po zmianie w core: `uv lock --upgrade-package meritum-core` w backendzie i workerze. CI i deploy pobierają core kluczem wdrożeniowym tylko do odczytu (sekret repozytorium `MERITUM_CORE_SSH_KEY` w backendzie i workerze; na planie Free sekrety organizacji nie trafiają do repo prywatnych).

## Praca lokalna

```bash
uv sync
uv run ruff check . && uv run ruff format --check . && uv run ty check
uv run pytest
```

Gałęzie: `develop` (integracja), `main` (produkcja). Zmiany przez PR do `develop`, potem PR `develop` → `main`. Nie pushuj bezpośrednio do `develop` ani `main`: na planie Free GitHub nie egzekwuje tego w repozytoriach prywatnych, więc to zasada zespołu.
