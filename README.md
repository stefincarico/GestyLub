# GestionaleDjango - Gestionale Aziendale
-
**Versione:** 1.0 08-2025
**Autore:** [Angelo Lubrano/Lubry Tech]
**Tecnologie:** Python, Django, PostgreSQL, Bootstrap 5

---

## 1. Descrizione del Progetto

**GestionaleDjango** è una piattaforma di gestione aziendale (ERP) web-based progettata per piccole e medie imprese. Centralizza le operazioni contabili, amministrative e di gestione del personale in un'unica interfaccia sicura e multi-utente.

Questo documento fornisce le istruzioni complete per l'installazione e il primo avvio del sistema su una macchina server Windows in un ambiente di rete locale.

## 2. Requisiti di Sistema

-   **Sistema Operativo:** Windows 10 / Windows 11 / Windows Server (64-bit)
-   **Software:**
    -   Python 3.10 o superiore
    -   PostgreSQL 15 o superiore
-   **Hardware:** Minimo 4GB di RAM, 20GB di spazio libero su disco.
-   **Rete:** Connessione di rete locale (LAN).

---

## 3. Guida all'Installazione (Prima Configurazione)

Questa procedura va eseguita **una sola volta** sulla macchina che fungerà da server.

### Fase A: Installazione del Software di Base

