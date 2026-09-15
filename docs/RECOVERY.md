# Rollback po błędzie pomiaru

Backup powstaje przed zmianą. Jeśli pomiar po zmianie zawiedzie, dziennik
zachowuje oryginalną konfigurację i status APPLIED; można zażądać rollbacku.
Sam błąd pomiaru nie uruchamia kolejnej zmiany ustawień.

Jeśli pierwotne ustawienia już obowiązują, rollback zwraca already_restored
i nie powtarza polecenia. Jeżeli użytkownik później przełączył DNS na tryb
automatyczny, rollback nie zastępuje tej zmiany konfiguracją ze starego planu.

Przypadki sprawdzono z podstawionym backendem — bez zmiany sieci komputera.
