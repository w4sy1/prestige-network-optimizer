# Prestige Network Optimizer
PRESTIGE TECH — by Dominik Wasilak — v0.3.4

Pomiar i jawne zmiany DNS lub MTU na Windows z backupem, porównaniem i rollbackiem.

## Instalacja i uruchomienie
Python 3.11+. Skopiuj katalog projektu. Podstawowy CLI używa biblioteki standardowej. PDF wymaga requirements-gui.txt; podpisy, jeśli dostępne, wymagają requirements-signing.txt.
```text
python app.py --help
python app.py --support
python -m unittest discover -s tests -v
```
Szczegóły i przykłady: `docs/USAGE.md`. Zależności systemowe opisano w tym pliku.

## Raporty i logi
Opcja `--output` zapisuje lokalnie JSON, TXT i HTML. Bez niej JSON trafia na stdout.
Log JSONL w `logs/` zawiera czas, moduł, akcję, wynik i typ błędu, bez treści wyjątków.
Kod 1 oznacza błąd, kod 2 oznacza negatywny wynik weryfikacji lub niekompletne dane,
jeżeli dane polecenie zwraca takie rozstrzygnięcie. `--dry-run` pokazuje plan bez wykonania.

## Bezpieczeństwo i ograniczenia
Narzędzie przeznaczone do celów edukacyjnych, diagnostycznych oraz do pracy z systemami i sieciami, których właścicielem jest użytkownik lub na których testowanie posiada zgodę.
Dane pozostają lokalne. Polecenia sieciowe wymagają świadomego wywołania;
zapytania DNS i połączenia do wskazanych hostów ujawniają im adres klienta.
Brak uprawnień lub backendu jest błędem, nie pozytywnym wynikiem audytu.
Zakres MVP i ograniczenia platformowe opisano w `docs/USAGE.md`.

## Autor i licencja
Dominik Wasilak, Prestige Tech, prestigetech@gmail.com. Licencja: `Prestige Tech Free Use License` - szczegóły w `LICENSE`.

## Wesprzyj autora
Opcja wsparcia autora zostanie udostępniona w przyszłości.
Linki w `config/author.json`.

## GUI i EXE 0.3.1

Uruchom `python gui.py` albo samodzielny EXE. W EXE interpreter, PDF i potrzebne
biblioteki Python są dołączone. Zewnętrzne backendy systemowe pozostają wymagane.
Budowa: [docs/BUILD.md](docs/BUILD.md). Obsługa: [docs/GUI.md](docs/GUI.md).
Ograniczenia bufora i testów: [docs/DESKTOP-STATUS.md](docs/DESKTOP-STATUS.md).
Własny kod jest objęty Prestige Tech Free Use License. Licencje zależności pozostają bez zmian: THIRD_PARTY_NOTICES.txt.

## Poprawki rollbacku 0.3.4

Rollback nie powtarza przywróconych ustawień ani nie nadpisuje późniejszego trybu automatycznego DNS.

Szczegóły: [docs/RECOVERY.md](docs/RECOVERY.md).
