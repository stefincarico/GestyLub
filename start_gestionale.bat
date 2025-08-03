@echo off
TITLE GestionaleDjango - SERVER IN ESECUZIONE (NON CHIUDERE QUESTA FINESTRA)

:: =================================================================
:: == Script di avvio per GestionaleDjango                          ==
:: =================================================================

:: --- 1. CONTROLLO E RICHIESTA PERMESSI DI AMMINISTRATORE ---
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
IF '%ERRORLEVEL%' NEQ '0' (
    ECHO **************************************************************
    ECHO *          Richiedo i permessi di Amministratore...          *
    ECHO *          PREMI 'Si' Quando ti sara' richiesto              *
    ECHO **************************************************************
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    EXIT
)
CD /D "%~dp0"
CLS

:: --- 2. MESSAGGIO DI BENVENUTO ---
ECHO.
ECHO =================================================
ECHO  AVVIO SERVER GESTIONALEDJANGO
ECHO =================================================
ECHO.

:: --- 3. CONTROLLO E AVVIO DI POSTGRESQL (Metodo PowerShell) ---
ECHO Verificando lo stato del servizio PostgreSQL...
SET PG_SERVICE_NAME=postgresql-x64-17

powershell -Command "Get-Service -Name '%PG_SERVICE_NAME%' | Where-Object {$_.Status -eq 'Running'}" | FIND "Running" > nul
IF %ERRORLEVEL% == 0 (
    ECHO   [OK] Servizio PostgreSQL e' gia' in esecuzione.
) ELSE (
    ECHO   [INFO] Servizio PostgreSQL non e' in esecuzione. Tentativo di avvio...
    NET START "%PG_SERVICE_NAME%" > nul
    TIMEOUT /T 3 /NOBREAK > nul
    powershell -Command "Get-Service -Name '%PG_SERVICE_NAME%' | Where-Object {$_.Status -eq 'Running'}" | FIND "Running" > nul
    IF %ERRORLEVEL% NEQ 0 (
        ECHO   [ERRORE FATALE] Impossibile avviare il servizio PostgreSQL.
        PAUSE
        EXIT
    )
    ECHO   [OK] PostgreSQL avviato con successo.
)
ECHO.

:: --- 4. INDIVIDUAZIONE INDIRIZZO IP ---
ECHO Rilevo indirizzo IP locale...
FOR /F "tokens=2 delims=:" %%a IN ('ipconfig ^| find "IPv4"') DO (
    FOR /F "tokens=*" %%b IN ("%%a") DO SET LOCAL_IP=%%b
)
ECHO.
ECHO   **************************************************************
ECHO   *   Indirizzo da comunicare agli utenti della rete locale:   *
ECHO                 http://%LOCAL_IP%:8000                        
ECHO   *                                                            *
ECHO   *          Invece per accedere da questo PC usare:           *
ECHO   *            usare http://localhost:8000                     *
ECHO   **************************************************************
ECHO.

:: --- 5. APERTURA BROWSER ---
ECHO Avvio del browser sulla pagina di login tra 3 secondi...
TIMEOUT /T 3 /NOBREAK > nul
start "" "http://127.0.0.1:8000/accounts/login/"

:: --- 6. AVVIO APPLICAZIONE DJANGO ---
ECHO.
ECHO Avvio del server dell'applicazione...
ECHO.
ECHO =============================================================================
ECHO =                    IL SERVER E' ORA ATTIVO.                               =
ECHO =  NON CHIUDERE QUESTA FINESTRA PER MANTENERE IL GESTIONALE IN FUNZIONE.    =
ECHO =============================================================================
ECHO.

CALL .\venv\Scripts\activate
waitress-serve --host=0.0.0.0 --port=8000 --threads=8 config.wsgi:application 2>nul