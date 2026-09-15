# Samodzielny EXE dla Windows

W katalogu tego repozytorium, z Pythonem 3.11 lub nowszym:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-build.txt
.venv/Scripts/python.exe build_exe.py
```

Wynik znajduje się w `dist/`. Interpreter Python i generator PDF są zawarte
w EXE. Zewnętrzne narzędzia systemowe potrzebne przez wybrane operacje
(np. PowerShell 7, ADB, Nmap) trzeba zainstalować oddzielnie.
Funkcje Termuxa wymagają Androida i Termuxa.

Program zapisuje dane w `%LOCALAPPDATA%/PrestigeTech/<nazwa-programu>`.
Przełącznik `--backend` uruchamia CLI. `--smoke` sprawdza konstrukcję okna.
Plik nie jest podpisany certyfikatem Authenticode.
Własny kod ma licencję MIT; licencje zależności znajdują się w
`THIRD_PARTY_NOTICES.txt` i `assets/FONT-LICENSE.txt`.

Workflow Tests uruchamia testy na Windows z Pythonem 3.11 i 3.14.
Dodanie konfiguracji nie oznacza wykonania jej na serwerze GitHub.
