Guida Completa: Installazione, Gestione e Sicurezza di PostgreSQL su macOS

### **Panoramica Teorica: La Strategia Corretta**

Il nostro approccio si basa su tre pilastri:

1.  **Installazione Pulita e Gestibile:** Useremo **Homebrew**, il gestore di pacchetti standard de facto per macOS. Questo evita di "inquinare" il sistema con file sparsi e ci fornisce strumenti semplici per aggiornare, avviare, fermare e disinstallare PostgreSQL.
2.  **Gestione Semplificata del Servizio:** Sfrutteremo i `brew services` per gestire il ciclo di vita del server PostgreSQL (avvio, arresto, riavvio automatico), astraendo la complessità dei comandi nativi.
3.  **Sicurezza a Livelli (Defense in Depth):** La sicurezza non è un singolo interruttore, ma una serie di pratiche:
    *   **Autenticazione Forte:** Non fidarsi mai delle impostazioni predefinite per l'accesso.
    *   **Minimo Privilegio:** Le applicazioni non devono MAI connettersi con l'utente "amministratore" (superuser).
    *   **Controllo degli Accessi di Rete:** Limitare chi può connettersi e da dove.
    *   **Manutenzione Regolare:** Mantenere il software aggiornato è una misura di sicurezza critica.

---

### **Procedura Pratica Dettagliata (Step-by-Step)**

#### **Fase 1: Installazione tramite Homebrew**

1.  **Installare Homebrew (se non già presente):**
    *   **Scopo:** Installare il gestore di pacchetti che useremo per PostgreSQL.
    *   **Comando:**
        ```bash
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        ```

2.  **Installare PostgreSQL:**
    *   **Scopo:** Scaricare e installare la versione più recente e stabile di PostgreSQL.
    *   **Comando:**
        ```bash
        brew install postgresql
        ```
    *   **Cosa succede dietro le quinte?**
        *   Homebrew scarica i file di PostgreSQL.
        *   Li installa in una directory dedicata (es. `/opt/homebrew/Cellar/postgresql/...` su Mac Apple Silicon).
        *   Crea le directory necessarie per i dati (es. `/opt/homebrew/var/postgres`).
        *   Esegue `initdb`, un comando che crea un "cluster di database", ovvero l'ambiente iniziale che conterrà tutti i tuoi database.
        *   Crea un utente "superuser" in PostgreSQL con lo stesso nome del tuo utente macOS.

#### **Fase 2: Gestione del Servizio (Avvio e Arresto)**

Hai due modi principali per gestire il server, uno facile e uno manuale. **Useremo quasi sempre il primo.**

1.  **Metodo Raccomandato: `brew services`**
    *   **Scopo:** Avviare PostgreSQL e configurarlo per partire automaticamente ad ogni login. È la scelta ideale per un ambiente di sviluppo.
    *   **Comando di avvio:**
        ```bash
        brew services start postgresql
        ```
    *   **Comando di arresto:**
        ```bash
        brew services stop postgresql
        ```
    *   **Comando di riavvio:**
        ```bash
        brew services restart postgresql
        ```
    *   **Verifica dello stato:**
        ```bash
        brew services list 
        ```
        Questo comando ti mostrerà `postgresql` e il suo stato (`started` o `stopped`).

2.  **Metodo Manuale (per conoscenza):**
    *   **Scopo:** Avviare il server solo per la sessione corrente, senza che si riavvii automaticamente. Utile per un uso sporadico.
    *   **Comando di avvio manuale:** `pg_ctl -D /opt/homebrew/var/postgres start`
    *   **Comando di arresto manuale:** `pg_ctl -D /opt/homebrew/var/postgres stop`

#### **Fase 3: Best Practice di Sicurezza e Configurazione Iniziale**

Questa è la fase più importante dopo l'installazione.

1.  **Connessione Iniziale e Creazione di un Utente Dedicato:**
    *   **Teoria (Principio del Minimo Privilegio):** Non usare mai il superuser (il tuo utente macOS) per le tue applicazioni. Se l'applicazione viene compromessa, l'attaccante avrebbe il controllo totale di tutti i database. Creiamo sempre un utente con permessi limitati.
    *   **Passaggi Pratici:**
        1.  **Connettiti al database di default:**
            ```bash
            psql postgres
            ```
        2.  **Crea un utente per la tua applicazione con una password sicura:**
            ```sql
            CREATE USER nome_utente_app WITH PASSWORD 'una_password_molto_robusta';
            ```
        3.  **Crea un database per la tua applicazione:**
            ```sql
            CREATE DATABASE nome_db_app;
            ```
        4.  **Assegna i permessi a quell'utente SOLO per quel database:**
            ```sql
            GRANT ALL PRIVILEGES ON DATABASE nome_db_app TO nome_utente_app;
            ```
        5.  **Esci da psql:** `\q`

2.  **Configurare l'Autenticazione (File `pg_hba.conf`):**
    *   **Teoria:** Questo file è il "guardiano" del tuo server. Decide **chi** può connettersi, da **quale indirizzo IP**, a **quale database** e con **quale metodo di autenticazione**.
    *   **Passaggi Pratici:**
        1.  **Trova il file:** Dentro `psql`, esegui `SHOW hba_file;`. Ti darà il percorso esatto.
        2.  **Modifica il file:** Apri quel file con un editor di testo.
        3.  **Cambia il metodo di autenticazione:** Le impostazioni di default di Homebrew sono spesso `trust` o `peer` per le connessioni locali. Questo significa che non viene chiesta una password. **Questo non è sicuro.** Dobbiamo forzare la richiesta di password.
            *   Trova le righe che assomigliano a queste:
                ```
                # TYPE  DATABASE        USER            ADDRESS                 METHOD
                local   all             all                                     peer
                host    all             all             127.0.0.1/32            peer
                ```
            *   Cambia il metodo in `scram-sha-256` (più moderno e sicuro) o `md5` (compatibile con client più vecchi). Questo impone la verifica della password.
                ```
                # TYPE  DATABASE        USER            ADDRESS                 METHOD
                local   all             all                                     scram-sha-256
                host    all             all             127.0.0.1/32            scram-sha-256
                ```
        4.  **Ricarica la configurazione:** Dopo aver salvato il file, devi dire a PostgreSQL di rileggere le modifiche con `brew services restart postgresql`.

3.  **Configurare l'Accesso di Rete (File `postgresql.conf`):**
    *   **Teoria:** Di default, per sicurezza, PostgreSQL accetta connessioni solo dal computer locale (`localhost`). Se non hai bisogno di accedere al database da un altro computer, **non cambiare questa impostazione**.
    *   **Passaggi Pratici (solo se serve accesso di rete):**
        1.  **Trova il file:** Dentro `psql`, esegui `SHOW config_file;`.
        2.  **Modifica il file:** Cerca la riga `listen_addresses = 'localhost'`.
        3.  **Cambiala** per accettare connessioni da indirizzi IP specifici (es. `listen_addresses = 'localhost, 192.168.1.10'`) o da qualsiasi indirizzo (`listen_addresses = '*'`). **ATTENZIONE:** Usare `'*'` è pericoloso se non hai un firewall.
        4.  **Usa un Firewall:** Se abiliti l'accesso di rete, assicurati che il firewall di macOS (o un firewall di rete) sia attivo e permetta connessioni sulla porta `5432` solo da indirizzi IP fidati.
