Feature: Przebieg ewaluacji
  Worker zapisuje EvalRun, backend go czyta, strona ewaluacji go pokazuje (US-OBS-06, ADR-28).

  Scenario: przebieg z miernikami i wynikami przypadków
    Given przebieg na golden secie z przypiętym corpus_version
    When worker zapisuje EvalRun
    Then EvalRun ma zestaw, datę, corpus_version, stan, mierniki i wynik każdego przypadku
    And mierniki obejmują macro-F1, pokrycie i poprawność cytowań, wstrzymanie, odporność, medianę i maksimum czasu, koszt 100 testów, spójność kanałów i pętlę informacji

  Scenario: stan niebędący werdyktem w wyniku przypadku
    Given przypadek, którego sprawdzenie skończyło się stanem "technical_failure"
    When worker zapisuje wynik przypadku
    Then wynik ma ten stan jako osobną klasę błędu i czas z CheckRecord, a walidacja go przyjmuje

  Scenario: powiadomienie o końcu przebiegu
    Given analityk uruchomił przebieg
    When przebieg się kończy
    Then Notification ma rodzaj "eval_run_done", user_id analityka i link do przebiegu
