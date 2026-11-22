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

  Scenario: zgłoszenie błędu bez uzasadnienia
    Given EscalateClaimInput z powodem "user_dispute" i bez justification_masked
    When kontrakt go waliduje
    Then walidacja przechodzi
    And uzasadnienie przy powodzie innym niż "user_dispute" nadal jest odrzucane

  Scenario: wejście workflowu sprawdzania z cudzym session_id w żądaniu
    Given CheckRequest z kanału web z session_id "session-1"
    When backend buduje wejście sprawdzania z innym session_id "session-2"
    Then walidacja odrzuca wejście

  Scenario: wejście przebiegu ewaluacji wskazuje wgrany zestaw w magazynie plików
    Given EvalRunInput z pliku użytkownika z dataset_blob_id wskazującym zestaw
    When kontrakt waliduje wejście przebiegu
    Then wejście przebiegu jest poprawne i niesie identyfikator zestawu
    And to samo wejście bez dataset_blob_id też jest poprawne
    And dataset_blob_id przy zestawie złotym jest odrzucane
