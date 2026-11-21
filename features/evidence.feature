Feature: Cytaty ze źródeł i siła dowodów
  Cytat trafia do odpowiedzi tylko wtedy, gdy fragment występuje dosłownie w tekście
  źródła (US-ZRD-01, F-16, ADR-06). Siła i zgodność wynikają z jednej reguły liczonej na
  cytatach z oceną wymowy, nie z deklaracji modelu (US-ZRD-03, US-ZRD-04, F-15, ADR-05).

  Scenario: cytat z drobną różnicą białych znaków i cudzysłowów
    Given źródło zawiera tekst „Ostrzeżenie  II stopnia obowiązuje do 18:00”
    When model zwraca cytat "Ostrzeżenie II stopnia obowiązuje do 18:00"
    Then cytat przechodzi weryfikację

  Scenario: cytat zmyślony przez model
    Given źródło nie zawiera zdania "Szkoły są zamknięte do odwołania"
    When model zwraca ten cytat
    Then cytat nie trafia do odpowiedzi
    And twierdzenie bez innego cytatu traci werdykt rozstrzygający

  Scenario: mocna podstawa przy dwóch niezależnych wydawcach, w tym urzędowym
    Given twierdzenie z werdyktem "potwierdzone"
    And cytaty wspierające od dwóch różnych publisher_id, w tym jednego urzędowego, oba świeże
    When system liczy przesłanki i siłę
    Then siła to "mocna"

  Scenario: dwie strony tego samego ministerstwa to jedno źródło
    Given dwa cytaty wspierające z różnych stron, ale z tym samym publisher_id
    When system liczy niezależnych wydawców
    Then liczba niezależnych wydawców wynosi 1

  Scenario: sprzeczne wiarygodne źródła
    Given ważne w dacie twierdzenia cytaty wspierające i obalające od różnych wydawców
    When system ustala werdykt
    Then werdykt to "brak wystarczających dowodów" bez poziomu siły
    And wynik zawiera cytaty obu stron i notatkę, czym się różnią

  Scenario: brak źródła urzędowego
    Given werdykt "confirmed" z siłą "moderate" i dwoma zgodnymi wydawcami wtórnymi
    When system liczy, co zmieniłoby werdykt
    Then wynik ma kod "needs_primary_source"

  Scenario: sprzeczne źródła
    Given werdykt "insufficient_evidence" ze sprzecznymi cytatami
    When system liczy, co zmieniłoby werdykt
    Then wynik ma kod mówiący, że rozstrzygnąłby nowszy dowód urzędowy, i żadnego faktu spoza wyniku
