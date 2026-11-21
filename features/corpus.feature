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
