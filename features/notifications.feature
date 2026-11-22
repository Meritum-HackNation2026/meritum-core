Feature: Powiadomienia
  Powiadomienie niesie kody i identyfikatory; tekst składa aplikacja z copy/pl.json (ADR-29).

  Scenario: postęp sprawdzenia w powiadomieniu
    Given workflow sprawdzania kończy krok "search_corpus"
    When powstaje Notification z kind "check_progress"
    Then powiadomienie niesie kod kroku "search_corpus", a aplikacja pokazuje tekst kroku z copy/pl.json

  Scenario: komunikat systemowy
    Given zespół wysyła informację systemową "maintenance_planned"
    When powstaje Notification z kind "system"
    Then powiadomienie niesie kod komunikatu "maintenance_planned" z copy/pl.json, nie wolny tekst

  Scenario: postęp bez kodu kroku
    Given workflow sprawdzania nie podaje kodu kroku
    When powstaje Notification z kind "check_progress"
    Then walidacja go odrzuca
