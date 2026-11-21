Feature: Sprawdzanie treści
  Kanały wysyłają do rdzenia jedno zgłoszenie, niezależnie od kanału.

  Scenario: zgłoszenie z samym tekstem jest przyjęte
    Given tekst "Polska przyjęła euro w 2024 roku." wysłany przez kanał "web"
    When kanał buduje zgłoszenie sprawdzenia
    Then zgłoszenie jest przyjęte z tym tekstem

  Scenario: import kontraktów się nie zmienia
    Given kod backendu, workera i testy importują "from meritum_core.checks.contracts import CheckResult"
    When kontrakty są pakietem "checks/contracts/" z prywatnymi modułami
    Then każdy dotychczasowy import działa bez zmian
    And wygenerowane "contracts/meritum.schema.json" i "contracts/meritum.ts" są identyczne jak przed zmianą

  Scenario: zapis i odczyt przebiegu
    Given CheckRecord ze stanem done i dwoma werdyktami
    When worker zapisuje go przez repozytorium, a backend czyta po check_id
    Then backend dostaje ten sam CheckRecord, z question_masked i bez surowego tekstu

  Scenario: usunięcie po identyfikatorze sesji
    Given trzy zapisy z session_id "s_12345678" i jedna sprawa z ich twierdzeniami
    When repozytorium usuwa dane tej sesji
    Then zapisy znikają, a sprawa traci tylko ich check_ids

  Scenario: nagranie OGG z Opus
    Given nagranie głosowe OGG z Opus 48 kHz o długości 40 s
    When system zleca transkrypcję
    Then dostaje tekst transkrypcji w języku pl-PL

  Scenario: nieobsługiwany format
    Given plik "nagranie.xyz"
    When system zleca transkrypcję
    Then port rzuca błąd nieobsługiwanego formatu, który workflow mapuje na "out_of_scope"

  Scenario: awaria dostawcy
    Given Speech-to-Text v2 zwraca błąd po wyczerpaniu ponowień
    When system zleca transkrypcję
    Then port rzuca błąd dostawcy, który workflow mapuje na "technical_failure"