#### 1. Installare Python
-   Vai su [python.org](https://www.python.org/downloads/windows/) e scarica l'installer per Windows.
-   **IMPORTANTE:** Durante l'installazione, assicurati di mettere la spunta sulla casella **"Add Python to PATH"**.
-   Verifica l'installazione aprendo un Prompt dei comandi (`cmd`) e digitando: `python --version`. Dovresti vedere la versione installata.

#### 2. Installare PostgreSQL
-   Vai su [postgresql.org/download/windows/](https://www.postgresql.org/download/windows/) e scarica l'installer.
-   Durante l'installazione guidata:
    -   Lascia i componenti di default.
    -   Quando ti viene chiesta la password per l'utente `postgres`, inserisci una password sicura. **ANNOTALA E CONSERVALA IN UN POSTO SICURO**, ti servirà tra poco.
    -   Lascia la porta di default (`5432`).
-   Al termine dell'installazione, il server PostgreSQL si avvierà come servizio di Windows.

#### 3. Installare Git
-   Vai su [git-scm.com/download/win](https://git-scm.com/download/win) e scarica l'installer.
-   Esegui l'installazione lasciando le opzioni di default.

### Fase B: Clonare e Configurare il Progetto

#### 1. Clonare la Repository
-   Apri un Prompt dei comandi (`cmd`).
-   Naviga nella cartella dove vuoi installare il gestionale (es. `C:\`).
-   Esegui il seguente comando (sostituisci l'URL con quello del tuo repository):
    ```bash
    git clone https://github.com/tuo-utente/tuo-repository.git GestiLub
    ```
-   Entra nella cartella appena creata:
    ```bash
    cd GestiLub
    ```

#### 2. Creare e Configurare l'Ambiente
-   **Creare l'Ambiente Virtuale:**
    ```bash
    python -m venv venv
    ```
-   **Attivare l'Ambiente Virtuale:**
    ```bash
    .\venv\Scripts\activate
    ```
    (Vedrai `(venv)` apparire all'inizio della riga del prompt).
-   **Installare le Dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

#### 3. Configurare il Database e le Impostazioni
-   **Crea il file `.env`:** Nella cartella `GestiLub`, crea un file di testo chiamato `.env` (assicurati che non abbia estensioni come `.txt`).
-   Incollaci dentro il seguente contenuto, **sostituendo la password** con quella che hai scelto durante l'installazione di PostgreSQL:
    ```ini
    # File .env - Impostazioni di Produzione Locale
    
    SECRET_KEY=genera-una-chiave-segreta-casuale-molto-lunga-e-incollala-qui
    DEBUG=False
    ALLOWED_HOSTS=*
    
    # Impostazioni Database
    DB_NAME=gestilub_db
    DB_USER=postgres
    DB_PASSWORD=LA_TUA_PASSWORD_DI_POSTGRESQL
    DB_HOST=localhost
    DB_PORT=5432
    ```
    *Nota: Puoi generare una `SECRET_KEY` da [questo sito](https://djecrety.ir/).*

-   **Crea il Database Vuoto:**
    -   Apri **pgAdmin 4** (dovrebbe essere stato installato con PostgreSQL).
    -   Connettiti al tuo server (ti chiederà la password di `postgres`).
    -   Nel pannello a sinistra, fai click destro su "Databases" -> "Create" -> "Database...".
    -   Come nome, inserisci `gestilub_db`.
    -   Clicca "Save".

-   **Applica le Migrazioni del Database:**
    Nel Prompt dei comandi, con `(venv)` attivo, esegui:
    ```bash
    python manage.py migrate
    ```

-   **Raccogli i File Statici:**
    ```bash
    python manage.py collectstatic
    ```
    Digita `yes` quando richiesto.

#### 4. Creare il Primo Super Amministratore
-   Esegui questo comando e segui le istruzioni per creare l'utente che gestirà l'intera piattaforma:
    ```bash
    python manage.py createsuperuser
    ```

### Fase C: Preparare l'Avvio Semplificato

#### 1. Verificare il Nome del Servizio PostgreSQL
-   Premi `Win + R`, scrivi `services.msc` e premi Invio.
-   Trova il servizio di PostgreSQL. Il nome esatto si trova nella colonna **"Nome"**. Di solito è `postgresql-x64-XX` (dove `XX` è la versione, es. `16`).
-   Apri il file `start_gestionale.bat` con un editor di testo (come Blocco Note) e assicurati che la riga `SET PG_SERVICE_NAME=...` contenga questo nome esatto.

#### 2. Creare il Collegamento sul Desktop
-   Trova il file `start_gestionale.bat` nella cartella `GestiLub`.
-   Fai **click destro** su di esso e scegli **"Crea collegamento"**.
-   Rinomina il collegamento come preferisci (es. "Avvia Gestionale").
-   **Imposta l'avvio come Amministratore:**
    -   Fai click destro sul **collegamento**.
    -   Vai su "Proprietà".
    -   Scheda "Collegamento" -> "Avanzate...".
    -   Metti la spunta su **"Esegui come amministratore"**. Clicca OK due volte.
-   Sposta questo collegamento sul Desktop.

### 3. Aggiungere PostgreSQL al PATH di Sistema (Obbligatorio per i Backup)
Apri le "Impostazioni di sistema avanzate" di Windows.
Clicca su "Variabili d'ambiente...".
Nella sezione "Variabili di sistema", trova e seleziona la variabile **Path** e clicca "Modifica...".
Clicca "Nuovo" e aggiungi il percorso alla cartella bin della tua installazione di PostgreSQL. Di solito è:
C:\Program Files\PostgreSQL\16\bin
(verifica che la versione 16 sia corretta).
Clicca OK su tutte le finestre.
Riavvia il computer per rendere effettiva la modifica.

**L'installazione è completata!**

---

## 4. Guida all'Uso Quotidiano

### Per Avviare il Gestionale:
1.  Fai doppio click sull'icona **"Avvia Gestionale"** che hai creato sul Desktop.
2.  Si aprirà una finestra di "Controllo Account Utente". Clicca **"Sì"**.
3.  Si aprirà una finestra nera del terminale. Verrà controllato PostgreSQL e avviato il server. Verrà mostrato l'indirizzo IP da comunicare ai colleghi.
4.  Il tuo browser di default si aprirà automaticamente sulla pagina di login.
5.  **IMPORTANTE: Non chiudere la finestra nera del terminale. Deve rimanere aperta per tutto il tempo che il gestionale deve essere accessibile.**

### Per Fermare il Gestionale:
1.  Semplicemente **chiudi la finestra nera del terminale** che è stata aperta dallo script di avvio.

### Accesso per gli Altri Utenti:
-   Gli altri utenti nella stessa rete locale potranno accedere al gestionale digitando nel loro browser l'indirizzo IP mostrato all'avvio (ad esempio `http://192.168.1.100:8000`).


## Modalità SVILUPPO (quando aggiungi nuove funzionalità):
Obiettivo: Massima visibilità per te, lo sviluppatore.
Configurazione (.env): DEBUG = True
Comportamento:
Pagine di Errore Dettagliate: Se c'è un bug, Django ti mostra la pagina gialla con tutta la traccia dell'errore, le variabili locali, ecc. Questo è FONDAMENTALE per il debug.
Ricaricamento Automatico: Il server di sviluppo (manage.py runserver) si riavvia automaticamente ogni volta che salvi un file, permettendoti di vedere le modifiche all'istante.
Servizio Statici Semplificato: Django serve i file statici direttamente, senza bisogno di collectstatic.
Come si avvia: python manage.py runserver
Se hai modificato file statici (CSS/JS), ricorda di eseguire:
 - python manage.py collectstatic

## Modalità PRODUZIONE (quando l'utente finale usa l'applicazione):
Obiettivo: Massima sicurezza, performance e stabilità.
Configurazione (.env): DEBUG = False
Comportamento:
Pagine di Errore Generiche: Se c'è un errore, l'utente vede una pagina "500 Server Error" generica e amichevole, senza rivelare dettagli tecnici sensibili.
Performance Ottimizzate: Whitenoise serve i file statici in modo super-veloce, con caching e compressione.
Server Robusto: Waitress gestisce più utenti contemporaneamente in modo efficiente.
Come si avvia: Il nostro script start_gestionale.bat (che usa waitress).

5. Procedure di Backup e Ripristino
Backup
Accedi al gestionale come utente Super Amministratore.
Naviga nel "Pannello Superadmin" (/super/).
Nella sezione "Utilità di Manutenzione", clicca su "Esegui Backup Database".
Un file di backup con nome YYYYMMDD_HHMMSS_gestilub_db_backup.sql verrà salvato nella cartella Documenti dell'utente del PC server.
È fondamentale copiare regolarmente questo file su un'unità esterna o un cloud storage.
Ripristino (Operazione di Emergenza)
ATTENZIONE: Questa procedura CANCELLA tutti i dati attuali e li sostituisce con quelli del backup. Da eseguire solo in caso di problemi gravi.
Assicurati che il server del gestionale sia spento.
Trova il file di backup .sql che vuoi ripristinare.
Nella cartella GestiLub sul server, fai click destro su restore_database.bat e scegli "Esegui come amministratore".
Segui le istruzioni a schermo: conferma l'operazione, inserisci il percorso completo del file di backup e la password di PostgreSQL quando richiesta.
Al termine, riavvia il gestionale usando lo script start_gestionale.bat.