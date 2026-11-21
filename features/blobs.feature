Feature: Magazyn plików
  Backend zapisuje nagranie albo obraz, worker czyta je po identyfikatorze (ADR-31).

  Scenario: zapis i odczyt nagrania
    Given plik OGG o rozmiarze 300 KB
    When backend zapisuje go przez BlobStore
    Then dostaje audio_id, a worker odczytuje te same bajty po tym identyfikatorze

  Scenario: usunięcie razem z sesją
    Given nagranie z audio_id powiązanym z session_id
    When workflow usuwania danych sesji kasuje blob
    Then odczyt po audio_id kończy się udokumentowanym błędem „nie ma takiego pliku”

  Scenario: adapter systemu plików
    Given MERITUM_BLOB_PROVIDER=filesystem i katalog wolumenu
    When backend zapisuje nagranie, a worker je odczytuje
    Then oba procesy widzą ten sam plik, a usunięcie kasuje go z dysku

  Scenario: adapter GCS podaje adres gs://
    Given MERITUM_BLOB_PROVIDER=gcs i nazwa bucketu
    When worker prosi o adres nagrania dłuższego niż około minuty
    Then dostaje adres gs:// do odczytu przez Speech-to-Text w trybie batch
