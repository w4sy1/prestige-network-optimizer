# Desktop 0.3.1 — wydanie testowe

GUI zachowuje ostatnie 65536 znaków wyniku. Po skróceniu informuje o tym
w pasku stanu. TXT i PDF zapisane z okna obejmują ten bufor; pełny raport
zapisz opcją wyjściową backendu. Długie wiersze przewijaj poziomo.
Przerwanie zatrzymuje uruchomiony proces i jego dzieci na Windows.
Po przerwaniu zapisu sprawdź dziennik oraz backup przed kolejną operacją.

Wersja zawiera lokalne testy automatyczne. Nie oznacza potwierdzenia operacji
administracyjnych, fizycznych urządzeń Android ani wszystkich sterowników.
Zewnętrzne AI wymaga własnego dostępnego konta API; ostatnia próba miała HTTP 429.
