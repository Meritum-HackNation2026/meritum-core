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
