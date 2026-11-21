Feature: Sprawdzanie treści
  Kanały wysyłają do rdzenia jedno zgłoszenie, niezależnie od kanału.

  Scenario: zgłoszenie z samym tekstem jest przyjęte
    Given tekst "Polska przyjęła euro w 2024 roku." wysłany przez kanał "web"
    When kanał buduje zgłoszenie sprawdzenia
    Then zgłoszenie jest przyjęte z tym tekstem
