Feature: Kontrakt zadań
  Backend zleca workerowi workflowy przez JobQueue i czyta ich postęp strumieniem.

  Scenario: wejście workflowu sprawdzania nie ma surowych danych
    Given CheckRequest z kanału discord z identyfikatorem użytkownika kanału
    When backend buduje wejście workflowu "check"
    Then wejście ma zamaskowany tekst, session_id i channel_user_hash, a surowego identyfikatora nie ma w żadnym polu

  Scenario: postęp czytany strumieniem
    Given workflow "check" publikuje trzy kolejne AnalysisStatus
    When backend czyta strumień przez JobQueue
    Then dostaje je w tej kolejności, a ostatni ma pole result
