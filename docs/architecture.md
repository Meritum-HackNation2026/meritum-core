# Architektura i jej strażnicy

Zasady są w skillu `meritum-architecture` w monorepo (`.claude/skills/meritum-architecture/SKILL.md`). Tu jest tylko to, co je egzekwuje w tym repo. Wszystkie kontrole działają lokalnie i w CI (`.github/workflows/ci.yml`, job `lint` i `tests`).

| Zasada | Kontrola |
| --- | --- |
| pionowe wycinki, prywatne `_nazwy` | `tests/architecture/test_slices.py` (pytestarch: wycinek importuje inny tylko przez jego pakiet, prywatny moduł `_x` tylko we własnym pakiecie); `scripts/check_conventions.py` (import prywatnej nazwy albo modułu innego pakietu; pakiet z modułami `_x` deklaruje `__all__`) |
| heksagonalna | `tests/architecture/test_hexagonal.py` (pytestarch: kod domeny nie importuje adapterów ani frameworków: DBOS, FastAPI, psycopg...); co jest adapterem lub fabryką, mówi `WIRING` w `tests/architecture/conftest.py` (także port techniczny w `shared/<pojęcie>/`); `test_hexagonal.py` sprawdza też, że adaptery `shared.llm` buduje tylko `shared.llm.factory` |
| lintery na pełną moc | ruff `select = ["ALL"]` z `preview`, wyłączone tylko reguły sprzeczne z formatterem i konwencją Google; `ty` z `all = "error"` |
| docstringi z funkcjami produktu | ruff `D` i `DOC` (Args, Returns, Raises); `scripts/check_conventions.py`: publiczna klasa i funkcja najwyższego poziomu w `src/` ma sekcję `Features:` z ID `US-XXX-00`, `F-00`, `ADR-00` albo `none (infrastructure)`, każdy parametr jest w `Args:` (parametry `__init__` w docstringu klasy), każde pole klasy w `Attributes:` |
| najwyżej 250 linii na plik | `scripts/check_conventions.py` (`src/`, `tests/`, `scripts/`, `features/`) |
| stałe | `scripts/check_conventions.py`: stała `UPPER_CASE` na poziomie modułu tylko w `constants.py`, z adnotacją `Final` i docstringiem atrybutu zaraz pod nią |
| typy | ruff `ANN`, `ty` strict |
| złożoność | ruff `C901` (`max-complexity = 10`) i `PLR09xx` (limity w `[tool.ruff.lint.pylint]`, najwyżej 3 części warunku i 3 poziomy zagnieżdżenia) |
| martwy kod | `vulture` (ścieżki w `[tool.vulture]`; nazwy używane tylko przez frameworki albo inne repo w `vulture_whitelist.py`) |
| bezpieczeństwo | ruff `S` (reguły bandita) i sam `bandit` (`[tool.bandit]`); bandit to linter bezpieczeństwa, nie szuka martwego kodu |

## Wyjątki

Wąsko i zawsze z powodem: `# noqa: XXX  # powód` w linii, per-file ignore w `[tool.ruff.lint.per-file-ignores]` z komentarzem, a dla `scripts/check_conventions.py` wpis `ścieżka = "powód"` w `[tool.meritum-conventions.*-exceptions]` w `pyproject.toml`.

Obecne wyjątki:

- `src/meritum_core/checks/contracts.py`: limit linii, sekcje `Features:`/`Attributes:` i `constants.py` (861 linii po kontraktach v3; podział na pakiet `checks/contracts/` i stałe w `checks/constants.py` w zgłoszeniu core/001), vulture (pola kontraktów czyta JSON i inne repo), ruff `too-many-boolean-expressions` (warunek wejścia `CheckRequest` z v3, do nazwanych warunków przy podziale);
- `tests/test_checks_contracts.py`: limit linii (dzielony razem z modułem);
- `src/meritum_core/jobs/contracts/_workflows.py`: stałe poza `constants.py`, bo specyfikacje workflowów (`PING`, `CHECK`…) i `WORKFLOWS` powstają z modeli kontraktu (osobny `constants.py` dałby cykl importów).
- `features/steps/`: ty `not-callable` i `dynamic-function-decorator-return` (behave podmienia `given`/`when`/`then` na prawdziwe dekoratory dopiero przy ładowaniu kroków), vulture `ignore_decorators` dla tych dekoratorów (kroki woła behave), ruff `assert` (kroki sprawdzają jak testy).
