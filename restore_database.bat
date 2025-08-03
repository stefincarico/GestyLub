@echo off
TITLE Ripristino Database GestionaleDjango

:: =================================================================
:: == Script di ripristino del database GestionaleDjango          ==
:: == ATTENZIONE: QUESTA OPERAZIONE CANCELLA TUTTI I DATI ATTUALI! ==
:: =================================================================

:: --- 1. CONTROLLO E RICHIESTA PERMESSI DI AMMINISTRATORE ---
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
IF '%ERRORLEVEL%' NEQ '0' (
    ECHO Richiedo i permessi di Amministratore...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    EXIT
)
CD /D "%~dp0"
CLS

:: --- 2. IMPOSTAZIONI E CONFERMA ---
SET DB_NAME=gestilub_db
SET DB_USER=postgres

ECHO ATTENZIONE! Stai per CANCELLARE e SOVRASCRIVERE il database '%DB_NAME%'.
ECHO Tutti i dati inseriti dopo l'ultimo backup verranno persi.
ECHO.
SET /p AREYOUSURE=Sei assolutamente sicuro di voler continuare? (S/N): 
IF /I "%AREYOUSURE%" NEQ "S" (
    ECHO Operazione annullata.
    PAUSE
    EXIT
)

ECHO.
SET /p BACKUP_FILE=Inserisci il percorso completo del file di backup (.sql): 
IF NOT EXIST "%BACKUP_FILE%" (
    ECHO [ERRORE] File non trovato: %BACKUP_FILE%
    PAUSE
    EXIT
)

ECHO.
ECHO Procedo con il ripristino da: %BACKUP_FILE%
ECHO.
ECHO --- FERMO IL SERVER DELL'APPLICAZIONE (se in esecuzione) ---
taskkill /IM waitress-serve.exe /F > nul 2> nul

ECHO.
ECHO --- INIZIO PROCEDURA DI RIPRISTINO DATABASE ---

:: Imposta la password di postgres per i comandi
SET /p PGPASSWORD=Inserisci la password dell'utente PostgreSQL '%DB_USER%': 

ECHO.
ECHO 1/3 - Cancellazione del database esistente...
dropdb -U %DB_USER% -h localhost %DB_NAME% --if-exists
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERRORE] Impossibile cancellare il database.
    PAUSE
    EXIT
)
ECHO   [OK] Database cancellato.

ECHO.
ECHO 2/3 - Creazione del database vuoto...
createdb -U %DB_USER% -h localhost %DB_NAME%
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERRORE] Impossibile creare il database.
    PAUSE
    EXIT
)
ECHO   [OK] Database vuoto creato.

ECHO.
ECHO 3/3 - Ripristino dei dati dal file di backup...
ECHO Questa operazione potrebbe richiedere alcuni minuti.
psql -U %DB_USER% -h localhost -d %DB_NAME% -f "%BACKUP_FILE%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERRORE] Si e' verificato un errore durante il ripristino.
    PAUSE
    EXIT
)
ECHO   [OK] Ripristino completato con successo!

ECHO.
ECHO --- PROCEDURA DI RIPRISTINO TERMINATA ---
ECHO Puoi ora riavviare il gestionale con lo script 'start_gestionale.bat'.
ECHO.
PAUSE