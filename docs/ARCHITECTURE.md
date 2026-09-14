# Architektura

`app.py`: CLI i logika domenowa. `runtime.py`: lokalne I/O, raporty, logowanie, backendy. `config/`: autor. `tests/`: unittest. `reports/`, `logs/`: lokalne wyniki. Projekt działa po skopiowaniu samodzielnego katalogu; nie importuje sąsiadujących projektów.

Zależności: Python 3.11+ i backendy wskazane w README. Brak pip dependencies.
