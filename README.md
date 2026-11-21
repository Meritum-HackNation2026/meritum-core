# meritum-core

Kod wspólny dla [meritum-backend](https://github.com/Meritum-HackNation2026/meritum-backend) i [meritum-worker](https://github.com/Meritum-HackNation2026/meritum-worker) oraz jedyne źródło prawdy kontraktów danych Meritum. Nie zawiera aplikacji, tylko bibliotekę `meritum_core` i wygenerowane z niej pliki dla TypeScriptu.

| Moduł | Zawartość |
| --- | --- |
| `meritum_core.checks.contracts` | kontrakty sprawdzania (MSZ „Prawdowid”): `CheckRequest`, `CheckResult` z werdyktami, cytatami i przesłankami, `CachedResult` (merytoryczna część wyniku w pamięci wyników), `AnalysisStatus`, `CheckRecord`, `ModeratorCase`, `CatalogEntry`; reguły z treści zadania pilnuje walidacja, `CONTRACT_VERSION` osobno od kontraktu zadań |
| `meritum_core.jobs.contracts` | nazwa aplikacji DBOS, kolejki, workflowy (`WorkflowSpec`) i ich modele wejścia/wyjścia (Pydantic) |
| `meritum_core.jobs.ports` | port `JobQueue`, przez który backend zleca zadania |
| `meritum_core.jobs.adapters` | `DbosJobQueue`: implementacja portu na `DBOSClient` |
| `meritum_core.shared.blobs` | port `BlobStore` na pliki audio i obrazy wspólne dla backendu i workera (ADR-31), `BlobRef`, `BlobNotFoundError`, fake w pamięci i fabryka `build_blob_store` według `MERITUM_BLOB_PROVIDER` (`memory`); test kontraktowy w `tests/shared/blobs/`, który przechodzi każdy adapter |
| `meritum_core.shared.llm` | port `LlmPort` (strukturalna odpowiedź jako model Pydantic plus zużycie tokenów, instrukcje osobno od danych), adaptery Vertex AI i stub, fabryka `build_llm(LlmSettings())`, błąd `ProviderUnavailableError` |
| `meritum_core.evidence`, `corpus`, `security`, `moderation`, `observability`, `notifications`, `shared` | szkielet domen (ADR-01): na razie puste publiczne API (`__all__ = []`); kod dochodzi w kolejnych zgłoszeniach |

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

## Model językowy (`meritum_core.shared.llm`)

Każdy krok workflowu woła model tylko przez `LlmPort`. Adapter wybiera konfiguracja, więc model albo dostawcę zmienia się bez przebudowy (US-WDR-02, ADR-11). Nazwa modelu, jego wersja i region są tylko w zmiennych środowiskowych, nigdy w kodzie.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_LLM_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `vertex` |
| `MERITUM_LLM_MODEL` | brak | przypięta wersja modelu w Vertex AI, np. `gemini-2.5-flash-001`; wymagana dla `vertex` |
| `MERITUM_LLM_REGION` | brak | lokalizacja Vertex AI w UE (lista w `EU_REGIONS`, np. `europe-west4`, `europe-central2`, `eu`), w której model jest dostępny (ADR-14); Londyn i Zurych są odrzucane; wymagany dla `vertex` |
| `MERITUM_LLM_PROJECT` | projekt z ADC | projekt Google Cloud |
| `MERITUM_LLM_RETRIES` | `3` | liczba prób HTTP przy błędach przejściowych (z pierwszą). Niepoprawną odpowiedź model dostaje do poprawy raz. Gdy próby się skończą albo dane logowania są odrzucone, adapter rzuca `ProviderUnavailableError`, który workflow mapuje na `technical_failure` |
| `MERITUM_LLM_STUB_FIXTURES` | brak | plik JSON dla stubu: nazwa klasy modelu wyjścia → odpowiedź, np. `{"ClaimList": {"claims": [...]}}` |

Vertex AI uwierzytelnia się przez Application Default Credentials (`gcloud auth application-default login` lokalnie, konto serwisowe w chmurze). Temperatura jest zawsze 0 (ADR-19). Przypięcie wersji to odpowiedzialność konfiguracji: podaj nazwę z wersją, nie alias. Testy w CI używają stubu i odpowiedzi w formacie Vertex AI podanej przez atrapę HTTP (`build_llm(..., http_client=...)`); prawdziwe wywołanie odpala tylko `uv run pytest -m integration` z ustawionym `MERITUM_LLM_PROVIDER=vertex`.

## Użycie w innym repo

Do końca prac repozytorium jest prywatne (potem wszystkie repozytoria Meritum będą publiczne), więc zależność idzie przez SSH:

```toml
[project]
dependencies = ["meritum-core"]

[tool.uv.sources]
meritum-core = { git = "ssh://git@github.com/Meritum-HackNation2026/meritum-core.git", rev = "<sha commita z main>" }
```

Backend i worker przypinają konkretny commit z gałęzi main w core (`rev`). Po pushu do main, który zmienia `src/`, `contracts/` albo `pyproject.toml`, workflow `bump-dependents.yml` otwiera albo aktualizuje PR-y z podbiciem do develop w backendzie i workerze (gałąź `chore/bump-core`) oraz PR z kopią kontraktów w design-systemie, gdy kontrakty się zmieniły. Potrzebuje sekretu repozytorium `MERITUM_BOT_TOKEN`: tokenu fine-grained z uprawnieniami Contents i Pull requests (odczyt i zapis) w meritum-backend, meritum-worker i meritum-design-system oraz Contents (odczyt) w meritum-core. Bez sekretu workflow tylko ostrzega. Core ma tylko gałąź main, więc przypięty commit jest na main, zanim backend albo worker wyda develop do main. CI i deploy pobierają core kluczem wdrożeniowym tylko do odczytu (sekret repozytorium `MERITUM_CORE_SSH_KEY` w backendzie i workerze; na planie Free sekrety organizacji nie trafiają do repo prywatnych).

## Praca lokalna

```bash
uv sync
uv run ruff check . && uv run ruff format --check . && uv run ty check
uv run python scripts/check_conventions.py && uv run vulture && uv run bandit -c pyproject.toml -r src scripts
uv run pytest            # z testami architektury (tests/architecture/), bez testów integracyjnych
uv run behave            # scenariusze z features/
uv run pytest -m integration   # tylko lokalnie: testy na prawdziwym PostgreSQL albo u dostawcy
```

Scenariusze behave leżą w `features/<domena>.feature` (Gherkin skopiowany ze zgłoszenia, kroki po polsku), kroki w `features/steps/` wołają publiczne API `meritum_core` i działają w procesie, bez bazy i sieci. CI uruchamia je w jobie `tests`.

Test, który potrzebuje prawdziwego PostgreSQL albo dostawcy, dostaje `@pytest.mark.integration`. `uv run pytest` go pomija (`-m "not integration"` w `addopts`), CI też. Uruchamia się go lokalnie przez `uv run pytest -m integration`.

Zasady architektury i to, co je sprawdza: [docs/architecture.md](docs/architecture.md).

Gałąź: tylko `main`. Zmiany przez PR do `main`. Nie pushuj bezpośrednio do `main`: na planie Free GitHub nie egzekwuje tego w repozytoriach prywatnych, więc to zasada zespołu.
