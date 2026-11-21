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
