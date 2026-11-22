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

  Scenario: dowód starszy niż 365 dni od daty twierdzenia
    Given twierdzenie z claim_date 2026-11-01 pochodzącą z tekstu
    And najnowszy zgodny dowód opublikowany 2025-09-01
    When system liczy siłę
    Then siła to "słaba" z przesłanką "dowód nieaktualny"

  Scenario: obowiązujący akt prawny nie jest nieaktualny
    Given cytat z pozycji katalogu ISAP o ważności "in_force" sprzed 5 lat
    When system liczy wiek dowodu
    Then cytat nie jest oznaczony jako nieaktualny

  Scenario: dowód zastąpiony nowszym
    Given starszy dowód wspierający i nowszy urzędowy dowód obalający od tego samego wydawcy i serii
    When system ustala werdykt
    Then starszy dowód ma ważność "superseded" i nie liczy się do siły ani rozbieżności
    And werdykt to "fałszywe" albo "wprowadzające w błąd" z techniką "outdated", nigdy "brak wystarczających dowodów"

  Scenario: werdykt z oceny Demagogu (scenariusz G)
    Given twierdzenie "Wrocław był jedynym miastem w Polsce, w którym 65-latkowie jeździli komunikacją miejską za darmo"
    And ClaimReview od Demagogu z textualRating "Fałsz", tytułem, datą i linkiem
    When system liczy werdykt i przesłanki
    Then werdykt to "fałszywe" z przesłanką z oceną "Fałsz", tytułem, datą i linkiem do Demagogu, bez fragmentu strony
    And siła liczy Demagoga jako jednego niezależnego wydawcę wtórnego, więc sama nie jest "mocna"

  Scenario: ocena spoza tabeli mapowania
    Given ClaimReview z textualRating, którego nie ma w tabeli mapowania ocen
    When system liczy werdykt
    Then ocena zostaje kontekstem z linkiem i nie jest przesłanką

  Scenario: dosłowny tekst oceny
    Given ClaimReview z textualRating "Częściowa prawda"
    When kanał pokazuje przesłankę
    Then ocena ma dokładnie brzmienie "Częściowa prawda", a nie parafrazę modelu
