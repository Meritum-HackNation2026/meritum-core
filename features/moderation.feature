Feature: Role personelu nadane przez administratora
  Backend nadaje i odbiera role panelu przez port StaffRepository z core;
  role leżą w tej samej bazie co reszta tabel aplikacji, więc przeżywają restart API.

  Scenario: rola nadana przez administratora przeżywa restart
    Given administrator nadał adresowi "ola@example.com" rolę "moderator"
    When API startuje ponownie z tą samą bazą
    Then repozytorium kont personelu nadal zwraca dla tego adresu rolę "moderator"

  Scenario: odebranie roli
    Given adres "ola@example.com" z rolą "analyst"
    When administrator odbiera mu rolę
    Then repozytorium nie zwraca dla tego adresu żadnej roli
