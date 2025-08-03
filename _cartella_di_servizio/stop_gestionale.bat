@echo off
TITLE Stop GestionaleDjango Server
ECHO Fermo il server dell'applicazione GestionaleDjango...

:: Trova il Process ID (PID) di waitress che esegue la nostra app e lo termina
FOR /F "tokens=2" %%i IN ('tasklist /V /FI "IMAGENAME eq waitress-serve.exe" /FI "WINDOWTITLE eq GestionaleDjango Server" /FO CSV /NH') DO (
    taskkill /F /PID %%i
)

ECHO Server fermato.
PAUSE