Feature: Usunięcie danych osoby
  Eraser usuwa sprawdzenia osoby i powiadomienia o nich, a zostawia jej powiadomienia
  o sprawach moderatora i systemowe (US-BEZ-05, decyzja z 22.11).

  Scenario: usunięcie historii zostawia powiadomienia o sprawach i systemowe
    Given użytkownik ma powiadomienie check_done o swoim sprawdzeniu, case_assigned o sprawie #S-1 i system
    When eraser usuwa dane tego użytkownika
    Then zostają tylko powiadomienia case_assigned i system
