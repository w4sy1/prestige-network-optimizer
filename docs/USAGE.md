# Użycie

`python app.py inspect --interface 12`
`python app.py dns --interface 12 --server 1.1.1.1` — plan.
`python app.py dns --interface 12 --server 1.1.1.1 --backup dns-before.json --apply`
`python app.py mtu --interface 12 --value 1400 --backup mtu-before.json --apply`
`python app.py rollback --backup dns-before.json --apply`

Windows + PowerShell + administrator dla zmian. Nie podnosi uprawnień samodzielnie.
Backup zapisuje poprzedni DNS i informację, czy był automatyczny, albo poprzednie MTU.
Rollback sprawdza, czy ustawienie nie zostało zmienione przez inną osobę.
MVP nie modyfikuje TCP, oszczędzania energii NIC ani IPv6; pokazuje TCP i link speed.
Zmiana DNS może niekorzystnie wpłynąć na domenę firmową/VPN. Program nie zgaduje lepszego DNS.
TEST BEFORE/AFTER wysyła zapytania example.com po świadomym --apply, obejmuje cache.
Dla MTU ten pomiar nie ocenia poprawnie przepustowości/fragmentacji; MTU najpierw zmierz
w Internet Diagnostic. Po pogorszeniu raport rekomenduje rollback, nie wykonuje go sam.
