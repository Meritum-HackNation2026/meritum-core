Feature: Model językowy za portem LlmPort
  Workflow woła model tylko przez LlmPort; dostawcę wybiera konfiguracja MERITUM_LLM_*.

  Scenario: stub bez kluczy
    Given MERITUM_LLM_PROVIDER=stub i brak kluczy dostawcy
    When workflow prosi model o strukturalną odpowiedź typu ClaimList
    Then dostaje poprawny obiekt ClaimList z danych stubu, bez wywołań sieci

  Scenario: Vertex AI wybrany konfiguracją
    Given MERITUM_LLM_PROVIDER=vertex, region UE i przypięta wersja modelu w konfiguracji
    When fabryka buduje adapter
    Then adapter używa temperatury 0 i przypiętej wersji modelu
    And zwraca dostawcę, model, region i zużycie tokenów do zapisu w ModelUsage
