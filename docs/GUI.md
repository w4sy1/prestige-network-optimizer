# Interfejs graficzny

Uruchom `python gui.py`. Najpierw zainstaluj `requirements-gui.txt`, jeśli chcesz eksport PDF.
Formularz udostępnia parametry programu. Operacje zapisujące wymagają zaznaczenia odpowiedniej opcji wykonania.
Zewnętrzne backendy (PowerShell, ADB, Nmap, Termux) pozostają wymagane dla odpowiednich funkcji.
Przycisk PDF eksportuje wynik; `python pdf_export.py --input raport.json --pdf raport.pdf` tworzy raport z JSON.
Wydanie EXE zawiera interpreter i biblioteki Python, ale nie zastępuje systemów Android/Termux.
