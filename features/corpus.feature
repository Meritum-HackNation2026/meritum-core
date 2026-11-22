Feature: Wyszukiwanie w korpusie
  Agenty badawcze i narzędzie search_sources szukają fragmentów przez CorpusSearchPort,
  zawsze w przypiętej migawce korpusu.

  Scenario: odmiana polska znajduje dokument
    Given w korpusie jest fragment "Ostrzeżenia meteorologiczne dla województwa mazowieckiego"
    When system szuka "ostrzeżenie meteorologiczne Mazowsze"
    Then fragment jest w pierwszych 5 wynikach

  Scenario: świeższy dokument wyżej przy podobnym dopasowaniu
    Given dwa fragmenty o podobnym dopasowaniu, opublikowane 3 dni i 400 dni przed datą twierdzenia
    When system szuka dla tego twierdzenia
    Then świeższy fragment jest wyżej

  Scenario: korpus ma tylko embeddingi policzone w UE
    Given korpus po ponownym przeliczeniu
    When sprawdzam metadane przebiegów embeddingów i logi Vertex AI
    Then każdy wektor pochodzi z regionu UE wybranego modelu, a wektory z us-central1 są usunięte

  Scenario: reranker skraca listę fragmentów
    Given 20 fragmentów z wyszukiwania hybrydowego dla jednego twierdzenia
    When przechodzą przez reranker
    Then do oceny wymowy trafia najwyżej tyle fragmentów, ile mówi stała, w kolejności trafności

  Scenario: bramka pusta
    Given brak konfiguracji rerankera
    When fragmenty przechodzą przez bramkę
    Then kolejność z wyszukiwania hybrydowego zostaje, a log zapisuje pominięcie

  Scenario: wykluczenie bez powodu nie przechodzi
    Given pozycja katalogu z excluded = true i pustym exclusion_reason
    When katalog jest walidowany
    Then walidacja kończy się błędem wskazującym tę pozycję

  Scenario: źródło wtórne z zastrzeżeniem TDM wypada
    Given źródło wtórne (tier secondary) z zastrzeżeniem eksploracji tekstów i danych w robots.txt albo Content-Signal
    When kurator uruchamia kontrolę katalogu
    Then pozycja ma tdm_reservation = reserved, excluded = true i exclusion_reason z powodem
    And walidacja CatalogEntry odrzuca taką pozycję bez wykluczenia

  Scenario: wynik spoza katalogu odpada
    Given katalog z domenami gov.pl i imgw.pl
    And dostawca zwraca adresy z gov.pl i z example.com
    When system wyszukuje frazę "ostrzeżenie przed burzami"
    Then port zwraca tylko adres z gov.pl jako kandydata do pobrania
    And adres z example.com nie jest pobierany ani cytowany

  Scenario: przekroczony limit czasu
    Given dostawca nie odpowiada przez 10 s
    When system czeka na wynik wyszukiwania
    Then port rzuca udokumentowany błąd przekroczenia czasu, który workflow mapuje na "technical_failure"

  Scenario: stub bez kluczy
    Given MERITUM_WEB_SEARCH_PROVIDER=stub
    When system wyszukuje dowolną frazę
    Then port zwraca kandydatów z fixture, bez wywołań sieci

  Scenario: zapas wybrany konfiguracją
    Given MERITUM_WEB_SEARCH_PROVIDER=searxng i adres instancji SearXNG
    When fabryka buduje adapter i system szuka w sieci "ostrzeżenie przed burzami"
    Then zapytanie jest ograniczone do domen katalogu, a wynik spoza katalogu odpada w naszym filtrze

  Scenario: Linkup bez klucza
    Given MERITUM_WEB_SEARCH_PROVIDER=linkup bez klucza albo z wyłączonym wyłącznikiem
    When fabryka buduje adapter wyszukiwania
    Then zgłasza błąd konfiguracji, który test gotowości wymienia z nazwy zmiennej

  Scenario: dokument z kanału RSS zapisuje drogę pozyskania
    Given migracja corpus 0007_documents_via.sql
    When sprawdzam kolumnę via w corpus.documents
    Then dopuszcza dokładnie wartości SourceVia, w tym "rss", a dokumenty sprzed migracji mają via = "corpus"

  Scenario: dokument aktu prawnego ma metadane aktu w korpusie
    Given akt DU/2024/1362 z ELI z in_force_until 2025-12-31
    When ingest zapisuje dokument w corpus.documents
    Then wiersz dokumentu ma eli "DU/2024/1362", document_type "Rozporządzenie" i in_force_until 2025-12-31
    And dokument strony spoza ELI ma te pola puste
