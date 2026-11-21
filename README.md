# meritum-core

Kod wspólny dla [meritum-backend](https://github.com/Meritum-HackNation2026/meritum-backend) i [meritum-worker](https://github.com/Meritum-HackNation2026/meritum-worker) oraz jedyne źródło prawdy kontraktów danych Meritum. Nie zawiera aplikacji, tylko bibliotekę `meritum_core` i wygenerowane z niej pliki dla TypeScriptu.

| Moduł | Zawartość |
| --- | --- |
| `meritum_core.checks.contracts` | kontrakty sprawdzania (MSZ „Prawdowid”): `CheckRequest`, `CheckResult` z werdyktami, cytatami i przesłankami, `CachedResult` (merytoryczna część wyniku w pamięci wyników), `AnalysisStatus`, `CheckRecord`, `ModeratorCase`, `CatalogEntry`; reguły z treści zadania pilnuje walidacja, `CONTRACT_VERSION` osobno od kontraktu zadań |
| `meritum_core.jobs.contracts` | nazwa aplikacji DBOS, kolejki, workflowy (`WorkflowSpec`: `ping`, `check`, `escalate_claim`, `delete_subject`, `readiness`) i ich modele wejścia/wyjścia (Pydantic) |
| `meritum_core.jobs.ports` | port `JobQueue`, przez który backend zleca zadania i czyta ich strumienie (`stream`) i zdarzenia (`event`) |
| `meritum_core.jobs.adapters` | `DbosJobQueue`: implementacja portu na `DBOSClient` |
| `meritum_core.jobs.fakes` | `InMemoryJobQueue`: port w pamięci do testów backendu i workera (nagrywa zlecone zadania, odtwarza strumienie i zdarzenia) |
| `meritum_core.shared.blobs` | port `BlobStore` na pliki audio i obrazy wspólne dla backendu i workera (ADR-31), `BlobRef`, `BlobNotFoundError`, fake w pamięci, adaptery systemu plików i prywatnego bucketu GCS oraz fabryka `build_blob_store` według `MERITUM_BLOB_PROVIDER` (zob. [Magazyn plików](#magazyn-plików)); test kontraktowy w `tests/shared/blobs/`, który przechodzi każdy adapter |
| `meritum_core.shared.llm` | port `LlmPort` (strukturalna odpowiedź jako model Pydantic plus zużycie tokenów, instrukcje osobno od danych), adaptery Vertex AI i stub, fabryka `build_llm(LlmSettings())`, błąd `ProviderUnavailableError` |
| `meritum_core.corpus` | port `CorpusSearchPort` (wyszukiwanie hybrydowe w przypiętej migawce `corpus_version`), `Passage`, reguła `fuse_rankings` (RRF ważone świeżością), adaptery PostgreSQL i w pamięci, fabryka `build_corpus_search`, migracje schematu `corpus` |
| `meritum_core.shared.embeddings` | port `EmbeddingsPort`, adaptery Vertex AI i stub, fabryka `build_embeddings(EmbeddingsSettings())` |
| `meritum_core.security.injection` | detektor prompt injection przed każdym wywołaniem modelu: wzorce PL/EN odporne na wielkość liter, znaki niewidoczne i podobne litery, bramka klasyfikatora za portem `InjectionGatePort` (`NullInjectionGate` loguje pominięcie, `FakeInjectionGate` w `fakes`), izolowany klasyfikator przez `LlmPort`; `build_injection_detector(llm=..., gate=...)` przyjmuje gotową bramkę, a `instruction_removed` wycina polecenie z treści użytkownika i zwraca `InjectionEvent` |
| `meritum_core.checks` (repozytorium), `moderation`, `notifications` | porty repozytoriów: `CheckRecordRepository` (zapis, odczyt, lista po sesji albo koncie, usunięcie osoby, wybór do retencji), `ModeratorCaseRepository` (zapis i aktualizacja, otwarta sprawa po twierdzeniu, lista dla panelu, usunięcie skasowanych sprawdzeń ze spraw), `HighRiskTopicRepository` (tematy wysokiego ryzyka ze słowami kluczowymi), `NotificationRepository` (zapis, lista dla sesji albo konta, oznaczenie jako przeczytane, usunięcie po adresacie i po `retention_until`); fake'i w pamięci w modułach `fakes` każdej domeny (`InMemory…`) i testy kontraktowe w `tests/checks/records/`, `tests/moderation/`, `tests/notifications/`, które przejdą też adaptery PostgreSQL (core#38) |
| `meritum_core.checks.transcription` | port `TranscriptionPort` (`audio_id` z `BlobStore` → `Transcript` w pl-PL), adapter Speech-to-Text v2 (Chirp 3, `eu`) i stub, fabryka `build_transcriber`, `inspect_audio` (format i długość z bajtów pliku), limity w `constants.py`, błędy `UnsupportedAudioError` i `TranscriptionUnavailableError` |
| `meritum_core.evidence`, `security`, `observability`, `shared` | szkielet domen (ADR-01): na razie puste publiczne API (`__all__ = []`); kod dochodzi w kolejnych zgłoszeniach |
| `meritum_core.evidence`, `security`, `moderation`, `observability`, `notifications`, `shared` | szkielet domen (ADR-01): na razie puste publiczne API (`__all__ = []`); kod dochodzi w kolejnych zgłoszeniach |
| `meritum_core.corpus.fetching` | `PageFetcherPort` i `build_page_fetcher()`: jedyna droga pobrania adresu URL. Tylko http(s), adresy wewnętrzne blokowane także po przekierowaniu i przy DNS rebinding, limity w `constants.py`, tekst główny przez trafilatura, osobne błędy dla logowania, paywalla i stron wymagających JavaScriptu; źródła respektują robots.txt i Content-Signal |
| `meritum_core.evidence`, `corpus`, `security`, `moderation`, `observability`, `notifications`, `shared` | szkielet domen (ADR-01): na razie puste publiczne API (`__all__ = []`); kod dochodzi w kolejnych zgłoszeniach |

## Magazyn plików

Backend i worker budują `BlobStore` przez `build_blob_store(BlobSettings())`, a ustawienia czytają ze zmiennych środowiska:

| Zmienna | Kiedy | Znaczenie |
| --- | --- | --- |
| `MERITUM_BLOB_PROVIDER` | zawsze | `memory` (testy), `filesystem` (lokalnie i serwer zespołu), `gcs` (chmura) |
| `MERITUM_BLOB_DIRECTORY` | `filesystem` | katalog na wolumenie wspólnym dla backendu i workera; tworzony, jeśli go nie ma |
| `MERITUM_BLOB_BUCKET` | `gcs` | nazwa prywatnego bucketu Cloud Storage |

Bucket leży w regionie `europe-central2`, nie ma publicznego dostępu, a reguła cyklu życia usuwa obiekty po 30 dniach (zakłada go meritum-infra). Adapter GCS loguje się przez Application Default Credentials i nie wydaje publicznych ani podpisanych adresów, tylko bajty albo adres `gs://` dla Speech-to-Text w trybie batch. Adapter systemu plików nazywa pliki wyłącznie identyfikatorem bloba i nie wychodzi poza katalog.

Test kontraktowy uruchamia adapter GCS na emulatorze w procesie (`gcp-storage-emulator` na localhost), bez sieci. Zapis do prawdziwego bucketu sprawdza się tylko lokalnie: `MERITUM_BLOB_BUCKET=<bucket> uv run pytest -m integration`.

## Kontrakty dla TypeScriptu i design systemu

`contracts/` trzyma pliki wygenerowane z `meritum_core.checks.contracts`. Generuje się je tylko tutaj:

```bash
scripts/generate-contracts.sh           # contracts/meritum.schema.json i contracts/meritum.ts
scripts/generate-contracts.sh --check   # to samo sprawdza CI (job contracts)
```

Wersje są przypięte: pydantic przez `uv.lock`, generator TS (`json-schema-to-typescript@15.0.4`) w skrypcie. `contracts/examples.json` to przykłady, które testy (`tests/checks/contracts/`) walidują razem z regułami: werdykt rozstrzygający bez cytatu, siła niezgodna z przesłankami albo policzona z wydawców, których cytaty nie zgadzają się z werdyktem, sprzeczne źródła z poziomem siły, awaria w pamięci wyników i inne.

Design system (`design-system/contracts/`) i aplikacje w TypeScripcie trzymają kopię tych plików i nigdy jej nie edytują. Kopię odświeża `contracts/sync.sh` w design-systemie po zmianie tutaj; zapisuje commit core i sumy kontrolne, a CI design-systemu sprawdza, że kopii nikt nie zmienił ręcznie. Przy rozbieżności wygrywa zawsze meritum-core.

## Kontrakt zadań

Zasady kontraktu:

- Backend zleca zadania tylko przez `JobQueue`, worker wykonuje je jako workflowy DBOS o nazwie i kolejce z `WorkflowSpec`.
- Workflow publikuje postęp jako obiekty JSON: strumień `PROGRESS_KEY` (kolejne `AnalysisStatus`, ostatni z `result`) i zdarzenie `READINESS_KEY` (`ReadinessReport`); klucze są w `meritum_core.jobs.constants`.
- Wejście nie niesie surowych danych: tekst jest zamaskowany przed zleceniem, a identyfikator użytkownika kanału trafia tylko jako solony skrót (`channel_user_hash`).
- Argument i wynik workflowu to jeden obiekt JSON (`model_dump(mode="json")`), serializowany jako `PORTABLE`, więc worker nie potrzebuje klas backendu, a backend klas workera.
- Każde wejście i wyjście ma `contract_version`. Zmiana niezgodna wstecz podnosi `CONTRACT_VERSION`.
- Worker przyjmuje tylko zadania ze swoim `application_version`, czyli nazwą środowiska (`dev`, `prd`, lokalnie `local`). Backend zleca z tą samą wartością.

## Model językowy (`meritum_core.shared.llm`)

Każdy krok workflowu woła model tylko przez `LlmPort`. Adapter wybiera konfiguracja, więc model albo dostawcę zmienia się bez przebudowy (US-WDR-02, ADR-11). Nazwa modelu, jego wersja i region są tylko w zmiennych środowiskowych, nigdy w kodzie.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_LLM_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `vertex` |
| `MERITUM_LLM_MODEL` | brak | przypięta wersja modelu w Vertex AI, np. `gemini-2.0-flash-001`; wymagana dla `vertex` |
| `MERITUM_LLM_REGION` | brak | lokalizacja Vertex AI w UE (lista w `EU_REGIONS`, np. `europe-west4`, `europe-central2`, `eu`), w której model jest dostępny (ADR-14); Londyn i Zurych są odrzucane; wymagany dla `vertex` |
| `MERITUM_LLM_PROJECT` | projekt z ADC | projekt Google Cloud |
| `MERITUM_LLM_RETRIES` | `3` | liczba prób HTTP przy błędach przejściowych (z pierwszą). Niepoprawną odpowiedź model dostaje do poprawy raz. Gdy próby się skończą albo dane logowania są odrzucone, adapter rzuca `ProviderUnavailableError`, który workflow mapuje na `technical_failure` |
| `MERITUM_LLM_STUB_FIXTURES` | brak | plik JSON dla stubu: nazwa klasy modelu wyjścia → odpowiedź, np. `{"ClaimList": {"claims": [...]}}` |

Vertex AI uwierzytelnia się przez Application Default Credentials (`gcloud auth application-default login` lokalnie, konto serwisowe w chmurze). Temperatura jest zawsze 0 (ADR-19). Przypięcie wersji to odpowiedzialność konfiguracji: podaj nazwę z wersją, nie alias. Adapter woła `generateContent`, więc obsługuje modele Gemini. Model partnerski z Model Garden (np. Mistral Small 3.1 z ADR-11) potrzebuje osobnego adaptera za tym samym portem. Brak odpowiedzi stubu dla danego typu też kończy się `ProviderUnavailableError` z nazwą typu, więc przy stubie ustaw `MERITUM_LLM_STUB_FIXTURES`. Testy w CI używają stubu i odpowiedzi w formacie Vertex AI podanej przez atrapę HTTP (`build_llm(..., http_client=...)`); prawdziwe wywołanie odpala tylko `uv run pytest -m integration` z ustawionym `MERITUM_LLM_PROVIDER=vertex`.

## Wyszukiwanie w korpusie (`meritum_core.corpus`)

Agenty badawcze w workerze i narzędzie MCP `search_sources` w backendzie wołają `CorpusSearchPort.search(query, claim_date=..., corpus_version=...)` w swoim procesie (ADR-32). Adapter PostgreSQL układa trzy rankingi w przypiętej migawce: podobieństwo wektorów (pgvector, HNSW), pełny tekst w konfiguracji `public.polish` (słownik hunspell-pl, dowolne słowo zapytania może pasować) i podobieństwo trigramów (`pg_trgm`, literówki). `fuse_rankings` łączy je przez reciprocal rank fusion i mnoży wynik przez wagę świeżości liczoną od daty twierdzenia, a nie od dzisiaj (US-ZRD-05). Wagi i progi są w `corpus/constants.py`. Migawka widzi fragmenty dodane do jej `taken_at` i niewycofane przed nim (`retired_at`); fragmentów się nie nadpisuje, zmieniony albo usunięty dokument dostaje `retired_at`. Workflow migawek zapisuje `taken_at` dopiero po zatwierdzeniu objętych nią transakcji pobierania. Nieznana wersja kończy się `UnknownCorpusVersionError`, a nie pustą listą (ADR-19).

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_CORPUS_PROVIDER` | `memory` | `memory` (migawki w procesie: testy, behave, praca bez bazy) albo `postgres` |
| `MERITUM_CORPUS_DATABASE_URL` | brak | adres libpq bazy ze schematem `corpus`; wymagany dla `postgres` |
| `MERITUM_EMBEDDINGS_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `vertex` |
| `MERITUM_EMBEDDINGS_MODEL` | `gemini-embedding-001` | model embeddingów w Vertex AI (ADR-04); adaptery biorą go tylko z ustawień |
| `MERITUM_EMBEDDINGS_REGION` | brak | lokalizacja Vertex AI w UE (`EU_REGIONS`, np. `europe-west4`); dostępność modelu w `europe-central2` do sprawdzenia; wymagany dla `vertex` |
| `MERITUM_EMBEDDINGS_PROJECT` | projekt z ADC | projekt Google Cloud |
| `MERITUM_EMBEDDINGS_DIMENSIONS` | `768` | rozmiar wektora; tabele korpusu mają `vector(768)`, więc zmiana wymaga migracji i ponownego zwektoryzowania |

Dostawca embeddingów to Vertex AI (Google Cloud) w regionie UE, uwierzytelniony przez Application Default Credentials. Zapytania idą z typem `RETRIEVAL_QUERY`, fragmenty z `RETRIEVAL_DOCUMENT`. Korpus i zapytania muszą używać tego samego modelu i rozmiaru wektora.

Migracje leżą w `src/meritum_core/corpus/migrations/` (SQL, w kolejności numerów) i trafiają do pakietu. Są tylko wstecznie zgodne (dodajemy, nie usuwamy i nie zmieniamy nazw), bo schemat `corpus` czytają dev i prd; uruchamia je deploy z `main` (infra/004). Wymagają obrazu `meritum-postgres` z meritum-infra (pgvector, `pg_trgm`, `public.polish`).

Test adaptera na prawdziwej bazie uruchamia się lokalnie:

```bash
docker run -d --rm --name corpus -e POSTGRES_PASSWORD=test -e POSTGRES_DB=meritum -p 55432:5432 <obraz meritum-postgres>
MERITUM_CORPUS_DATABASE_URL=postgresql://postgres:test@localhost:55432/meritum uv run pytest -m integration tests/corpus
```

## Transkrypcja nagrań (`meritum_core.checks.transcription`)

Nagranie z formularza albo wiadomość głosowa z Discorda leży w `BlobStore` (ADR-31). Workflow woła `TranscriptionPort.transcribe(audio_id)` i dostaje `Transcript` (tekst i język), który sprawdza jak zwykły tekst (US-SPR-11, F-08).

| Co | Wartość |
| --- | --- |
| Dostawca | Google Speech-to-Text v2 przez REST, model `chirp_3`, multi-region `eu` (endpoint `eu-speech.googleapis.com`), język `pl-PL` (ADR-30). Dane nie opuszczają UE (ADR-14) |
| Tryby | do `SYNC_MAX_SECONDS` (55 s) i 10 MiB treści w base64: synchroniczne `recognize` z treścią w żądaniu; dłuższe: `batchRecognize` z adresu `gs://` z `BlobStore.uri()` (inny adres to `TranscriptionUnavailableError`). Batch nie mieści się w celu 30 s, więc dłuższe nagranie kończy się powiadomieniem |
| Formaty | OGG z Opus, MP3, M4A, WAV; format i długość odczytuje `inspect_audio` z bajtów (granula ostatniej strony Ogg, chunki WAV, `mvhd` w M4A, ramka Xing/Info albo bitrate w MP3), nie z typu MIME od użytkownika; plik bez czytelnej długości jest odrzucany |
| Limity | `MAX_AUDIO_BYTES` 20 MiB, `MAX_AUDIO_SECONDS` 600 s |
| Koszt | cennik Standard to 0,016 USD za minutę; czy `chirp_3` jest tak rozliczany, nie potwierdziliśmy (załącznik B dokumentu produktowego) |
| Retencja | nagranie w magazynie usuwa retencja `BlobStore` (`expires_at`, ADR-13); adapter niczego nie zapisuje po stronie dostawcy (wynik batch wraca w odpowiedzi, `inlineResponseConfig`) |

Błędy: `UnsupportedAudioError` (inny format, przekroczony limit) workflow mapuje na `out_of_scope`, `TranscriptionUnavailableError` (dostawca padł po ponowieniach, odrzucone dane logowania, operacja batch nie skończyła się w `BATCH_TIMEOUT_SECONDS`) na `technical_failure`; oba błędy niosą status w `check_status`. Brak pliku to `BlobNotFoundError`.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_TRANSCRIPTION_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `speech_v2` |
| `MERITUM_TRANSCRIPTION_PROJECT` | brak | projekt Google Cloud z włączonym Speech-to-Text API; wymagany dla `speech_v2` |
| `MERITUM_TRANSCRIPTION_RETRIES` | `3` | liczba prób HTTP przy 429 i 5xx (z pierwszą) |
| `MERITUM_TRANSCRIPTION_STUB_FIXTURE` | brak | plik JSON z `Transcript` dla stubu, np. `{"text": "...", "language": "pl-PL"}`; bez niego stub rzuca `TranscriptionUnavailableError` |

Uwierzytelnienie przez Application Default Credentials. Testy w CI działają na odpowiedziach w formacie Speech-to-Text v2 podanych przez atrapę HTTP (`tests/checks/transcription/fixtures/`), bez sieci.

Ręczny test (lokalnie, nigdy w CI): czy v2 dekoduje wiadomość głosową z Discorda (OGG z Opus 48 kHz) bez konwersji.

```bash
gcloud auth application-default login
uv run python scripts/transcribe_audio.py wiadomosc-glosowa.ogg --project <projekt>
```

Wynik: jeszcze nie uruchomiony na prawdziwej wiadomości z Discorda (wymaga projektu GCP z włączonym API, zgłoszenie #62). Wpisz go tutaj i w załączniku B dokumentu produktowego. Skrypt sprawdza tylko tryb synchroniczny (do 55 s); trybu batch na prawdziwym dostawcy nie sprawdził.

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
