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
  Scenario: adres wewnętrzny
    Given link "http://169.254.169.254/latest/meta-data/"
    When system próbuje pobrać stronę
    Then pobranie jest zablokowane przed połączeniem
    And wynik to "technical_failure" bez szczegółów sieci w komunikacie

  Scenario: przekierowanie na adres prywatny
    Given publiczny adres, który przekierowuje na "http://10.0.0.5/"
    When system pobiera stronę
    Then przekierowanie jest zablokowane

  Scenario: strona za logowaniem
    Given link do posta na Facebooku wymagającego logowania
    When system pobiera stronę
    Then wynik to "technical_failure" z prośbą o wklejenie tekstu

  Scenario Outline: strona blokady antybotowej nie jest treścią
    Given serwis za ochroną antybotową odpowiada stroną blokady <dostawca>
    When system pobiera stronę
    Then wynik to "technical_failure" z powodem "blocked_by_bot_protection"

    Examples:
      | dostawca              |
      | Incapsula z kodem 200 |
      | AWS WAF z kodem 202   |

  Scenario: artykuł z datą publikacji w metadanych
    Given publiczna strona HTML z datą publikacji 2026-11-18 w metadanych
    When fetcher pobiera ją jako link użytkownika
    Then FetchedPage ma published_at 2026-11-18

  Scenario: strona bez daty publikacji
    Given publiczna strona HTML bez daty w metadanych
    When fetcher ją pobiera
    Then FetchedPage ma published_at None

  Scenario: identyfikator w kanale z przeglądarką
    Given żądanie z channel = web i identyfikatorem użytkownika kanału
    When kontrakt waliduje żądanie
    Then walidacja je odrzuca

  Scenario: awaria indeksu fact-checkerów
    Given sprawdzenie zakończone stanem done, a Google Fact Check Tools API zwróciło błąd dostępu
    When worker składa CheckResult
    Then wynik ma kod ograniczenia "fact_check_unavailable", z którego kanał składa komunikat o błędzie dostępu do indeksu
    And stan sprawdzenia nie jest technical_failure

  Scenario: przesłanka z oceny fact-checkera
    Given ClaimResult z werdyktem "fałszywe" i jedyną przesłanką z ClaimReview Demagogu z textualRating "Fałsz", tytułem, datą i linkiem
    When kontrakt waliduje wynik
    Then walidacja go przyjmuje, choć przesłanka nie ma fragmentu strony

  Scenario: dopasowanie tylko po domenie
    Given IncidentMatch z podstawą dopasowania zawierającą tylko domenę i matched_on "content"
    When kontrakt waliduje twierdzenie
    Then walidacja je odrzuca, bo dopasowanie treści wymaga zgodnego tytułu, tematu i daty

  Scenario: twierdzenie bez daty
    Given wynik "done" z twierdzeniem bez claim_date
    When kontrakt waliduje wynik
    Then walidacja go odrzuca

  Scenario: żądanie sprawdzenia niesie session_id
    Given kanał z identyfikatorem sesji przeglądarki
    When wysyła CheckRequest z polem session_id
    Then kontrakt przyjmuje żądanie, a session_id trafia do CheckRecord

  Scenario Outline: wynik sprawdzenia niesie znacznik treści wygenerowanej przez AI
    Given wynik sprawdzenia z uzasadnieniem napisanym przez model "<model>" dostawcy "<provider>"
    When kanał serializuje wynik do odpowiedzi
    Then odpowiedź ma znacznik czytelny maszynowo z informacją, że uzasadnienie wygenerował system AI, i z nazwą modelu

    Examples:
      | provider | model                |
      | vertex   | gemini-2.0-flash-001 |
      | stub     | stub                 |

  Scenario Outline: odrzucone nagranie niesie kod ograniczenia
    Given wynik "out_of_scope" dla nagrania odrzuconego błędem <error>
    When kontrakt waliduje wynik
    Then wynik ma kod ograniczenia "<code>", z którego kanał wybiera tekst w copy/pl.json

    Examples:
      | error                       | code                     |
      | UnsupportedAudioFormatError | audio_format_unsupported |
      | AudioTooLongError           | audio_too_long           |

  Scenario: poza zakresem z powodem
    Given wynik ze stanem "out_of_scope" dla obrazu
    When kontrakt waliduje wynik
    Then wynik ma kod powodu "image", z którego kanał wybiera tekst w copy/pl.json

  Scenario: kod powodu tylko przy out_of_scope
    Given wynik ze stanem "done"
    When kontrakt waliduje wynik
    Then kod powodu jest pusty

  Scenario: kod powodu przy innym stanie
    Given wynik ze stanem "done" z kodem powodu "image"
    When kontrakt waliduje wynik
    Then walidacja go odrzuca

  Scenario: zrzut ekranu z tekstem i datą
    Given zrzut ekranu posta z tekstem i datą "12.11.2026"
    When system zleca OCR
    Then dostaje odczytany tekst i datę jako kandydata na claim_date
    And wynik zaznacza, że data widoczna na obrazie sama nie potwierdza rzeczywistej daty publikacji

  Scenario: brak wyszukiwania wcześniejszych wystąpień
    Given nie skonfigurowano działającego API ani lokalnej bazy obrazów
    When system pyta o wcześniejsze wystąpienia
    Then port zwraca jawny wynik "nie wyszukano", który odpowiedź pokazuje użytkownikowi

  Scenario: awaria OCR
    Given dostawca OCR zwraca błąd po wyczerpaniu ponowień
    When system zleca OCR
    Then port rzuca udokumentowany błąd, który workflow mapuje na "technical_failure"

  Scenario: lista sprawdzeń z okresu do eksportu
    Given CheckRecord ze stanem done i dwoma werdyktami
    When analityk pobiera sprawdzenia z okresu obejmującego ten zapis
    Then lista do eksportu zawiera zapisane sprawdzenie
