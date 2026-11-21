Feature: Cytaty ze źródeł
  Cytat trafia do odpowiedzi tylko wtedy, gdy fragment występuje dosłownie w tekście
  źródła (US-ZRD-01, F-16, ADR-06).

  Scenario: cytat z drobną różnicą białych znaków i cudzysłowów
    Given źródło zawiera tekst „Ostrzeżenie  II stopnia obowiązuje do 18:00”
    When model zwraca cytat "Ostrzeżenie II stopnia obowiązuje do 18:00"
    Then cytat przechodzi weryfikację

  Scenario: cytat zmyślony przez model
    Given źródło nie zawiera zdania "Szkoły są zamknięte do odwołania"
    When model zwraca ten cytat
    Then cytat nie trafia do odpowiedzi
    And twierdzenie bez innego cytatu traci werdykt rozstrzygający
