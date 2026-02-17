# PostgreSQL to SQL Server Migrator

Script Python per migrare i dati di spend dal database PostgreSQL dello Spendloader alla tabella di spend di WiseBuy su SQLServer.

## Descrizione

Lo script estrae i dati dalla tabella `tb_spend_l2` di PostgreSQL, genera file SQL con statement INSERT ottimizzati per SQL Server, e opzionalmente li esegue direttamente sulla tabella target di WiseBuy.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Modifica .env con le tue credenziali
```

## Configurazione

Modifica il file `.env` con le credenziali e configurazioni database.

## Utilizzo

```bash
# Genera ed esegui gli script SQL
python migrator.py

# Solo generazione (senza esecuzione)
python migrator.py -g
```

## Personalizzazione

- **Query**: Modifica `extraction_query.sql` per personalizzare l'estrazione dati
- **Periodi**: Modifica la lista `reference_periods` in `migrator.py`
- **Output**: Gli script generati vengono salvati nella cartella `output/`

## Note
- Richiede `sqlcmd.exe` (Windows) per l'esecuzione degli script, oltre che i due database accessibili dalla macchina in cui si sta eseguendo questo script (pensato per uso DEV, locale)
- Funziona da WSL con conversione automatica dei path
