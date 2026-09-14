# Użycie

`python app.py inspect --interface 12`
`python app.py dns --interface 12 --server 1.1.1.1` — plan.
`python app.py dns --interface 12 --server 1.1.1.1 --backup dns-before.json --apply`
`python app.py mtu --interface 12 --value 1400 --probe-target 192.168.1.1 --backup mtu-before.json --apply`
`python app.py rollback --backup dns-before.json --apply`

Windows + PowerShell + administrator dla zmian. Nie podnosi uprawnień samodzielnie.
Backup zapisuje poprzedni DNS i informację, czy był automatyczny, albo poprzednie MTU.
Rollback sprawdza, czy ustawienie nie zostało zmienione przez inną osobę.
MVP nie modyfikuje TCP, oszczędzania energii NIC ani IPv6; pokazuje TCP i link speed.
Zmiana DNS może niekorzystnie wpłynąć na domenę firmową/VPN. Program nie zgaduje lepszego DNS.
TEST BEFORE/AFTER wysyła zapytania example.com po świadomym --apply, obejmuje cache.
Dla MTU wykonywane są sondy DF opisane niżej; MTU można wcześniej oszacować
w Internet Diagnostic. Po pogorszeniu raport rekomenduje rollback, nie wykonuje go sam.

## Rozszerzenia 0.2.0

Zmiana MTU wymaga `--probe-target 192.168.1.1`. TEST BEFORE/AFTER wysyła po 10 ICMP
z payloadem odpowiednio stare MTU-28 i nowe MTU-28, z zakazem fragmentacji.
RTT i liczba odpowiedzi nie są pomiarem przepustowości. Routing jest systemowy; upewnij się,
że cel przebiega przez wybrany interfejs. Brak ICMP nie dowodzi awarii sieci.
`inspect` pokazuje TCP, oszczędzanie energii NIC, link speed, IPv4/IPv6, binding i licznik
cache DNS. Dostępność informacji zależy od sterownika — UNKNOWN nie oznacza problemu.
Zmiany TCP/NIC/wyłączenie IPv6 nie są proponowane bez powtarzalnego uzasadnienia pomiarowego.
