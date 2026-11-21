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

  Scenario Outline: model wybierany konfiguracją
    Given MERITUM_LLM_PROVIDER=<dostawca>, MERITUM_LLM_MODEL=<model> i MERITUM_LLM_REASONING=<rozumowanie> ustawione
    When workflow woła LlmPort o ustrukturyzowaną odpowiedź
    Then odpowiada wybrany model z wybranym poziomem rozumowania
    And CheckRecord zapisuje dostawcę, model, region i koszt

    Examples:
      | dostawca   | model                      | rozumowanie |
      | openrouter | anthropic/claude-haiku-5.5 | high        |
      | vertex     | gemini-3.5-flash           | high        |
      | openrouter | openai/gpt-6.1-terra       | low         |
      | openrouter | stepfun/step-3.7-flash     | medium      |
