# meritum-core

Kod wspólny dla [meritum-backend](https://github.com/Meritum-HackNation2026/meritum-backend) i [meritum-worker](https://github.com/Meritum-HackNation2026/meritum-worker) oraz jedyne źródło prawdy kontraktów danych Meritum. Nie zawiera aplikacji, tylko bibliotekę `meritum_core` i wygenerowane z niej pliki dla TypeScriptu.

| Moduł | Zawartość |
| --- | --- |
| `meritum_core.checks.contracts` | kontrakty sprawdzania (MSZ „Prawdowid”): `CheckRequest`, `CheckResult` z werdyktami, cytatami i przesłankami, `CachedResult` (merytoryczna część wyniku w pamięci wyników), `AnalysisStatus`, `CheckRecord`, `ModeratorCase`, `CatalogEntry`; reguły z treści zadania pilnuje walidacja, `CONTRACT_VERSION` osobno od kontraktu zadań |
| `meritum_core.jobs.contracts` | nazwa aplikacji DBOS, kolejki, workflowy (`WorkflowSpec`) i ich modele wejścia/wyjścia (Pydantic) |
| `meritum_core.jobs.ports` | port `JobQueue`, przez który backend zleca zadania |
| `meritum_core.jobs.adapters` | `DbosJobQueue`: implementacja portu na `DBOSClient` |

## Kontrakty dla TypeScriptu i design systemu

`contracts/` trzyma pliki wygenerowane z `meritum_core.checks.contracts`. Generuje się je tylko tutaj:

```bash
scripts/generate-contracts.sh           # contracts/meritum.schema.json i contracts/meritum.ts
scripts/generate-contracts.sh --check   # to samo sprawdza CI (job contracts)
```

Wersje są przypięte: pydantic przez `uv.lock`, generator TS (`json-schema-to-typescript@15.0.4`) w skrypcie. `contracts/examples.json` to przykłady, które testy (`tests/test_checks_contracts.py`) walidują razem z regułami: werdykt rozstrzygający bez cytatu, siła niezgodna z przesłankami albo policzona z wydawców, których cytaty nie zgadzają się z werdyktem, sprzeczne źródła z poziomem siły, awaria w pamięci wyników i inne.

Design system (`design-system/contracts/`) i aplikacje w TypeScripcie trzymają kopię tych plików i nigdy jej nie edytują. Kopię odświeża `contracts/sync.sh` w design-systemie po zmianie tutaj; zapisuje commit core i sumy kontrolne, a CI design-systemu sprawdza, że kopii nikt nie zmienił ręcznie. Przy rozbieżności wygrywa zawsze meritum-core.

## Kontrakt zadań

Zasady kontraktu:

- Backend zleca zadania tylko przez `JobQueue`, worker wykonuje je jako workflowy DBOS o nazwie i kolejce z `WorkflowSpec`.
- Argument i wynik workflowu to jeden obiekt JSON (`model_dump(mode="json")`), serializowany jako `PORTABLE`, więc worker nie potrzebuje klas backendu, a backend klas workera.
- Każde wejście i wyjście ma `contract_version`. Zmiana niezgodna wstecz podnosi `CONTRACT_VERSION`.
- Worker przyjmuje tylko zadania ze swoim `application_version`, czyli nazwą środowiska (`dev`, `prd`, lokalnie `local`). Backend zleca z tą samą wartością.

## Użycie w innym repo

Do końca prac repozytorium jest prywatne (potem wszystkie repozytoria Meritum będą publiczne), więc zależność idzie przez SSH:

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
uv run python scripts/check_conventions.py && uv run vulture && uv run bandit -c pyproject.toml -r src scripts
uv run pytest            # z testami architektury (tests/architecture/)
```

Zasady architektury i to, co je sprawdza: [docs/architecture.md](docs/architecture.md).

Gałęzie: `develop` (integracja), `main` (produkcja). Zmiany przez PR do `develop`, potem PR `develop` → `main`. Nie pushuj bezpośrednio do `develop` ani `main`: na planie Free GitHub nie egzekwuje tego w repozytoriach prywatnych, więc to zasada zespołu.
