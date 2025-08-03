@echo off
REM =================================================================
REM == Script di avvio per GestionaleDjango                          ==
REM =================================================================

TITLE GestionaleDjango Server

ECHO.
ECHO =================================================
ECHO  AVVIO SERVER GESTIONALEDJANGO
ECHO =================================================
ECHO.

REM --- PASSO 1: CONTROLLO E AVVIO DI POSTGRESQL ---
ECHO Verifico lo stato del servizio PostgreSQL...
SC QUERY "postgresql-x64-17" | FIND "STATE" | FIND "RUNNING" > nul
IF %ERRORLEVEL% == 0 (
    ECHO   [OK] Il servizio PostgreSQL e' gia' in esecuzione.
) ELSE (
    ECHO   [AVVISO] Il servizio PostgreSQL non e' in esecuzione. Tento l'avvio...
    NET START "postgresql-x64-17"
    IF %ERRORLEVEL% == 0 (
        ECHO   [OK] Servizio PostgreSQL avviato con successo.
    ) ELSE (
        ECHO   [ERRORE FATALE] Impossibile avviare PostgreSQL. Contattare l'assistenza.
        PAUSE
        EXIT
    )
)
ECHO.

REM --- PASSO 2: INDIVIDUAZIONE DELL'INDIRIZZO IP ---
ECHO Cerco l'indirizzo IP della macchina nella rete locale...
FOR /F "tokens=2 delims=:" %%a IN ('ipconfig ^| find "IPv4"') DO (
    FOR /F "tokens=*" %%b IN ("%%a") DO SET LOCAL_IP=%%b
)
ECHO.
ECHO   *********************************************************
ECHO   *                                                       *
ECHO   *   Gestionale accessibile all'indirizzo:               *
ECHO   *                                                       *
ECHO   *         http://%LOCAL_IP%:8000                         *
ECHO   *                                                       *
ECHO   *   Comunicare questo indirizzo ai colleghi.            *
ECHO   *                                                       *
ECHO   *********************************************************
ECHO.
ECHO Per fermare il server, chiudere questa finestra.
ECHO.

REM --- PASSO 3: AVVIO DELL'APPLICAZIONE DJANGO CON WAITRESS ---
ECHO Avvio del server dell'applicazione...

REM Attiva l'ambiente virtuale
CALL .\venv\Scripts\activate

REM Lancia Waitress per servire l'applicazione Django
REM --host=0.0.0.0 : Ascolta su tutte le interfacce di rete (necessario per essere visibile in LAN)
REM --port=8000   : Usa la porta 8000
REM --threads=8   : Numero di thread per gestire le richieste (buon punto di partenza per 10 utenti)
waitress-serve --host=0.0.0.0 --port=8000 --threads=8 config.wsgi:application

REM --- PASSO 4: APERTURA DEL BROWSER (Opzionale, eseguito quasi in parallelo) ---
REM Lo script arriverà qui solo dopo che waitress si è chiuso.
REM Per un avvio immediato, potremmo usare 'start'.

REM Creiamo un piccolo file VBS per lanciare il browser in background.
ECHO CreateObject("WScript.Shell").Run "http://127.0.0.1:8000/", 1, false > temp_open_browser.vbs
start temp_open_browser.vbs