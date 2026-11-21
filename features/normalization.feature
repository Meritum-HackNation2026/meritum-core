Feature: Klucz pamięci wyników
  To samo wejście daje ten sam klucz w każdym kanale (US-WTY-03, ADR-19).

  Scenario: ten sam post z dwóch kanałów
    Given tekst z formularza "Od jutra  „zakaz” wjazdu do Warszawy"
    And tekst z wtyczki "Od jutra \"zakaz\" wjazdu do Warszawy https://x.com/a/status/1"
    When system normalizuje oba wejścia
    Then oba dają ten sam klucz pamięci wyników
    And adres posta jest zapisany osobno jako kontekst
