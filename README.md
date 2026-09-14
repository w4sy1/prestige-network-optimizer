# Prestige Network Optimizer
PRESTIGE TECH — by Dominik Wasilak — v0.2.0

Pomiar i jawne zmiany DNS lub MTU na Windows z backupem, porównaniem i rollbackiem.

## Instalacja i uruchomienie
Python 3.11+. Skopiuj katalog projektu. Bez instalowania pakietów pip.
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
Dominik Wasilak, Prestige Tech, prestigetech@gmail.com. Licencja MIT: `LICENSE`.

## Wesprzyj autora
Opcja wsparcia autora zostanie udostępniona w przyszłości.
Linki w `config/author.json`.
