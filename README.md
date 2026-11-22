# meritum-core

Kod wspólny dla [meritum-backend](https://github.com/Meritum-HackNation2026/meritum-backend) i [meritum-worker](https://github.com/Meritum-HackNation2026/meritum-worker) oraz jedyne źródło prawdy kontraktów danych Meritum. Nie zawiera aplikacji, tylko bibliotekę `meritum_core` i wygenerowane z niej pliki dla TypeScriptu.

| Moduł | Zawartość |
| --- | --- |
| `meritum_core.checks.contracts` | kontrakty sprawdzania (MSZ „Prawdowid”): `CheckRequest`, `CheckResult` z werdyktami, cytatami i przesłankami oraz znacznikiem `AiMarker` (który system AI napisał uzasadnienie, z `ai_marker_for`, US-BEZ-07), `CachedResult` (merytoryczna część wyniku w pamięci wyników), `AnalysisStatus` (od v13 opcjonalny `draft`: zamaskowany szkic odpowiedzi do strumieniowania, nie werdykt), `CheckRequest` (od v15 `image_id`, wykluczające się z `text`, `url` i `audio_id`), `Source` (od v14 opcjonalne `max_age_hours` z katalogu; `max_age_for` daje ten sam próg regule rozbieżności i sile, domyślnie 365 dni), `CheckRecord`, `ModeratorCase`, `CatalogEntry` (od v18 `kind_by_path`: rodzaj źródła po ścieżce URL, np. `/transcripts/` → `transcript`; `kind_for` wybiera rodzaj dokumentu), `Notification` (od v9 kod kroku `step_code` przy `check_progress` i kod komunikatu `message_code` przy `system`; tekst składa aplikacja z copy/pl.json, ADR-29); reguły z treści zadania pilnuje walidacja, `CONTRACT_VERSION` osobno od kontraktu zadań |
| `meritum_core.jobs.contracts` | nazwa aplikacji DBOS, kolejki, workflowy (`WorkflowSpec`: `ping`, `check`, `escalate_claim`, `delete_subject`, `readiness`) i ich modele wejścia/wyjścia (Pydantic); od wersji 5 `EvalRunInput` niesie opcjonalne `dataset_blob_id` (wgrany zestaw przypadków w `BlobStore`, rodzaj `dataset`), a migracja `0005_eval_storage.sql` tworzy tabele `eval_runs` i `eval_datasets` |
| `meritum_core.jobs.ports` | port `JobQueue`, przez który backend zleca zadania i czyta ich strumienie (`stream`) i zdarzenia (`event`) |
| `meritum_core.jobs.adapters` | `DbosJobQueue`: implementacja portu na `DBOSClient` |
| `meritum_core.jobs.fakes` | `InMemoryJobQueue`: port w pamięci do testów backendu i workera (nagrywa zlecone zadania, odtwarza strumienie i zdarzenia) |
| `meritum_core.shared.blobs` | port `BlobStore` na pliki audio i obrazy wspólne dla backendu i workera (ADR-31), `BlobRef`, `BlobNotFoundError`, fake w pamięci, adaptery systemu plików, prywatnego bucketu GCS i dowolnego magazynu zgodnego z S3 oraz fabryka `build_blob_store` według `MERITUM_BLOB_PROVIDER` (zob. [Magazyn plików](#magazyn-plików)); test kontraktowy w `tests/shared/blobs/`, który przechodzi każdy adapter |
| `meritum_core.shared.llm` | port `LlmPort` (strukturalna odpowiedź jako model Pydantic plus zużycie tokenów i koszt, instrukcje osobno od danych), adaptery OpenRouter, Vertex AI i stub, poziom rozumowania z konfiguracji, fabryka `build_llm(LlmSettings())`, błąd `ProviderUnavailableError` |
| `meritum_core.corpus` | port `CorpusSearchPort` (wyszukiwanie hybrydowe w przypiętej migawce `corpus_version`), `Passage`, reguła `fuse_rankings` (RRF ważone świeżością), adaptery PostgreSQL i w pamięci, fabryka `build_corpus_search`, migracje schematu `corpus` |
| `meritum_core.shared.embeddings` | port `EmbeddingsPort`, adaptery Vertex AI i stub, fabryka `build_embeddings(EmbeddingsSettings())` |
| `meritum_core.security.injection` | detektor prompt injection przed każdym wywołaniem modelu: wzorce PL/EN odporne na wielkość liter, znaki niewidoczne i podobne litery, bramka klasyfikatora za portem `InjectionGatePort` (`NullInjectionGate` loguje pominięcie, `FakeInjectionGate` w `fakes`), izolowany klasyfikator przez `LlmPort`; `build_injection_detector(llm=..., gate=...)` przyjmuje gotową bramkę, a `instruction_removed` wycina polecenie z treści użytkownika i zwraca `InjectionEvent` |
| `meritum_core.security.pii` | `mask_personal_data(text, gate)`: najpierw bramka maskowania za portem `PiiGatePort` (Google Sensitive Data Protection w regionie UE albo `NullPiiGate`, która loguje pominięcie), potem wzorce telefonu, e-maila, PESEL-u i numeru dowodu; fabryka `build_pii_gate(PiiGateSettings())` według `MERITUM_PII_GATE` (zob. [Maskowanie danych osobowych](#maskowanie-danych-osobowych-meritum_coresecuritypii)) |
| `meritum_core.checks` (repozytorium), `moderation`, `notifications` | porty repozytoriów: `CheckRecordRepository` (zapis, odczyt, lista po sesji albo koncie, usunięcie osoby, wybór do retencji), `ModeratorCaseRepository` (zapis i aktualizacja, otwarta sprawa po twierdzeniu, lista dla panelu, usunięcie skasowanych sprawdzeń ze spraw), `HighRiskTopicRepository` (tematy wysokiego ryzyka ze słowami kluczowymi), `NotificationRepository` (zapis, lista dla sesji albo konta, oznaczenie jako przeczytane, usunięcie po adresacie, po usuniętych sprawdzeniach i po `retention_until`); fake'i w pamięci w modułach `fakes` każdej domeny (`InMemory…`), adaptery PostgreSQL i testy kontraktowe w `tests/checks/records/`, `tests/moderation/`, `tests/notifications/`, które przechodzą oba (zob. [Baza aplikacji](#baza-aplikacji)) |
| `meritum_core.checks.ocr` | porty `OcrPort` (`image_id` z `BlobStore` → `OcrResult`: tekst, kandydat na `claim_date`, metadane pliku) i `ImageSearchPort` (wcześniejsze wystąpienia albo jawne „nie wyszukano”), adapter Cloud Vision (`eu-vision.googleapis.com`, `DOCUMENT_TEXT_DETECTION`) i stub, fabryki `build_ocr` i `build_image_search`, `inspect_image`, limity w `constants.py`, błędy `UnsupportedImageError` i `OcrUnavailableError` |
| `meritum_core.checks.transcription` | port `TranscriptionPort` (`audio_id` z `BlobStore` → `Transcript` w pl-PL), adapter Speech-to-Text v2 (Chirp 3, `eu`) i stub, fabryka `build_transcriber`, `inspect_audio` (format i długość z bajtów pliku), limity w `constants.py`, błędy `UnsupportedAudioError` i `TranscriptionUnavailableError` |
| `meritum_core.corpus.fetching` | `PageFetcherPort` i `build_page_fetcher()`: jedyna droga pobrania adresu URL. Tylko http(s), adresy wewnętrzne blokowane także po przekierowaniu i przy DNS rebinding, limity w `constants.py`, tekst główny przez trafilatura, osobne błędy dla logowania, paywalla i stron wymagających JavaScriptu (te opcjonalnie renderuje Crawl4AI, zob. [Strony wymagające JavaScriptu](#strony-wymagające-javascriptu-crawl4ai-core30)); źródła respektują robots.txt i Content-Signal; `FetchedPage.tdm_reserved` mówi, czy znaczniki meta strony zastrzegają eksplorację, a `content_signals()` czyta Content-Signal z robots.txt |
| `meritum_core.observability` | `build_app_repositories(DatabaseSettings())` buduje wszystkie repozytoria aplikacji naraz (`AppRepositories`) według `MERITUM_DATABASE_PROVIDER`; port `SubjectEraser` usuwa jedną osobę ze wszystkich tabel aplikacji (US-BEZ-05), fake w `observability.fakes` |
| `meritum_core.shared.database` | `DatabaseSettings` (`MERITUM_DATABASE_*`), migracje schematu aplikacji i polecenie `meritum-migrate-app` |
| `meritum_core.corpus.catalog` | jawny katalog źródeł `catalog.yaml` (zob. [Katalog źródeł](#katalog-źródeł-meritum_corecorpuscatalog)): `load_catalog()` waliduje każdy wpis jako `CatalogEntry`, `check_tdm()` zapisuje zastrzeżenie TDM właściciela przez fetcher stron, `catalog_json()` i `catalog_markdown()` dają eksport dla frontendu i tabelę audytu |
| `meritum_core.evidence`, `shared` | szkielet domen (ADR-01): na razie puste publiczne API (`__all__ = []`); kod dochodzi w kolejnych zgłoszeniach |

## Strony wymagające JavaScriptu (Crawl4AI, core#30)

Fetcher httpx nie uruchamia JavaScriptu. Strona, której HTML nie ma tekstu głównego, kończy się `JavaScriptRequiredError` (`javascript_required`): obywatel dostaje prośbę o wklejenie tekstu, a inne źródła pobierają się dalej. Po ustawieniu `MERITUM_FETCH_CRAWL4AI_URL` (np. `http://crawl4ai:11235`) i `MERITUM_FETCH_CRAWL4AI_TOKEN` fabryka `build_page_fetcher(settings=FetchingSettings())` dokłada adapter, który taką stronę renderuje w lokalnym Crawl4AI. Włączamy go w obrazie `worker-ingest` (ADR-32), bo przeglądarka bezgłowa jest ciężka; zwykły worker zostaje bez niej. Obraz to `unclecode/crawl4ai:0.9.2`, plik `deploy/crawl4ai/compose.yaml` (repo niczego nie wdraża).

Ochrona przed SSRF przy renderowaniu:

- Crawl4AI dostaje adres dopiero wtedy, gdy fetcher httpx przeszedł z nim wszystkie kontrole (schemat, publiczny adres na każdym przekierowaniu, robots.txt i Content-Signal dla źródeł) i nie znalazł tylko tekstu.
- Tuż przed renderowaniem host jest rozwiązywany i sprawdzany jeszcze raz.
- Gdy przeglądarka wyląduje na innym hoście albo na adresie wewnętrznym, wynik jest odrzucany jako `redirect_blocked`. Inny host odrzucamy zawsze, bo wymagałby osobnego robots.txt.
- Kod nie może przypiąć adresu przeglądarki ani zatrzymać jej podzasobów, więc ostatnią warstwą jest sieć kontenera: Crawl4AI nie publikuje portu, z workerem rozmawia przez sieć `internal`, a ruch wychodzący idzie przez most `br-crawl4ai`. Na hoście trzeba zablokować z niego adresy wewnętrzne, np.:

```bash
for net in 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 100.64.0.0/10 127.0.0.0/8; do
  iptables -I DOCKER-USER -i br-crawl4ai -d "$net" -j DROP
done
ip6tables -I DOCKER-USER -i br-crawl4ai -d fc00::/7 -j DROP
ip6tables -I DOCKER-USER -i br-crawl4ai -d fe80::/10 -j DROP
```

W Cloud Run odpowiednikiem jest osobna usługa z ruchem wychodzącym przez VPC i regułą zapory odmawiającą zakresów prywatnych i serwera metadanych. Testy (`tests/corpus/test_fetching_crawl4ai.py`) odtwarzają nagrane odpowiedzi Crawl4AI z `tests/corpus/fixtures/`, bez przeglądarki i sieci. Próbę z prawdziwym Crawl4AI robi się lokalnie, poza CI.

## Magazyn plików

Backend i worker budują `BlobStore` przez `build_blob_store(BlobSettings())`, a ustawienia czytają ze zmiennych środowiska:

| Zmienna | Kiedy | Znaczenie |
| --- | --- | --- |
| `MERITUM_BLOB_PROVIDER` | zawsze | `memory` (testy), `filesystem` (lokalnie i serwer zespołu), `gcs` (chmura GCP), `s3` (dowolny magazyn zgodny z S3: MinIO, Cloudflare R2, usługa dostawcy z UE) |
| `MERITUM_BLOB_DIRECTORY` | `filesystem` | katalog na wolumenie wspólnym dla backendu i workera; tworzony, jeśli go nie ma |
| `MERITUM_BLOB_BUCKET` | `gcs`, `s3` | nazwa prywatnego bucketu |
| `MERITUM_BLOB_ENDPOINT_URL` | `s3` | adres usługi, np. `http://minio:9000`; bez niego adapter łączy się z AWS S3 |
| `MERITUM_BLOB_REGION` | `s3` | region bucketu; dla Cloudflare R2 `auto` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `s3` | klucze dostępu, tylko ze zmiennych środowiska (standardowe zmienne boto3) |

Bucket leży w regionie `europe-central2`, nie ma publicznego dostępu, a reguła cyklu życia usuwa obiekty po 30 dniach (zakłada go meritum-infra). Adapter GCS loguje się przez Application Default Credentials i nie wydaje publicznych ani podpisanych adresów, tylko bajty albo adres `gs://` dla Speech-to-Text w trybie batch. Adapter systemu plików nazywa pliki wyłącznie identyfikatorem bloba i nie wychodzi poza katalog.

Samodzielne hostowanie bez GCP: ustaw `MERITUM_BLOB_PROVIDER=s3`, endpoint, bucket (prywatny, z regułą wygasania obiektów po 30 dniach) i klucze; adapter używa adresowania ścieżkowego, więc działa z MinIO bez dodatkowych ustawień. Adres z `uri()` ma postać `s3://bucket/id`; Speech-to-Text batch czyta tylko `gs://`, więc transkrypcja z tym adapterem idzie ścieżką bajtów.

Test kontraktowy uruchamia adapter GCS na emulatorze w procesie (`gcp-storage-emulator` na localhost), a adapter S3 na serwerze `moto` w procesie, bez sieci. Zapis do prawdziwego bucketu sprawdza się tylko lokalnie: `MERITUM_BLOB_BUCKET=<bucket> uv run pytest -m integration`.

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
- `CheckInput` odrzuca `request.session_id` różne od własnego `session_id`: sprawdzenie trafia tylko do sesji, z której przyszło.
- Argument i wynik workflowu to jeden obiekt JSON (`model_dump(mode="json")`), serializowany jako `PORTABLE`, więc worker nie potrzebuje klas backendu, a backend klas workera.
- Każde wejście i wyjście ma `contract_version`. Zmiana niezgodna wstecz podnosi `CONTRACT_VERSION`.
- Worker przyjmuje tylko zadania ze swoim `application_version`, czyli nazwą środowiska (`dev`, `prd`, lokalnie `local`). Backend zleca z tą samą wartością.

## Model językowy (`meritum_core.shared.llm`)

Każdy krok workflowu woła model tylko przez `LlmPort`. Adapter, model, region i poziom rozumowania wybiera konfiguracja, więc model albo dostawcę zmienia się bez przebudowy (US-WDR-02, ADR-11). Domyślne wartości są w `shared/llm/constants.py`: Claude Haiku 5.5 przez OpenRouter z wysokim poziomem rozumowania.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_LLM_PROVIDER` | `openrouter` | `openrouter`, `vertex` (Gemini na Vertex AI) albo `stub` (bez kluczy i sieci) |
| `MERITUM_LLM_MODEL` | `anthropic/claude-haiku-5.5` | identyfikator modelu u dostawcy (tabela niżej); dla `vertex` trzeba go podać |
| `MERITUM_LLM_REGION` | `global` | dla `vertex` lokalizacja Vertex AI w UE (lista w `EU_REGIONS`, np. `europe-west3`, `eu`; Londyn i Zurych są odrzucane, ADR-14); dla `openrouter` `global` albo `eu` (`eu.openrouter.ai`, tylko na planie Business) |
| `MERITUM_LLM_REASONING` | `high` | poziom rozumowania `low`, `medium` albo `high`; Pydantic AI tłumaczy go na `thinkingConfig.thinking_level` w Vertex AI i `reasoning.effort` w OpenRouter |
| `OPENROUTER_API_KEY` | brak | klucz OpenRouter, wymagany dla `openrouter`; sekret, nigdy w repo ani w logach |
| `MERITUM_LLM_OPENROUTER_ZDR` | `true` | tylko endpointy bez retencji danych (`provider.zdr`); `false` wyłącznie do ewaluacji na golden secie modelu bez takich endpointów, nigdy z danymi użytkowników. `provider.data_collection=deny` jest zawsze |
| `MERITUM_LLM_PROJECT` | projekt z ADC | projekt Google Cloud |
| `MERITUM_LLM_RETRIES` | `3` | liczba prób HTTP przy błędach przejściowych (z pierwszą). Niepoprawną odpowiedź model dostaje do poprawy raz. Gdy próby się skończą albo dane logowania są odrzucone, adapter rzuca `ProviderUnavailableError`, który workflow mapuje na `technical_failure` |
| `MERITUM_LLM_STUB_FIXTURES` | brak | plik JSON dla stubu: nazwa klasy modelu wyjścia → odpowiedź, np. `{"ClaimList": {"claims": [...]}}` |

Bez `OPENROUTER_API_KEY` domyślna konfiguracja kończy się błędem walidacji przy starcie; testy i środowiska bez kluczy ustawiają `MERITUM_LLM_PROVIDER=stub`.

### Modele

Ceny w USD za milion tokenów (wejście / wyjście), sprawdzone 21 listopada 2026. Czas to mediana 5 wywołań krótkiego promptu z ekstrakcją twierdzeń, mierzona lokalnie z Polski.

| Model | Konfiguracja | Gdzie przetwarzane | Cena | Czas |
| --- | --- | --- | --- | --- |
| Claude Haiku 5.5 (domyślny) | `openrouter`, `anthropic/claude-haiku-5.5`, `high` | tylko Amazon Bedrock (`provider.only`, bez fallbacku), endpoint ZDR | 0,10 / 0,50 | 0,9 s |
| Gemini 3.5 Flash | `vertex`, `gemini-3.5-flash`, region `europe-west3` | Vertex AI, Frankfurt | 1,65 / 9,90 (stawka „Non-global”; globalna 1,50 / 9,00; wyjście liczy też tokeny rozumowania) | 4,9 s (`low`), 7,4 s (`high`) |
| GPT-6.1 Terra | `openrouter`, `openai/gpt-6.1-terra`, `low` | endpoint ZDR wybrany przez OpenRouter (Azure) | 1,00 / 5,00 | 1,3 s |
| Step 3.7 Flash | `openrouter`, `stepfun/step-3.7-flash`, `medium`, `MERITUM_LLM_OPENROUTER_ZDR=false` | StepFun albo Novita (OpenRouter nie ma dla niego endpointu ZDR) | 0,20 / 1,15 | 3,0 s |

Źródła: [Claude Haiku 5.5 (Anthropic)](https://platform.claude.com/docs/en/about-claude/pricing), [Gemini 3.5 Flash na Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-5-flash) i [cennik Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/pricing), strony modeli OpenRouter ([Haiku 5.5](https://openrouter.ai/anthropic/claude-haiku-5.5), [GPT-6.1 Terra](https://openrouter.ai/openai/gpt-6.1-terra), [Step 3.7 Flash](https://openrouter.ai/stepfun/step-3.7-flash)) i lista [endpointów ZDR](https://openrouter.ai/api/v1/endpoints/zdr).

Koszt wywołania trafia do `LlmUsage.cost_usd`, a pola `LlmUsage` pasują do kontraktu `ModelUsage` w `CheckRecord`. OpenRouter podaje koszt w odpowiedzi; dla Vertex AI adapter liczy go z cennika `PRICES_USD_PER_MTOK` w `constants.py`. Model spoza cennika ma koszt 0 i adapter zapisuje ostrzeżenie w logu, więc nowy model dopisz do cennika. Region w `LlmUsage` dla OpenRouter to region routingu i dostawca, do którego OpenRouter skierował wywołanie, np. `global:Google`.

Uwagi do dostawców:

- GPT-6.1 Terra przez OpenRouter trafia na endpoint ZDR w Azure, a Step 3.7 Flash do StepFun albo Novita; OpenRouter nie podaje regionu tych dostawców.
- Haiku 5.5 ma na OpenRouter endpointy ZDR tylko w Google Vertex AI i Amazon Bedrock, a Vertex AI przechowuje oflagowane prompty do 90 dni. Adapter przypina go więc do Amazon Bedrock (`provider.only=["amazon-bedrock"]`, `allow_fallbacks=false`, lista w `OPENROUTER_PINNED_PROVIDERS`); gdy Bedrock nie odpowiada, wywołanie kończy się `ProviderUnavailableError` zamiast trafić gdzie indziej.
- Claude Haiku 5.5 nie jest włączony w Vertex AI naszego projektu (dostęp wymaga formularza Anthropic), więc idzie przez OpenRouter. OpenRouter działa z regionem `global`, bo routing EU wymaga planu Business; na razie służy przede wszystkim ewaluacji, dopóki zespół nie zdecyduje inaczej.
- Gemini 3.5 Flash odpowiada w `europe-west3` i w multiregionie `eu`. Temperatura jest 0 (ADR-19). Modele rozumujące przez OpenRouter odrzucają parametry próbkowania, więc temperatura nie jest do nich wysyłana.
- Vertex AI uwierzytelnia się przez Application Default Credentials (`gcloud auth application-default login` lokalnie, konto serwisowe w chmurze). Adapter `vertex` woła `generateContent`, więc obsługuje modele Gemini.
- Brak odpowiedzi stubu dla danego typu kończy się `ProviderUnavailableError` z nazwą typu, więc przy stubie ustaw `MERITUM_LLM_STUB_FIXTURES`.

Testy w CI używają stubu i odpowiedzi nagranych od każdego dostawcy (`tests/shared/llm/recordings/`, skrócone myśli i podpisy), podanych przez atrapę HTTP (`build_llm(..., http_client=...)`). Prawdziwe wywołanie odpala tylko `uv run pytest -m integration` z ustawionym `MERITUM_LLM_PROVIDER` i pozostałymi zmiennymi, np.:

```bash
MERITUM_LLM_PROVIDER=vertex MERITUM_LLM_MODEL=gemini-3.5-flash MERITUM_LLM_REGION=europe-west3 \
  uv run pytest -m integration tests/shared/llm
```

## Wyszukiwanie w korpusie (`meritum_core.corpus`)

Agenty badawcze w workerze i narzędzie MCP `search_sources` w backendzie wołają `CorpusSearchPort.search(query, claim_date=..., corpus_version=...)` w swoim procesie (ADR-32). Adapter PostgreSQL układa trzy rankingi w przypiętej migawce: podobieństwo wektorów (pgvector, HNSW), pełny tekst w konfiguracji `public.polish` (słownik hunspell-pl, dowolne słowo zapytania może pasować) i podobieństwo trigramów (`pg_trgm`, literówki). `fuse_rankings` łączy je przez reciprocal rank fusion i mnoży wynik przez wagę świeżości liczoną od daty twierdzenia, a nie od dzisiaj (US-ZRD-05). Wagi i progi są w `corpus/constants.py`. Migawka widzi fragmenty dodane do jej `taken_at` i niewycofane przed nim (`retired_at`); fragmentów się nie nadpisuje, zmieniony albo usunięty dokument dostaje `retired_at`. Workflow migawek zapisuje `taken_at` dopiero po zatwierdzeniu objętych nią transakcji pobierania. Nieznana wersja kończy się `UnknownCorpusVersionError`, a nie pustą listą (ADR-19).

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_CORPUS_PROVIDER` | `memory` | `memory` (migawki w procesie: testy, behave, praca bez bazy) albo `postgres` |
| `MERITUM_CORPUS_DATABASE_URL` | brak | adres libpq bazy ze schematem `corpus`; wymagany dla `postgres` |
| `MERITUM_EMBEDDINGS_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `vertex` |
| `MERITUM_EMBEDDINGS_MODEL` | `gemini-embedding-001` | model embeddingów w Vertex AI (ADR-04); adaptery biorą go tylko z ustawień |
| `MERITUM_EMBEDDINGS_REGION` | `europe-central2` | lokalizacja Vertex AI w UE (`EU_REGIONS`); region spoza UE (np. `us-central1`, `global`) kończy się błędem ustawień |
| `MERITUM_EMBEDDINGS_PROJECT` | projekt z ADC | projekt Google Cloud |
| `MERITUM_EMBEDDINGS_DIMENSIONS` | `768` | rozmiar wektora; tabele korpusu mają `vector(768)`, więc zmiana wymaga migracji i ponownego zwektoryzowania |

Dostawca embeddingów to Vertex AI (Google Cloud) w regionie UE, uwierzytelniony przez Application Default Credentials. Zapytania idą z typem `RETRIEVAL_QUERY`, fragmenty z `RETRIEVAL_DOCUMENT`. Korpus i zapytania muszą używać tego samego modelu i rozmiaru wektora.

### Model i region embeddingów (core#64)

Embeddingi liczymy tylko w UE (ADR-14): `gemini-embedding-001` w `europe-central2` (Warszawa), 768 wymiarów. Porównanie z 21.11.2026:

| | `gemini-embedding-001` | `text-multilingual-embedding-002` |
| --- | --- | --- |
| Jakość (MTEB Multilingual) | 1. miejsce w publikacji modelu (arXiv 2503.07891) | starsza generacja, niżej |
| Nasz test po polsku (12 pytań, 16 fragmentów, `europe-central2`) | recall@1 12/12, średni odstęp od najlepszego błędnego fragmentu 0,146 | recall@1 12/12, odstęp 0,115 |
| Działa w `europe-central2` | tak (sprawdzone wywołaniem) | tak (sprawdzone wywołaniem) |
| Wymiar | do 3072, u nas 768 (MRL) | 768 |
| Cena online (SKU Vertex AI) | 0,15 USD za 1 mln tokenów | 0,025 USD za 1 mln znaków |
| Koszt 10 mln znaków polskiego tekstu (~3 znaki na token) | ok. 0,50 USD | ok. 0,25 USD |

Wybraliśmy `gemini-embedding-001`: lepiej rozdziela polskie fragmenty, a różnica w koszcie przeliczenia całego korpusu to centy. Wymiar się nie zmienia, więc migracja `vector(768)` zostaje bez zmian. `gemini-embedding-2` nie jest dostępny w `europe-central2`.

Ponowne przeliczenie korpusu to lokalny skrypt, nigdy CI. Nadpisuje wektor każdego fragmentu w `corpus.passages` i wypisuje jedną linię JSON z modelem, regionem, wymiarem, liczbą fragmentów i czasem przebiegu:

```bash
MERITUM_EMBEDDINGS_PROVIDER=vertex MERITUM_CORPUS_DATABASE_URL=postgresql://... \
  uv run python scripts/reembed_corpus.py
```

Skrypt odmawia pracy ze stubem, bez bazy, z regionem spoza UE, z innym modelem niż `gemini-embedding-001` i z rozmiarem wektora innym niż 768. Zatwierdza wektory po każdej paczce, więc przerwany przebieg trzeba uruchomić ponownie, a linię JSON z wynikiem wkleić do PR albo zgłoszenia. Wektory zmienia też we fragmentach wycofanych, więc stare migawki widzą ten sam tekst, ale szukają już nowym modelem. Test integracyjny skryptu bierze adres z `MERITUM_TEST_DATABASE_URL` i przelicza tylko wstawione przez siebie wiersze.

Migracje leżą w `src/meritum_core/corpus/migrations/` (SQL, w kolejności numerów) i trafiają do pakietu. Są tylko wstecznie zgodne (dodajemy, nie usuwamy i nie zmieniamy nazw), bo schemat `corpus` czytają dev i prd; uruchamia je deploy z `main` (infra/004). Wymagają obrazu `meritum-postgres` z meritum-infra (pgvector, `pg_trgm`, `public.polish`). Schematu `corpus` nie zakładają: tworzy go platforma (`db.sh` w meritum-infra) i oddaje roli `meritum_worker_prd`, która ma na bazie tylko `CONNECT`, a `CREATE SCHEMA IF NOT EXISTS` wymaga prawa `CREATE` na bazie nawet wtedy, gdy schemat już jest. Test `tests/corpus/test_migrations_as_owner_integration.py` odtwarza ten układ na kopii bazy i stosuje migracje jako właściciel schematu.

Test adaptera na prawdziwej bazie uruchamia się lokalnie:

```bash
docker run -d --rm --name corpus -e POSTGRES_PASSWORD=test -e POSTGRES_DB=meritum -p 55432:5432 <obraz meritum-postgres>
MERITUM_CORPUS_DATABASE_URL=postgresql://postgres:test@localhost:55432/meritum uv run pytest -m integration tests/corpus
```

Migracja `0002_euvsdisinfo_copy.sql` dodaje tabele lokalnej kopii EUvsDisinfo (`euvsdisinfo_entries`, `euvsdisinfo_flagged_domains`), które zapisuje tylko workflow synchronizacji w meritum-worker (worker#59). Test `test_migrations_integration.py` uruchamia wszystkie migracje corpus dwa razy. Późniejsza zmiana tych tabel to nowy plik migracji (`ADD COLUMN IF NOT EXISTS`), bo poprawiony `CREATE TABLE` w 0002 nie dotrze do istniejącej bazy.

Migracja `0003_corpus_documents.sql` dodaje `corpus.documents` (jeden wiersz na pobrany adres: domena, `publisher_id` i licencja z katalogu, `fetched_at`, suma kontrolna i pełny tekst tylko dla systemu), `corpus.snapshot_manifest` (dokumenty, sumy kontrolne i `fetched_at` każdej `corpus_version`) oraz `corpus.ingest_attempts` (ostatnia próba wczytania każdej domeny katalogu, także nieudana, żeby domena bez żadnej pobranej strony czekała swoje `refresh_minutes`). Zapisują je workflowy wczytywania katalogu i migawek w meritum-worker (worker#17); retencja z worker#77 czyści `full_text` po 90 dniach od `fetched_at`, a wiersz zostaje. Fragmenty dokumentu leżą w `corpus.passages` z tym samym `source_id`.

Migracja `0006_publisher_removals.sql` dodaje `corpus.publisher_removals`, ewidencję wniosków wydawców o usunięcie tekstu (adres, `publisher_id`, `requested_at`, `removed_at` i liczba usuniętych dokumentów). Wiersz zapisuje workflow `publisher_removal` w meritum-worker (worker#77) w tej samej transakcji, w której kasuje dokumenty i fragmenty, więc widać, czy zmieścił się w 7 dniach. Numer 0006 idzie po 0004 i 0005 schematu `app`; numerów 0004 i 0005 w `corpus` nie ma, a pliki biegną w kolejności nazw.

Migracja `0007_documents_via.sql` dodaje do `corpus.documents` kolumnę `via`, czyli drogę, którą dokument trafił do korpusu (US-KOR-03, F-13). Wartości są te same co w `SourceVia` z kontraktów: `corpus`, `rss`, `web_search`, `mcp`, pilnuje ich ograniczenie `documents_via_known`. Wiersze sprzed migracji dostają `corpus`, domyślną wartość `SourceVia`, bo przyszły z wczytywania katalogu. Kontrakt się nie zmienia.

## Wyszukiwanie na żywo (`meritum_core.corpus.web_search`)

Przy świeżych twierdzeniach agent badawczy uzupełnia korpus wyszukiwaniem w sieci, ale tylko w domenach z katalogu (US-KOR-04, ADR-07). `build_web_search(WebSearchSettings(), load_catalog())` zwraca `WebSearchPort`; `search(MaskedText, limit=...)` daje listę `WebSearchCandidate` (adres, domena z katalogu, `publisher_id`). Port nie pobiera stron i nie zwraca ich treści: adres czyta potem fetcher (`corpus.fetching`, `FetchPurpose.SOURCE`, z robots.txt i Content-Signal) i dopiero wtedy można go cytować.

| Co | Wartość |
| --- | --- |
| Dostawca | Vertex AI Search (Discovery Engine v1, `:search` na `default_search`), basic website search z wzorcami INCLUDE dla domen katalogu. Data store, aplikację i wzorce zakłada Terraform w meritum-infra (infra#16) |
| Region | basic website search działa tylko w lokalizacji `global`, czyli **poza UE**. Dlatego do zapytania trafia wyłącznie twierdzenie po maskowaniu danych osobowych (`MaskedText`); nic więcej nie wychodzi. Wpis w rejestrze podmiotów przetwarzających: design-system#59 |
| Filtr Meritum | druga kontrola po stronie dostawcy: `catalog_entry_for` dopasowuje host (z subdomenami, bez `www.`) i ścieżkę wpisu segment po segmencie (`www.gov.pl/web/gis/ostrzezenia`); wygrywa najdokładniejszy wpis. Wpisy wykluczone i listy `source_status` niczego nie przepuszczają |
| Limity | `SEARCH_TIMEOUT_S` 10 s na jedno wyszukiwanie, `MAX_QUERIES_PER_MINUTE` 60 wyszukiwań w oknie 60 s na zbudowany port (budujemy go raz na proces), `limit` od 1 do 25 (maksimum basic website search) |
| Koszt | edycja Enterprise, 4 USD za 1 000 zapytań po 10 000 darmowych miesięcznie |

Błędy (wszystkie dziedziczą po `WebSearchError`, `check_status` = `technical_failure`): `WebSearchTimeoutError` (przekroczony czas), `WebSearchRateLimitError` (nasz limit zapytań albo 429 od dostawcy), `WebSearchUnavailableError` (inny błąd dostawcy, odrzucone dane logowania, nieczytelna odpowiedź). Komunikaty nie zawierają zapytania.

Zapasowy dostawca (core/024) implementuje `WebSearchProviderPort` (zapytanie → adresy) i przechodzi przez ten sam filtr i limity; jego testy wołają `provider_contract_violations(adapter)` i oczekują pustej listy.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_WEB_SEARCH_PROVIDER` | `stub` | `stub` (bez kluczy i sieci), `vertex_search`, `searxng` (zapas) albo `linkup` (opcjonalny) |
| `MERITUM_WEB_SEARCH_PROJECT` | brak | projekt Google Cloud aplikacji wyszukiwania; wymagany dla `vertex_search` |
| `MERITUM_WEB_SEARCH_ENGINE` | brak | id aplikacji (engine) Vertex AI Search nad website data store; wymagany dla `vertex_search` |
| `MERITUM_WEB_SEARCH_STUB_FIXTURE` | brak | plik JSON z listą adresów, które zwraca stub; bez niego stub nic nie znajduje |
| `MERITUM_WEB_SEARCH_SEARXNG_URL` | brak | adres naszej instancji SearXNG (np. `http://searxng:8080`); wymagany dla `searxng` |
| `MERITUM_WEB_SEARCH_LINKUP_API_KEY` | brak | klucz Linkup; wymagany dla `linkup` |
| `MERITUM_WEB_SEARCH_LINKUP_ENABLED` | `false` | wyłącznik Linkup; bez `true` ustawienia odrzucają `linkup` |

Brak wymaganej zmiennej to błąd walidacji `WebSearchSettings` z jej nazwą w komunikacie, więc test gotowości workflowu pokazuje, czego brakuje.

### Zapas: SearXNG i Linkup

Gdy Vertex AI Search nie działa albo chcemy uniezależnić się od jednego dostawcy, `MERITUM_WEB_SEARCH_PROVIDER=searxng` przełącza port na własną instancję SearXNG. Oba zapasowe adaptery stoją za tym samym `WebSearchPort`, z tym samym limitem czasu, limitem zapytań i filtrem `catalog_entry_for`.

| Co | SearXNG (`searxng`) | Linkup (`linkup`) |
| --- | --- | --- |
| Zapytanie | `GET {SEARXNG_URL}/search?format=json`, do `q` dopisane `(site:host1 OR site:host2 ...)` z hostów katalogu (`catalog_hosts`) | `POST https://api.linkup.so/v1/search`, `outputType=searchResults`, `depth=standard`, hosty katalogu w `includeDomains` |
| Ścieżki wpisów | nie trafiają do dostawcy; sprawdza je dopiero nasz filtr | jak obok |
| Włączenie | adres instancji | klucz i `LINKUP_ENABLED=true` |

Usługa SearXNG: obraz `docker.io/searxng/searxng` (przypnij tag z datą wydania), port 8080. W `settings.yml` instancji trzeba włączyć format JSON (`search.formats: [html, json]`), ustawić `server.secret_key` z sekretu, `server.limiter: false` (ruch tylko z sieci wewnętrznej workera) i wybrać silniki obsługujące `site:` (np. `duckduckgo`, `bing`, `brave`). Instancja stoi w tym samym regionie UE co worker i nie jest wystawiona publicznie; do silników wychodzi tylko zamaskowane twierdzenie. Dopisanie usługi do `docker-compose.yml` w meritum-monorepo i wdrożenie to osobna zmiana po decyzji o włączeniu zapasu.

Testy działają na nagranych odpowiedziach SearXNG i Linkup (`searxng-reply.json`, `linkup-reply.json`), bez sieci.

Uwierzytelnienie przez Application Default Credentials. Testy w CI działają na nagranych odpowiedziach w formacie Discovery Engine (`tests/corpus/web_search/fixtures/`), bez sieci. Zapytanie do prawdziwego data store tylko lokalnie:

```bash
gcloud auth application-default login
MERITUM_WEB_SEARCH_PROJECT=<projekt> MERITUM_WEB_SEARCH_ENGINE=<engine> uv run pytest -m integration tests/corpus/web_search
```

## OCR obrazów (`meritum_core.checks.ocr`)

Zrzut ekranu albo zdjęcie z tekstem leży w `BlobStore` (ADR-31), a żądanie niesie `image_id` (kontrakt v15; wyklucza `text`, `url` i `audio_id`). Workflow woła `OcrPort.read(image_id)` i dostaje `OcrResult`: tekst, pierwszą datę z tekstu jako kandydata na `claim_date` i metadane pliku. `date_confirms_publication` jest zawsze `false`: data widoczna na obrazie sama nie potwierdza, kiedy post faktycznie opublikowano. Tekst sprawdzamy dalej jak zwykły tekst (US-SPR-08, F-33). Od v16 `CheckResult` i `CachedResult` niosą odczytany tekst w opcjonalnym `image_text` (zamaskowany, jak `transcript` dla audio), żeby kanał mógł go pokazać.

Od v17 `Premises` niesie `signatory_reviews` (liczbę sygnatariuszy IFCN/EFCSN, których ocena zgadza się z werdyktem), a jedna taka ocena daje siłę co najmniej „umiarkowaną” (`strength_for`). Pole jest addytywne, domyślnie 0.

| Co | Wartość |
| --- | --- |
| Dostawca | Google Cloud Vision API przez REST, `DOCUMENT_TEXT_DETECTION`, punkt końcowy UE `eu-vision.googleapis.com` (ADR-14, ADR-30). Obraz wysyłamy w treści żądania; retencję po stronie Google'a opisuje jego dokumentacja Vision (nie trenuje na danych klienta), a w naszym `BlobStore` obraz żyje do `expires_at` |
| Formaty i limit | PNG, JPEG, WebP, do `MAX_IMAGE_BYTES` (10 MiB); format ustalają bajty pliku, nie typ MIME |
| Koszt | płatne według liczby obrazów (cennik Cloud Vision, pierwsze 1000 jednostek miesięcznie bezpłatnie); ponowienia liczą się jako osobne wywołania |
| Wyszukiwanie wcześniejszych wystąpień | `ImageSearchPort` nie ma jeszcze dostawcy: `build_image_search()` daje adapter, który zwraca `searched=false`. Odpowiedź pokazuje wtedy ograniczenie `image_search_not_run` |

Błędy: `UnsupportedImageError` (inny format, za duży plik) workflow mapuje na `out_of_scope` z `out_of_scope_code: "image"`; podtypy niosą `limitation_code` (`image_format_unsupported`, `image_too_large`). `OcrUnavailableError` (dostawca padł po ponowieniach, odrzucone dane logowania, odrzucony obraz) workflow mapuje na `technical_failure`. Brak pliku to `BlobNotFoundError`.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_OCR_PROVIDER` | `stub` | `stub` (bez kluczy i sieci) albo `vision` |
| `MERITUM_OCR_PROJECT` | brak | projekt Google Cloud z włączonym Cloud Vision API; wymagany dla `vision` |
| `MERITUM_OCR_RETRIES` | `3` | liczba prób HTTP przy 429 i 5xx (z pierwszą) |
| `MERITUM_OCR_STUB_TEXT` | brak | plik z tekstem, który stub „odczytuje” z każdego obrazu; bez niego stub rzuca `OcrUnavailableError` |

Uwierzytelnienie przez Application Default Credentials. Testy w CI działają na nagranych odpowiedziach Vision (`tests/checks/ocr/`), bez sieci; prawdziwy dostawca tylko lokalnie.

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

Błędy: `UnsupportedAudioError` (inny format, przekroczony limit) workflow mapuje na `out_of_scope`, `TranscriptionUnavailableError` (dostawca padł po ponowieniach, odrzucone dane logowania, operacja batch nie skończyła się w `BATCH_TIMEOUT_SECONDS`) na `technical_failure`; oba błędy niosą status w `check_status`. Podtypy `UnsupportedAudioFormatError` i `AudioTooLongError` niosą też kod ograniczenia w `limitation_code` (`audio_format_unsupported`, `audio_too_long`), który workflow w meritum-worker ma wpisywać do `limitation_codes` wyniku `out_of_scope`; sam wynik ma wtedy dostawać `out_of_scope_code: "audio"` (kontrakt v8), bez powtarzania szczegółu. Brak pliku to `BlobNotFoundError`.

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

## Baza aplikacji

Zapisy sprawdzeń, sprawy moderatora, tematy wysokiego ryzyka, powiadomienia i role personelu panelu (`StaffRepository`, adresy małymi literami) leżą w schemacie aplikacji środowiska (`app_dev` albo `app_prd`, infra#12). Kod nie zna nazwy schematu: bierze ją z `search_path` w adresie bazy. Każda tabela trzyma cały model kontraktu jako `jsonb` i kolumny, po których repozytoria filtrują i sortują.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_DATABASE_PROVIDER` | `memory` | `memory` (fake'i w procesie: testy, behave, praca bez bazy) albo `postgres` |
| `MERITUM_DATABASE_URL` | brak | adres libpq z `search_path` schematu aplikacji, np. `postgresql://worker_dev@host/meritum?options=-csearch_path%3Dapp_dev`; wymagany dla `postgres` |

Migracje leżą w `src/meritum_core/shared/database/migrations/` (SQL, w kolejności nazw), osobno od migracji schematu `corpus`. Uruchamia je deploy workera (worker/035) poleceniem:

```bash
MERITUM_DATABASE_URL=... uv run meritum-migrate-app
```

Każdy plik idzie raz (tabela `schema_migrations`), wszystko w jednej transakcji pod blokadą doradczą, więc drugie uruchomienie niczego nie zmienia, a dwa deploye naraz czekają na siebie. `SubjectEraser` w PostgreSQL usuwa w jednej transakcji zapisy osoby, jej powiadomienia, powiadomienia o jej sprawdzeniach (także te wysłane na jej drugi identyfikator) i jej sprawdzenia ze spraw moderatora. Identyfikatory usuniętych ze spraw sprawdzeń trafiają do tabeli `removed_case_checks`, a `ModeratorCaseRepository.save()` je pomija, więc sprawa wczytana przed usunięciem nie przywraca ich przy zapisie. Zapisy spraw idą pod jedną blokadą doradczą (`CASE_WRITE_LOCK`), żeby zapis równoległy z usuwaniem zawsze widział usunięte sprawdzenia.

Testy kontraktowe na prawdziwym PostgreSQL działają tylko lokalnie. Biorą adres z osobnej zmiennej `MERITUM_TEST_DATABASE_URL`, żeby nie trafić w bazę dev ustawioną w `MERITUM_DATABASE_URL`. Każdy test dostaje własny, świeżo zmigrowany schemat i usuwa go po sobie:

```bash
docker run -d --rm --name app-db -e POSTGRES_PASSWORD=test -e POSTGRES_DB=meritum -p 55433:5432 <obraz meritum-postgres>
MERITUM_TEST_DATABASE_URL=postgresql://postgres:test@localhost:55433/meritum uv run pytest -m integration tests/checks tests/moderation tests/notifications tests/observability tests/shared/database
```

## Maskowanie danych osobowych (`meritum_core.security.pii`)

Backend woła `await mask_personal_data(text, gate)` przed startem workflowu, a worker na wynikach kroków (US-BEZ-04, ADR-13). Bramkę buduje raz `build_pii_gate(PiiGateSettings())`. Najpierw działa bramka, potem wzorce telefonu, e-maila, PESEL-u i numeru dowodu osobistego, które działają zawsze. Wynik jest idempotentny: znaczniki nie zawierają cyfr ani `@`.

| Co | Wartość |
| --- | --- |
| Dostawca | Google Sensitive Data Protection (DLP API v2), `content:deidentify` na regionalnym endpoincie `dlp.<region>.rep.googleapis.com`, więc dane zostają w regionie także w tranzycie (ADR-14, ADR-35) |
| Region | z `MERITUM_PII_LOCATION`, domyślnie `europe-central2` (Warszawa); dozwolone tylko regiony w UE (`EU_LOCATIONS`), bez Londynu i Zurychu |
| Typy danych | `PHONE_NUMBER` → `[telefon]`, `EMAIL_ADDRESS` → `[e-mail]`, `POLAND_PESEL_NUMBER` → `[PESEL]`, `POLAND_NATIONAL_ID_NUMBER` → `[dowód osobisty]`, `POLAND_PASSPORT` → `[paszport]`, `IBAN_CODE` → `[numer konta]`, `CREDIT_CARD_NUMBER` → `[karta płatnicza]`, od prawdopodobieństwa `LIKELY` (`INFO_TYPE_MARKERS` w `constants.py`). Nigdy nie maskujemy `NEVER_MASKED_INFO_TYPES`: `PERSON_NAME`, `FIRST_NAME`, `LAST_NAME`, `ORGANIZATION_NAME`, `LOCATION`, `STREET_ADDRESS`, `DATE`, `DATE_OF_BIRTH` |
| Zasada | Maskujemy identyfikatory osoby: PESEL, numer dowodu, paszport, telefon, e-mail, numer konta IBAN, numer karty płatniczej. Nie maskujemy imion i nazwisk, nazw instytucji, miejsc, adresów, dat, kwot ani innych liczb, bez których zmienia się sens twierdzenia albo nie da się znaleźć dowodu (#102). Wzorzec telefonu pomija kwoty: grupę cyfr po innej grupie z tym samym separatorem tysięcy („1 450 000 000”), po znaku `$`/`€` albo przed jednostką (`zł`, `PLN`, `EUR`, `euro`, `USD`, `€`, `$`, `osób`, `tys.`, `mln`, `mld`) lub częścią dziesiętną. Ograniczenie: numer domu tuż przed telefonem pisanym ze spacjami („Długiej 5 601 234 567”) wygląda jak kwota i zostaje |
| Koszt | według cennika Sensitive Data Protection za inspekcję treści; nie potwierdziliśmy stawki dla regionu (załącznik B dokumentu produktowego) |
| Awaria | błąd dostawcy (`PiiGateUnavailableError`) nie zatrzymuje sprawdzenia: log zapisuje pominięcie bramki, a wzorce działają dalej (ADR-35) |

Logi nigdy nie zawierają maskowanego tekstu.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MERITUM_PII_GATE` | `none` | `none` (tylko wzorce, log zapisuje pominięcie) albo `sdp` |
| `MERITUM_PII_PROJECT` | brak | projekt Google Cloud z włączonym Sensitive Data Protection API; wymagany dla `sdp`. Adapter wysyła go też w nagłówku `x-goog-user-project`, bo bez niego DLP odrzuca lokalne poświadczenia użytkownika (403). Konto serwisowe API i workera potrzebuje więc w tym projekcie `roles/dlp.user` i `serviceusage.services.use` (np. `roles/serviceusage.serviceUsageConsumer`) |
| `MERITUM_PII_LOCATION` | `europe-central2` | region UE endpointu |

Uwierzytelnienie przez Application Default Credentials. Testy w CI działają bez sieci na odpowiedziach z atrapy HTTP (`tests/security/fixtures/`). `dlp-identifiers.json` to odpowiedź prawdziwego DLP w `europe-central2` na tekst z nazwiskiem, telefonem, PESEL-em i numerem dowodu (dane fikcyjne), nagrana 2026-11-21. Przy progu `LIKELY` DLP maskuje tylko PESEL: nie rusza telefonu `601 234 567` ani numeru dowodu `ABA300000` bez słów „dowodu osobistego” obok, więc oba łapią wzorce (numer dowodu z sumą kontrolną, jak PESEL). Prawdziwe wywołanie (lokalnie, nigdy w CI):

```bash
MERITUM_PII_PROJECT=<projekt> uv run pytest -m integration tests/security/test_pii_gate_integration.py
```

## Katalog źródeł (`meritum_core.corpus.catalog`)

Ta sekcja opisuje [`catalog.yaml`](src/meritum_core/corpus/catalog/catalog.yaml), czyli jawny katalog domen, w których Meritum szuka dowodów. Dokumentów nie dodajemy ręcznie. System pobiera je sam według katalogu: z RSS, map stron, API albo ze stałych adresów.

- Stan na 21.11.2026. robots.txt, Content-Signal i `/.well-known/tdmrep.json` sprawdzono automatycznie tego dnia.
- 57 wpisów: 51 włączonych (40 niezależnych wydawców) i 6 wykluczonych z podanym powodem.
- Wszystkie wpisy przechodzą walidację kontraktu `CatalogEntry` z `meritum-core` (`meritum_core.checks.contracts`).
- Członkostwo IFCN/EFCSN w polu `signatory_of` (tylko wydawcy ocen ClaimReview) ustalamy według obecności na oficjalnej liście sygnatariuszy IFCN w zakładce **Active** (https://ifcncodeofprinciples.poynter.org/signatories) albo na liście EFCSN (https://members.efcsn.com/signatories), stan na **2026-11-21**. Datę ważności odznaki na profilu IFCN nie bierzemy pod uwagę.

### Kolumny

Każdy wpis w `catalog.yaml` to dokładnie `CatalogEntry`. Kontrakt ma `extra="forbid"`, więc adresy wejścia, podstawy prawne i uwagi są tylko w README, w sekcji „Adresy wejścia, podstawy prawne i uwagi”. Z `catalog.yaml` core generuje `catalog/catalog.json` dla frontendu.

| Pole | Znaczenie |
|---|---|
| `domain` | Domena albo prefiks ścieżki (np. `www.gov.pl/web/rcb`). Wyszukiwanie na żywo używa go jako wzorca INCLUDE. |
| `publisher`, `publisher_id` | Wydawca. Wpisy z tym samym `publisher_id` liczą się jako jedno niezależne źródło (np. `imgw` dla meteo, hydro i baltyk). |
| `kind` | `instytucja`, `dane_publiczne`, `akt_prawny`, `fact_check` |
| `tier` | `primary`: urzędowe i pierwotne; `secondary`: fact-checkerzy |
| `role` | `evidence`: źródło dowodów. `source_status`: lista statusu źródła (sankcje, ostrzeżenia CERT). Ingest ją pomija, a sprawdzenie używa jej tylko do neutralnego ostrzeżenia z §5. |
| `license` | Licencja albo warunki ponownego wykorzystania |
| `ingest` | `rss`, `sitemap`, `api` (publiczne API: IMGW, GIOŚ, ELI, dane.gov.pl, GUS, NBP, Eurostat), `static` (stałe adresy pobierane cyklicznie), `mcp` (EUvsDisinfo), `live` (odpytywane na żywo w chwili sprawdzenia, poza migawką korpusu) |
| `refresh_minutes` | Co ile minut odświeżać, minimum 15. Ostrzeżenia 15–30 min. Brak przy `live`. |
| `validity` | `expires`: wygasa po `max_age_hours`, domyślnie 365 dni. `in_force`: obowiązuje, dopóki akt nie zostanie zmieniony („nie wygasa”). `updated_in_place`: strona stała, poprawiana na miejscu. |
| `max_age_hours` | Krótki próg dla ostrzeżeń, dróg, pogody i pomiarów |
| `qualified_because` | Powód kwalifikacji |
| `tdm_reservation` | `none`: brak zastrzeżenia. `reserved`: `ai-train=no` albo `ai-input=no` w Content-Signal robots.txt, znacznik meta `tdm-reservation` albo `noai`. Samo `Disallow` blokuje pobieranie, nie eksplorację, więc daje wykluczenie z powodem, a nie `reserved`. `unknown`: nie dało się odczytać. |
| `signatory_of` | `ifcn` i/lub `efcsn`, gdy wydawca jest na liście Active IFCN albo na liście sygnatariuszy EFCSN (reguła i data weryfikacji wyżej). Puste u wydawców bez członkostwa oraz u agregatorów i portali bez własnych ocen ClaimReview (np. EUvsDisinfo, EDMO, Check First, NASK). |
| `excluded`, `exclusion_reason` | Wykluczenie zawsze ma powód. Pola pomijamy, gdy wpis nie jest wykluczony. Wykluczenie nie zeruje `signatory_of`, jeśli Fact Check API ma rozpoznać wydawcę oceny. |

### Tabela audytu

Generuje ją `uv run python scripts/export_catalog.py` z `catalog.yaml`, razem z `catalog/catalog.json` dla strony „Jak działa Meritum” (kopiuje go `pnpm sync` w meritum-frontend). CI odrzuca nieaktualny eksport (`--check`). `load_catalog()` waliduje każdy wpis jako `CatalogEntry`, a `check_tdm()` zapisuje zastrzeżenie TDM właściciela w `tdm_reservation`. Pełny tekst dokumentu trzymamy `FULL_TEXT_RETENTION_DAYS` (90) dni od `fetched_at`.

<!-- catalog:start (scripts/export_catalog.py) -->
| Domena | Wydawca (`publisher_id`) | Poziom | Rola | Pobieranie | Odświeżanie (min) | Ważność | Zastrzeżenie TDM | Stan |
|---|---|---|---|---|---|---|---|---|
| `www.gov.pl/web/gov/ostrzezenia` | Rządowe Centrum Bezpieczeństwa (system ostrzeżeń gov.pl) (`rcb`) | primary | evidence | static | 15 | expires, 48 h | none | włączone |
| `www.gov.pl/web/mswia/regionalny-system-ostrzegania` | Ministerstwo Spraw Wewnętrznych i Administracji (`mswia`) | primary | evidence | static | 15 | expires, 48 h | none | włączone |
| `www.gov.pl/web/rcb` | Rządowe Centrum Bezpieczeństwa (`rcb`) | primary | evidence | static | 360 | expires, 72 h | none | włączone |
| `www.gov.pl/web/mswia` | Ministerstwo Spraw Wewnętrznych i Administracji (`mswia`) | primary | evidence | static | 360 | expires | none | włączone |
| `www.gov.pl/web/kgpsp` | Komenda Główna Państwowej Straży Pożarnej (`kg-psp`) | primary | evidence | static | 360 | expires | none | włączone |
| `policja.pl` | Komenda Główna Policji (`kgp`) | primary | evidence | rss | 30 | expires | none | włączone |
| `mazowiecka.policja.gov.pl` | Komenda Wojewódzka Policji z siedzibą w Radomiu (`kwp-radom`) | primary | evidence | static | 360 | expires | none | włączone |
| `www.gov.pl/web/obrona-narodowa` | Ministerstwo Obrony Narodowej (`mon`) | primary | evidence | static | 360 | expires | none | włączone |
| `www.gov.pl/web/gis` | Główny Inspektorat Sanitarny (`gis`) | primary | evidence | static | 360 | expires, 168 h | none | włączone |
| `www.gov.pl/web/paa` | Państwowa Agencja Atomistyki (`paa`) | primary | evidence | static | 360 | expires | none | włączone |
| `monitoring.paa.gov.pl` | Państwowa Agencja Atomistyki (`paa`) | primary | evidence | live |  | expires, 6 h | unknown | włączone |
| `powietrze.gios.gov.pl` | Główny Inspektorat Ochrony Środowiska (`gios`) | primary | evidence | live |  | expires, 3 h | none | włączone |
| `moje.cert.pl` | NASK – CERT Polska (`cert-polska`) | primary | evidence | static |  | expires | none | wykluczone: robots.txt: Disallow: / dla wszystkich robotów. Zamiast tego pobieramy cert.pl (RSS). |
| `cert.pl` | NASK – CERT Polska (`cert-polska`) | primary | evidence | rss | 30 | expires | none | włączone |
| `www.gov.pl/web/infrastruktura` | Ministerstwo Infrastruktury (`mi`) | primary | evidence | static | 360 | expires | none | włączone |
| `drogi.gddkia.gov.pl` | Generalna Dyrekcja Dróg Krajowych i Autostrad (`gddkia`) | primary | evidence | live |  | expires, 6 h | unknown | włączone |
| `www.gov.pl/web/gddkia` | Generalna Dyrekcja Dróg Krajowych i Autostrad (`gddkia`) | primary | evidence | static | 10080 | updated_in_place | none | włączone |
| `ulc.gov.pl` | Urząd Lotnictwa Cywilnego (`ulc`) | primary | evidence | static | 1440 | updated_in_place | unknown | włączone |
| `portalpasazera.pl` | PKP Polskie Linie Kolejowe (`pkp-plk`) | primary | evidence | live |  | expires, 6 h | unknown | włączone |
| `utk.gov.pl` | Urząd Transportu Kolejowego (`utk`) | primary | evidence | static |  | updated_in_place | none | wykluczone: robots.txt: Disallow: / dla wszystkich robotów. |
| `kgsok.pl` | Komenda Główna Straży Ochrony Kolei (`kg-sok`) | primary | evidence | sitemap | 1440 | expires | none | włączone |
| `www.sar.gov.pl` | Morska Służba Poszukiwania i Ratownictwa (`mspir`) | primary | evidence | static | 1440 | expires | none | włączone |
| `www.umgdy.gov.pl` | Urząd Morski w Gdyni (`um-gdynia`) | primary | evidence | static | 360 | expires, 72 h | none | włączone |
| `www.ums.gov.pl` | Urząd Morski w Szczecinie (`um-szczecin`) | primary | evidence | static | 360 | expires, 72 h | none | włączone |
| `www.gov.pl/web/wody-polskie` | Państwowe Gospodarstwo Wodne Wody Polskie (`wody-polskie`) | primary | evidence | static | 360 | expires, 72 h | none | włączone |
| `www.gov.pl/web/dyplomacja` | Ministerstwo Spraw Zagranicznych (`msz`) | primary | evidence | static | 360 | updated_in_place | none | włączone |
| `odyseusz.gov.pl` | Ministerstwo Spraw Zagranicznych (`msz`) | primary | evidence | static | 1440 | updated_in_place | none | włączone |
| `www.gov.pl/web/premier` | Kancelaria Prezesa Rady Ministrów (`kprm`) | primary | evidence | static | 360 | expires | none | włączone |
| `meteo.imgw.pl` | Instytut Meteorologii i Gospodarki Wodnej – PIB (`imgw`) | primary | evidence | live |  | expires, 24 h | none | włączone |
| `hydro.imgw.pl` | Instytut Meteorologii i Gospodarki Wodnej – PIB (`imgw`) | primary | evidence | live |  | expires, 24 h | none | włączone |
| `baltyk.imgw.pl` | Instytut Meteorologii i Gospodarki Wodnej – PIB (`imgw`) | primary | evidence | live |  | expires, 24 h | none | włączone |
| `isap.sejm.gov.pl` | Kancelaria Sejmu (`kancelaria-sejmu`) | primary | evidence | static |  | in_force | none | wykluczone: robots.txt: Disallow: / dla wszystkich robotów. Te same akty pobieramy z api.sejm.gov.pl (ELI). |
| `api.sejm.gov.pl` | Kancelaria Sejmu (`kancelaria-sejmu`) | primary | evidence | api | 10080 | in_force | none | włączone |
| `eur-lex.europa.eu` | Urząd Publikacji Unii Europejskiej (`urzad-publikacji-ue`) | primary | evidence | static | 10080 | in_force | unknown | włączone |
| `dane.gov.pl` | Ministerstwo Cyfryzacji (`mc`) | primary | evidence | api | 1440 | expires | none | włączone |
| `fakenews.pl` | Fundacja Przeciwdziałania Dezinformacji (fakenews.pl) (`fakenews-pl`) | secondary | evidence | rss | 60 | expires | none | włączone |
| `pravda.org.pl` | Stowarzyszenie Pravda (`pravda`) | secondary | evidence | rss | 60 | expires | none | włączone |
| `euvsdisinfo.eu` | Europejska Służba Działań Zewnętrznych (EUvsDisinfo) (`eeas-euvsdisinfo`) | secondary | evidence | mcp | 1440 | expires | none | włączone |
| `factchecktools.googleapis.com` | Google (agregator ocen ClaimReview) (`google-factcheck`) | secondary | evidence | live |  | expires | unknown | włączone |
| `demagog.org.pl` | Stowarzyszenie Demagog (`demagog`) | secondary | evidence | live |  | expires | reserved | wykluczone: Content-Signal ai-train=no, use=reference i blokady botów AI w robots.txt: nie pobieramy treści, tylko ocena z Fact Check API. |
| `sprawdzam.afp.com` | Agence France-Presse (AFP Sprawdzam) (`afp`) | secondary | evidence | live |  | expires | unknown | włączone |
| `konkret24.tvn24.pl` | TVN S.A. (Konkret24) (`konkret24`) | secondary | evidence | static |  | expires | none | wykluczone: Brak w IFCN i EFCSN; TVN wymaga umowy licencyjnej (zastrzeżenie z art. 25 ust. 1 pkt 1 lit. b pr. aut.). |
| `www.gov.pl/web/dyplomacja/bip` | Ministerstwo Spraw Zagranicznych (`msz`) | primary | evidence | static | 10080 | updated_in_place | none | włączone |
| `edmo.eu` | European Digital Media Observatory (`edmo`) | secondary | evidence | sitemap | 1440 | expires | none | włączone |
| `checkfirst.network` | CheckFirst (`checkfirst`) | secondary | evidence | rss | 1440 | expires | none | włączone |
| `www.nask.pl` | NASK – Państwowy Instytut Badawczy (`nask`) | secondary | evidence | static | 1440 | expires | none | włączone |
| `www.eeas.europa.eu` | Europejska Służba Działań Zewnętrznych (`eeas`) | primary | evidence | static | 360 | expires | none | włączone |
| `ec.europa.eu/commission/presscorner` | Komisja Europejska (`komisja-europejska`) | primary | evidence | rss | 60 | expires | none | włączone |
| `www.consilium.europa.eu` | Rada Unii Europejskiej (`rada-ue`) | primary | evidence | static |  | expires | none | wykluczone: Strona „Browser check” blokuje automaty (403), także robots.txt. Nie obchodzimy zabezpieczeń; decyzje Rady bierzemy z Dziennika Urzędowego w EUR-Lex. |
| `www.nato.int` | Organizacja Traktatu Północnoatlantyckiego (NATO) (`nato`) | primary | evidence | sitemap | 360 | expires | none | włączone |
| `bdl.stat.gov.pl` | Główny Urząd Statystyczny (`gus`) | primary | evidence | api | 10080 | expires | none | włączone |
| `api.nbp.pl` | Narodowy Bank Polski (`nbp`) | primary | evidence | api | 1440 | expires | none | włączone |
| `ec.europa.eu/eurostat` | Eurostat (Komisja Europejska) (`eurostat`) | primary | evidence | api | 10080 | expires | none | włączone |
| `pkw.gov.pl` | Państwowa Komisja Wyborcza (`pkw`) | primary | evidence | sitemap | 360 | expires | none | włączone |
| `webgate.ec.europa.eu/fsd` | Komisja Europejska (wykaz sankcji finansowych UE) (`komisja-europejska`) | primary | source_status | api | 1440 | expires, 48 h | none | włączone |
| `www.gov.pl/web/mswia/lista-osob-i-podmiotow-objetych-sankcjami` | Ministerstwo Spraw Wewnętrznych i Administracji (`mswia`) | primary | source_status | static | 1440 | expires, 48 h | none | włączone |
| `hole.cert.pl` | NASK – CERT Polska (Lista ostrzeżeń) (`cert-polska`) | primary | source_status | api | 60 | expires, 24 h | none | włączone |
<!-- catalog:end -->

### Podstawy prawne

- **Materiały urzędowe** (komunikaty i ostrzeżenia organów): art. 4 pkt 2 ustawy o prawie autorskim stanowi, że nie są przedmiotem prawa autorskiego. Dodatkowo treści tekstowe na gov.pl są na licencji **CC BY-SA 4.0** (potwierdzone w stopce gov.pl, strona `gov.pl/web/gov/prawa-autorskie`), a KPRM udostępnia je na CC BY 3.0 PL. Zdjęć i wideo z gov.pl (CC BY-NC-ND 4.0) nie pobieramy.
- **Dane publiczne** (IMGW, GIOŚ, PAA, GDDKiA, dane.gov.pl): ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu informacji sektora publicznego. IMGW wskazuje też rozporządzenie wykonawcze (UE) 2023/138 o zbiorach wysokiej wartości i art. 385–387 Prawa wodnego.
- **Akty prawne:** akty normatywne RP nie są utworami (art. 4 pkt 1 pr. aut.). Dokumenty EUR-Lex można ponownie wykorzystywać na zasadach decyzji Komisji 2011/833/UE, co potwierdza nota prawna EUR-Lex.
- **Fact-checkerzy:** ich artykuły są chronione prawem autorskim. Pokazujemy krótki cytat z linkiem (prawo cytatu, art. 29 pr. aut.). Eksplorację tekstów prowadzimy tylko tam, gdzie wydawca jej nie zastrzegł (art. 26¹ pr. aut., art. 4 dyrektywy 2019/790).
- **Przechowywanie:** pełny tekst trzymamy 90 dni od pobrania, metadane i cytowane fragmenty tak długo jak zapis przebiegu.

### Źródła

#### 1. Ostrzeżenia i bezpieczeństwo (lista organizatora)

System ostrzeżeń gov.pl, RSO (MSWiA), raport dobowy RCB, MSWiA, KG PSP, Policja (KGP i KWP Radom), MON, GIS, PAA z monitoringiem promieniowania, GIOŚ (jakość powietrza), CERT Polska.

Są to urzędowe źródła pierwotne dla tematów, w których dezinformacja jest najgroźniejsza: zagrożenia, alarmy, skażenia, oszustwa. Ostrzeżenia mają krótki próg ważności (48 h, dla pomiarów 3–6 h), bo stare ostrzeżenie łatwo podać jako aktualne.

#### 2. Transport, podróże, morze (lista organizatora)

Ministerstwo Infrastruktury, GDDKiA (utrudnienia i infolinia 19 111), ULC (prawa pasażera lotniczego), Portal Pasażera (PKP PLK), UTK, Straż Ochrony Kolei, MSPiR (SAR), Urzędy Morskie w Gdyni i Szczecinie, Wody Polskie, MSZ (informacje dla podróżujących, Odyseusz), KPRM.

Utrudnienia drogowe i kolejowe mają próg 6 h, komunikaty nawigacyjne 72 h. Prawa pasażera i strony infolinii mają `updated_in_place`.

#### 3. Pogoda i hydrologia (lista organizatora)

IMGW-PIB: meteo, hydro, baltyk. Ostrzeżenia bierzemy z oficjalnego API `danepubliczne.imgw.pl`, a nie ze stron, bo API daje stabilny format i datę wydania. Próg ważności to 24 h.

#### 4. Prawo: ISAP i EUR-Lex (dodane przez nas)

**Uzasadnienie:** wiele twierdzeń dotyczy przepisów, np. „od jutra nowy podatek”, „prezydent może mieć trzy kadencje” czy „UE zakazuje…”. Werdykt w takiej sprawie wymaga tekstu aktu, a nie komunikatu o nim. Akty mają `validity = in_force`, czyli nie wygasają z wiekiem, dopóki nie zostaną zmienione.

- **ISAP jest wykluczony**, bo robots.txt `isap.sejm.gov.pl` zabrania wszystkiego (`Disallow: /`). Te same akty pobieramy z oficjalnego **API ELI Kancelarii Sejmu** (`api.sejm.gov.pl`, robots.txt `Allow: /`). Użytkownikowi można nadal pokazywać link do ISAP.
- **EUR-Lex:** pobieramy wybrane akty. Strona odpowiada automatom kodem 202 (ochrona antybotowa), więc pewniejsza droga to repozytorium Cellar Urzędu Publikacji.
- **dane.gov.pl:** liczby do twierdzeń statystycznych. Licencję zapisujemy osobno dla każdego zbioru.

#### 5. Fact-checkerzy (punkt 2 listy organizatora)

- **Google Fact Check Tools API** (`claims:search`) wyszukuje oceny ClaimReview do twierdzenia. Zwraca same metadane: wydawcę, ocenę, tytuł, datę i link. Ocenę fact-checkera z IFCN albo EFCSN pokazujemy jako przesłankę z linkiem (ADR-24, ADR-34). Nie przechowujemy jej dłużej, niż pozwalają nagłówki cache (Google APIs Terms §5(e)). Do ręcznego podglądu służy Fact Check Explorer (`toolbox.google.com/factcheck/explorer`).
- **`signatory_of`**: członkostwo = obecność na liście Active IFCN (https://ifcncodeofprinciples.poynter.org/signatories) albo na liście sygnatariuszy EFCSN (https://members.efcsn.com/signatories), sprawdzone 2026-11-21, bez patrzenia na datę ważności odznaki IFCN na profilu.
- **fakenews.pl** i **pravda.org.pl** to sygnatariusze IFCN bez blokad dla robotów. Pobieramy je z RSS jako źródła wtórne.
- **AFP Sprawdzam** zwraca automatom 403. Jego ocena wchodzi tylko przez Fact Check API.

#### 6. Operacje informacyjne (punkt 3 listy organizatora)

**EUvsDisinfo** (EEAS) to baza przypadków prorosyjskiej dezinformacji. Pobieramy ją przez serwer MCP do lokalnej kopii, a instrukcja organizatora (`How_to_grab_all_Articles_and_Cases_from_disinfo.pdf`) opisuje pobranie całości. Służy do sprawdzenia, czy podobne twierdzenie pojawiło się już w znanej operacji. Teksty „fact” są cytowalnym dowodem wtórnym.

#### 7. Punkty odniesienia z treści zadania (§7)

| Zadanie wymienia | W katalogu |
|---|---|
| dane.gov.pl | `dane.gov.pl` |
| BIP | `www.gov.pl/web/dyplomacja/bip` (BIP MSZ). BIP-y innych instytucji dodajemy, gdy wymaga tego przypadek testowy. |
| ISAP | Przez `api.sejm.gov.pl` (ELI), bo robots.txt ISAP blokuje roboty |
| EUR-Lex | `eur-lex.europa.eu` |
| Korpusy fact-checkerów IFCN i EFCSN | fakenews.pl, pravda.org.pl. Demagog i AFP tylko przez Fact Check API. |
| EDMO | `edmo.eu`: briefy i przeglądy dezinformacji w UE, po angielsku |
| EUvsDisinfo | `euvsdisinfo.eu` przez MCP |
| Check First | `checkfirst.network`: raporty o konkretnych operacjach FIMI, do dopasowania incydentów (scenariusz I). robots.txt wprost dopuszcza roboty AI. |
| Materiały NASK o dezinformacji | `www.nask.pl`: aktualności z tagiem „Dezinformacja”. Pakiet NASK od organizatora dopiszemy, gdy go dostaniemy. |

EDMO, Check First i NASK mają `tier = secondary`. Ich analizy cytujemy krótko z linkiem, tak jak teksty fact-checkerów. NASK jest instytutem badawczym, a nie organem, więc jego teksty nie są materiałami urzędowymi w rozumieniu art. 4.

#### 8. UE i NATO (dodane przez nas)

**Uzasadnienie:** zadanie dotyczy sytuacji międzynarodowej i zagranicznych manipulacji (FIMI), a twierdzenia o UE i NATO można rozstrzygnąć tylko u źródła.

- **EEAS:** stanowiska UE w polityce zagranicznej. Ma inny `publisher_id` niż EUvsDisinfo, bo to inna redakcja.
- **Komisja Europejska (Press Corner):** ma RSS po polsku.
- **NATO:** pobieranie z mapy strony. Warunki ponownego użycia są jeszcze do potwierdzenia.
- **Rada UE jest wykluczona:** strona „Browser check” blokuje automaty. Nie obchodzimy zabezpieczeń (§5 zadania), a decyzje Rady są w Dzienniku Urzędowym w EUR-Lex.

Te źródła są głównie po angielsku, więc wspierają wyszukiwanie wielojęzyczne z odpowiedzią po polsku (funkcja premiowana).

#### 9. Dane liczbowe (dodane przez nas)

GUS (API BDL i DBW), NBP, Eurostat i PKW. Twierdzenia liczbowe to najczęstszy przypadek scenariusza C, czyli dwóch wiarygodnych źródeł z różnymi danymi. GUS i Eurostat to dwaj niezależni wydawcy tych samych wskaźników. Wybory są klasycznym celem FIMI. Wszystkie źródła mają publiczne API bez klucza, które działało przy sprawdzeniu.

#### 10. Status źródła: ostrzeżenie, nie dowód

Paragraf 5 zadania mówi, że objęcie podmiotu sankcjami UE nie może przesądzać o prawdziwości twierdzenia, a system ma pokazać odrębne, neutralne ostrzeżenie. Do tego służą trzy wpisy:

- **Wykaz sankcji finansowych UE:** CSV Komisji, około 9 MB.
- **Lista sankcyjna MSWiA.**
- **Lista ostrzeżeń CERT (`hole.cert.pl`):** domeny wyłudzające, do ostrzeżenia przy linku w scenariuszu I.

**Te wpisy nie mogą trafiać do wyszukiwania dowodów.** W katalogu mają `role: source_status`, więc ingest je pomija.

### Wykluczone

| Źródło | Powód |
|---|---|
| isap.sejm.gov.pl | robots.txt `Disallow: /`. Zastępuje go api.sejm.gov.pl. |
| moje.cert.pl | robots.txt `Disallow: /`. Zastępuje go cert.pl z RSS, ten sam wydawca. |
| utk.gov.pl | robots.txt `Disallow: /`. Do rozważenia: zgoda UTK albo samo linkowanie. |
| demagog.org.pl | `Content-Signal: ai-train=no, use=reference` i blokady botów AI. Treści nie pobieramy, ocena przychodzi z Fact Check API. |
| konkret24.tvn24.pl | Brak w IFCN i EFCSN, TVN wymaga umowy licencyjnej. |
| consilium.europa.eu | Strona „Browser check” blokuje automaty. Decyzje Rady bierzemy z EUR-Lex. |

### Ryzyka dostępu

- **GDDKiA, ULC:** ochrona Incapsula zwraca stronę antybotową zamiast robots.txt i tdmrep (`tdm_reservation = unknown`). Pobranie może się nie udać. SAR ma tę samą ochronę, ale kontrola z 21.11 odczytała jego robots.txt i znaczniki meta bez zastrzeżenia (`none`).
- **portalpasazera.pl:** błąd certyfikatu TLS (curl 60).
- **monitoring.paa.gov.pl:** robots.txt przekierowuje, tdmrep zwraca 403.
- **umgdy.gov.pl:** robots.txt wskazuje mapę strony na serwerze deweloperskim wykonawcy. Nie używamy jej.
- **Brak RSS na gov.pl:** wpisy gov.pl mają `ingest = static`, czyli cykliczne pobieranie stron list.
- **Kontrola TDM:** `uv run python scripts/check_catalog_tdm.py` czyta Content-Signal z robots.txt hosta i znaczniki meta strony wpisu przez fetcher stron, wypisuje różnice, a z `--write` zapisuje je w `catalog.yaml`. Gdy któregoś sygnału nie da się odczytać (antybot, błąd serwera, strona wymagająca JavaScriptu), wpis zostaje bez zmian. `/.well-known/tdmrep.json` nie jest czytany, bo fetcher nie przyjmuje JSON-a.

### Ustalenia (core#22)

1. `refresh_minutes` z minimum 15 zamiast `refresh_hours`. Ostrzeżenia gov.pl i RSO: 15 min, Policja i CERT: 30 min, reszta przeliczona z godzin.
2. `ingest = api` obejmuje wszystkie publiczne API. Opis pola w kontrakcie jest poprawiony.
3. Demagog zostaje `excluded`. Jego `publisher_id` służy do rozpoznania wydawcy ClaimReview (core#27).
4. Ostrzeżenia gov.pl wydaje RCB (`rcb`). Portal Pasażera i SOK to oficjalne informacje przewoźnika, nie organu.
5. Pole `role: evidence | source_status` w tym samym katalogu. `source_status`: sankcje UE (`webgate.ec.europa.eu/fsd`), sankcje MSWiA, `hole.cert.pl`.
6. Źródła krótkotrwałe mają `ingest = live` i nie mają `refresh_minutes`: monitoring PAA, GIOŚ, drogi GDDKiA, Portal Pasażera, meteo, hydro i baltyk IMGW. Tak samo Fact Check API oraz AFP i Demagog, których oceny przychodzą przez to API.

Kontrakt odrzuca wpis `live` z `refresh_minutes`.

### Adresy wejścia, podstawy prawne i uwagi

#### `www.gov.pl/web/gov/ostrzezenia`

- Wejście: https://www.gov.pl/web/gov/ostrzezenia
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Brak RSS. Widok wojewódzki: #/_/<województwo>/wszystkie. Wydawcę potwierdzić.

#### `www.gov.pl/web/mswia/regionalny-system-ostrzegania`

- Wejście: https://www.gov.pl/web/mswia/regionalny-system-ostrzegania
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `www.gov.pl/web/rcb`

- Wejście: https://www.gov.pl/web/rcb/raport-dobowy3
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Obejmuje też stronę główną RCB.

#### `www.gov.pl/web/mswia`

- Wejście: https://www.gov.pl/web/mswia
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `www.gov.pl/web/kgpsp`

- Wejście: https://www.gov.pl/web/kgpsp/aktualnosci
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `policja.pl`

- Wejście: https://policja.pl/pol/aktualnosci
- Podstawa prawna: art. 4 pkt 2 pr. aut.
- Uwagi: RSS: https://policja.pl/dokumenty/rss/1-rss-1.rss. robots.txt blokuje tylko /ftp/.

#### `mazowiecka.policja.gov.pl`

- Wejście: https://mazowiecka.policja.gov.pl/ra/aktualnosci/aktualnosci
- Podstawa prawna: art. 4 pkt 2 pr. aut.
- Uwagi: robots.txt blokuje tylko /ftp/.

#### `www.gov.pl/web/obrona-narodowa`

- Wejście: https://www.gov.pl/web/obrona-narodowa/aktualnosci5
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `www.gov.pl/web/gis`

- Wejście: https://www.gov.pl/web/gis/ostrzezenia
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Ostrzeżenia o produktach bywają aktualne dłużej; próg 7 dni do strojenia.

#### `www.gov.pl/web/paa`

- Wejście: https://www.gov.pl/web/paa/panstwowa-agencja-atomistyki
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `monitoring.paa.gov.pl`

- Wejście: https://monitoring.paa.gov.pl/
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: robots.txt i tdmrep zwracają 302/403; sprawdzić przed pobraniem.

#### `powietrze.gios.gov.pl`

- Wejście: https://powietrze.gios.gov.pl/pjp/
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: API: https://api.gios.gov.pl/pjp-api/v1/rest/ (działa). Brak robots.txt (404).

#### `moje.cert.pl`

- Wejście: https://moje.cert.pl/komunikaty/
- Uwagi: Zastąpione wpisem cert.pl.

#### `cert.pl`

- Wejście: https://cert.pl/
- Podstawa prawna: art. 4 pkt 2 pr. aut.
- Uwagi: RSS: https://cert.pl/feed/ (działa).

#### `www.gov.pl/web/infrastruktura`

- Wejście: https://www.gov.pl/web/infrastruktura/aktualnosci
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Strony prawa-pasazerow, infolinia, dane-kontaktowe są stałe: można je dać osobnym wpisem updated_in_place.

#### `drogi.gddkia.gov.pl`

- Wejście: https://drogi.gddkia.gov.pl/informacje-drogowe/lista-utrudnien
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: Ochrona Incapsula: robots.txt zwraca stronę antybotową. Ryzyko braku dostępu.

#### `www.gov.pl/web/gddkia`

- Wejście: https://www.gov.pl/web/gddkia/informacja-drogowa---19-111
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `ulc.gov.pl`

- Wejście: https://ulc.gov.pl/prawa-pasazera/poradnik-dla-pasazerow
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: Ochrona Incapsula przy tdmrep; robots.txt bez blokad.

#### `portalpasazera.pl`

- Wejście: https://portalpasazera.pl/
- Podstawa prawna: do sprawdzenia: spółka, nie organ (art. 4 może nie obejmować)
- Uwagi: Błąd certyfikatu TLS przy pobraniu (curl 60). Sprawdzić przed włączeniem.

#### `utk.gov.pl`

- Wejście: https://utk.gov.pl/pl/pasazerowie
- Uwagi: Można zapytać UTK o zgodę albo cytować przez wyszukiwanie na żywo z linkiem.

#### `kgsok.pl`

- Wejście: https://kgsok.pl/
- Podstawa prawna: SOK jest formacją PKP PLK; status materiału urzędowego do sprawdzenia
- Uwagi: Mapa strony: https://kgsok.pl/wp-sitemap.xml.

#### `www.sar.gov.pl`

- Wejście: https://www.sar.gov.pl/
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: Ochrona Incapsula przy tdmrep; robots.txt bez blokad.

#### `www.umgdy.gov.pl`

- Wejście: https://www.umgdy.gov.pl/
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: robots.txt wskazuje mapę strony na umgdynia.dev.kdmc.pl (błąd wydawcy, nie używać).

#### `www.ums.gov.pl`

- Wejście: https://www.ums.gov.pl/bezpieczenstwo-morskie/warunki-zeglugi
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP

#### `www.gov.pl/web/wody-polskie`

- Wejście: https://www.gov.pl/web/wody-polskie/komunikaty-nawigacyjne
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `www.gov.pl/web/dyplomacja`

- Wejście: https://www.gov.pl/web/dyplomacja/informacje-dla-podrozujacych
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Także źródło BIP MSZ.

#### `odyseusz.gov.pl`

- Wejście: https://odyseusz.gov.pl/
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: Aplikacja SPA bez robots.txt; treść głównie w gov.pl/web/dyplomacja.

#### `www.gov.pl/web/premier`

- Wejście: https://www.gov.pl/web/premier
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie

#### `meteo.imgw.pl`

- Wejście: https://meteo.imgw.pl/
- Podstawa prawna: ustawa z 11.08.2021 o otwartych danych; rozp. wyk. (UE) 2023/138; art. 385–387 Prawa wodnego
- Uwagi: API ostrzeżeń: https://danepubliczne.imgw.pl/api/data/warningsmeteo (działa).

#### `hydro.imgw.pl`

- Wejście: https://hydro.imgw.pl/
- Podstawa prawna: jak meteo.imgw.pl
- Uwagi: API: https://danepubliczne.imgw.pl/api/data/warningshydro (działa).

#### `baltyk.imgw.pl`

- Wejście: https://baltyk.imgw.pl/
- Podstawa prawna: jak meteo.imgw.pl
- Uwagi: Mapa strony: https://baltyk.imgw.pl/sitemap.xml.

#### `isap.sejm.gov.pl`

- Wejście: https://isap.sejm.gov.pl/
- Uwagi: Zastąpione wpisem api.sejm.gov.pl; link dla użytkownika może dalej prowadzić do ISAP.

#### `api.sejm.gov.pl`

- Wejście: https://api.sejm.gov.pl/eli/acts/DU/2024
- Podstawa prawna: art. 4 pkt 1 pr. aut. (akty normatywne nie są utworami)
- Uwagi: robots.txt: Allow: /. Pobieramy wybrane akty, nie całość.

#### `eur-lex.europa.eu`

- Wejście: https://eur-lex.europa.eu/
- Podstawa prawna: decyzja Komisji 2011/833/UE; nota prawna EUR-Lex
- Uwagi: robots.txt i tdmrep zwracają 202 (ochrona przed botami). Lepiej pobierać przez Cellar/SPARQL Urzędu Publikacji.

#### `dane.gov.pl`

- Wejście: https://dane.gov.pl/
- Podstawa prawna: ustawa z 11.08.2021 o otwartych danych
- Uwagi: Aplikacja SPA bez robots.txt. Licencję zapisujemy per zbiór.

#### `fakenews.pl`

- Wejście: https://fakenews.pl/
- Podstawa prawna: art. 29 pr. aut. (prawo cytatu); art. 26^1 pr. aut. (TDM, brak zastrzeżenia)
- Uwagi: RSS https://fakenews.pl/feed/, mapa https://fakenews.pl/sitemap_index.xml. robots.txt bez blokad AI.
- Członkostwo: lista IFCN (Active) 2026-11-21 — https://ifcncodeofprinciples.poynter.org/signatories, profil https://www.ifcncodeofprinciples.poynter.org/profile/fundacja-%22przeciwdzia%C5%82amy-dezinformacji%22; `signatory_of: [ifcn]`. Brak na liście EFCSN 2026-11-21 — https://members.efcsn.com/signatories.

#### `pravda.org.pl`

- Wejście: https://pravda.org.pl/
- Podstawa prawna: art. 29 pr. aut. (prawo cytatu); art. 26^1 pr. aut. (TDM, brak zastrzeżenia)
- Uwagi: RSS https://pravda.org.pl/rss/, mapa https://pravda.org.pl/sitemap.xml.
- Członkostwo: IFCN (Active) i EFCSN 2026-11-21 — https://ifcncodeofprinciples.poynter.org/signatories, https://members.efcsn.com/signatories; `signatory_of: [ifcn, efcsn]`.

#### `euvsdisinfo.eu`

- Wejście: https://euvsdisinfo.eu/
- Podstawa prawna: nota prawna EEAS; licencja bazy niepotwierdzona
- Uwagi: MCP https://euvsdisinfo-mcp-server.vercel.app/mcp; instrukcja organizatora: euvsdisinfo.eu/public-docs/How_to_grab_all_Articles_and_Cases_from_disinfo.pdf. robots.txt blokuje */feed/.

#### `factchecktools.googleapis.com`

- Wejście: https://developers.google.com/fact-check/tools/api/reference/rest
- Podstawa prawna: warunki Google APIs; artykuły należą do wydawców
- Uwagi: Zapytanie przy każdym sprawdzeniu; bez trwałych kopii ponad nagłówki cache. Podgląd: toolbox.google.com/factcheck/explorer. publisher_id oceny bierzemy od wydawcy ClaimReview.

#### `demagog.org.pl`

- Wejście: https://demagog.org.pl/
- Podstawa prawna: zastrzeżenie TDM z art. 4 dyrektywy 2019/790
- Uwagi: publisher_id potrzebny do rozpoznania wydawcy oceny ClaimReview.
- Członkostwo: IFCN (Active) i EFCSN 2026-11-21 — https://ifcncodeofprinciples.poynter.org/signatories, https://members.efcsn.com/signatories; `signatory_of: [ifcn, efcsn]` (wykluczenie dotyczy treści, nie rozpoznania wydawcy w Fact Check API).

#### `sprawdzam.afp.com`

- Wejście: https://sprawdzam.afp.com/
- Uwagi: robots.txt, RSS i tdmrep zwracają 403 (Akamai). Nie pobieramy treści.
- Członkostwo: AFP Fact Check na liście IFCN (Active) i AFP na liście EFCSN 2026-11-21 — https://ifcncodeofprinciples.poynter.org/signatories, https://members.efcsn.com/signatories; `signatory_of: [ifcn, efcsn]` dla polskiego serwisu Sprawdzam.

#### `konkret24.tvn24.pl`

- Wejście: https://konkret24.tvn24.pl/
- Członkostwo: brak na listach IFCN i EFCSN 2026-11-21 — https://ifcncodeofprinciples.poynter.org/signatories, https://members.efcsn.com/signatories; `signatory_of` puste.

#### `www.gov.pl/web/dyplomacja/bip`

- Wejście: https://www.gov.pl/web/dyplomacja/bip
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: BIP-y innych instytucji z katalogu dopisujemy według potrzeb przypadków testowych; ogólny spis: https://www.gov.pl/bip.

#### `edmo.eu`

- Wejście: https://edmo.eu/
- Podstawa prawna: art. 29 pr. aut. (prawo cytatu); art. 26^1 pr. aut. (TDM, brak zastrzeżenia)
- Uwagi: Mapa strony: https://edmo.eu/sitemap_index.xml (/feed/ zwraca HTML). robots.txt blokuje tylko /wp-json/. Teksty po angielsku.

#### `checkfirst.network`

- Wejście: https://checkfirst.network/
- Podstawa prawna: art. 29 pr. aut. (prawo cytatu); art. 26^1 pr. aut. (TDM, brak zastrzeżenia)
- Uwagi: RSS: https://checkfirst.network/feed/. robots.txt wprost dopuszcza roboty AI, llms.txt prosi o podanie źródła.

#### `www.nask.pl`

- Wejście: https://www.nask.pl/aktualnosci
- Podstawa prawna: art. 29 pr. aut. (prawo cytatu); NASK nie jest organem, więc art. 4 nie obejmuje
- Uwagi: robots.txt: Allow: /. Bierzemy aktualności z tagiem „Dezinformacja”; brak RSS. Pakiet NASK od organizatora dopiszemy osobno.

#### `www.eeas.europa.eu`

- Wejście: https://www.eeas.europa.eu/eeas/press-material_en
- Podstawa prawna: nota prawna EEAS: reuse is authorised, provided the source is acknowledged
- Uwagi: Brak RSS; pobieramy listę materiałów prasowych. Inny publisher_id niż eeas-euvsdisinfo, bo to inna redakcja. Teksty po angielsku.

#### `ec.europa.eu/commission/presscorner`

- Wejście: https://ec.europa.eu/commission/presscorner/home/pl
- Podstawa prawna: decyzja Komisji 2011/833/UE
- Uwagi: RSS: https://ec.europa.eu/commission/presscorner/api/rss?language=pl (działa, także po polsku).

#### `www.consilium.europa.eu`

- Wejście: https://www.consilium.europa.eu/pl/press/press-releases/
- Uwagi: Zastąpione wpisem eur-lex.europa.eu.

#### `www.nato.int`

- Wejście: https://www.nato.int/cps/en/natohq/news.htm
- Podstawa prawna: do potwierdzenia: warunki ponownego użycia NATO
- Uwagi: Mapa strony: https://www.nato.int/sitemap.xml. robots.txt blokuje tylko */newsletter/*. Teksty po angielsku.

#### `bdl.stat.gov.pl`

- Wejście: https://bdl.stat.gov.pl/api/v1/subjects?format=json
- Podstawa prawna: ustawa o statystyce publicznej; ustawa z 11.08.2021 o otwartych danych
- Uwagi: API BDL działa; także API Dziedzinowej Bazy Wiedzy: https://api-dbw.stat.gov.pl/. Warunki portalu GUS do potwierdzenia.

#### `api.nbp.pl`

- Wejście: https://api.nbp.pl/api/exchangerates/tables/a/?format=json
- Podstawa prawna: ustawa z 11.08.2021 o otwartych danych
- Uwagi: API działa, bez klucza.

#### `ec.europa.eu/eurostat`

- Wejście: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=PL&lastTimePeriod=1
- Podstawa prawna: decyzja Komisji 2011/833/UE
- Uwagi: API działa. robots.txt blokuje tylko stare SDMX i wyszukiwarkę.

#### `pkw.gov.pl`

- Wejście: https://pkw.gov.pl/aktualnosci
- Podstawa prawna: art. 4 pkt 2 pr. aut.
- Uwagi: Mapa strony: https://pkw.gov.pl/sitemaps/sitemap_1.xml. Wyniki wyborów: wybory.gov.pl.

#### `webgate.ec.europa.eu/fsd`

- Wejście: https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw
- Podstawa prawna: decyzja Komisji 2011/833/UE
- Uwagi: CSV ok. 9 MB, działa. Do zbioru sankcji medialnych (RT, Sputnik) dochodzą rozporządzenia Rady z EUR-Lex.

#### `www.gov.pl/web/mswia/lista-osob-i-podmiotow-objetych-sankcjami`

- Wejście: https://www.gov.pl/web/mswia/lista-osob-i-podmiotow-objetych-sankcjami
- Podstawa prawna: art. 4 pkt 2 pr. aut. (materiały urzędowe); warunki gov.pl/web/gov/prawa-autorskie
- Uwagi: Strona HTML ok. 2 MB.

#### `hole.cert.pl`

- Wejście: https://hole.cert.pl/domains/v2/domains.txt
- Podstawa prawna: art. 4 pkt 2 pr. aut.; ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu ISP
- Uwagi: Plik tekstowy ok. 2,6 MB, działa. Opis: https://cert.pl/lista-ostrzezen/.

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
