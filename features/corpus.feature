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
