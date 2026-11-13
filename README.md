# Regia

> **English summary.** Regia is a local web dashboard to follow and steer several **Claude Code** sessions from one
> place: who is working on what, how much context and plan usage they consume, a chat with the coordinating session,
> pending items, attachments, and pinned elements (text, links, images, PDFs, reminders). Python standard library
> only, runs on `127.0.0.1`, no accounts, no external services. Built and tested on **macOS**; Windows notes in
> [`docs/WINDOWS.md`](docs/WINDOWS.md). The interface is in Italian. MIT licence.

Pannello in una pagina web per seguire e guidare le sessioni di **Claude Code** da un posto solo:
chi sta lavorando, a cosa, quanto consuma, i messaggi per il coordinatore (la sessione «SUPERAGENTE»),
le cose in sospeso, i permessi in attesa, gli allegati, e gli **elementi** fissati nella pagina
(testi, link, immagini, pdf, promemoria).

Gira **solo sul tuo computer** (indirizzo `127.0.0.1`): nessun servizio esterno, niente account.

## Scaricare

- **Ultima versione**: pagina [Releases](../../releases/latest) → `regia-<versione>.zip`, poi estrai la cartella dove vuoi.
- Oppure: `git clone` di questa repo.

## Cosa serve

- **macOS** (provato) con **Python 3.9 o più recente**: solo libreria standard, niente `pip install`.
- **Claude Code** installato: la Regia legge le sessioni con `claude agents --json` e le trascrizioni in `~/.claude/projects`.
- **Google Chrome** (facoltativo): serve a `verifica.py` per controllare la pagina e fare le schermate.
- Facoltativi (senza, le relative colonne restano vuote, nessun errore):
  - [dont-waste-your-token](https://github.com/saverio-moretti-dev/dont-waste-your-token) per la scheda Token;
  - [superagent-method](https://github.com/saverio-moretti-dev/superagent-method) (`tools/passaggi.py`) per le note di passaggio.
  Mettile **accanto** alla cartella della Regia (stessa cartella madre) e vengono trovate da sole; altrimenti vedi
  [Impostazioni](#impostazioni).

## Avvio sul Mac

Doppio clic su `avvia-mac.command` (la prima volta: tasto destro → Apri, perché non è firmato), oppure dal Terminale
nella cartella della Regia:

```
python3 plancia/server.py
```

poi apri <http://127.0.0.1:8765>. Un'altra porta: `python3 plancia/server.py 8790`.
Quando cambia un file `.py` il server si rilancia da solo.

**Avvio automatico (facoltativo)**: `plancia/avvio/regia.server.plist.esempio` — sostituisci `PERCORSO_REPO`, `PYTHON`
e `CASA`, copialo in `~/Library/LaunchAgents/local.regia.server.plist`, poi
`launchctl load ~/Library/LaunchAgents/local.regia.server.plist`.

**App per Mac (facoltativa)**: `plancia/app-mac/costruisci.sh` costruisce `Regia.app` (serve Xcode); `--installa` la
copia in `~/Applications`. `REGIA_URL` cambia l'indirizzo che apre (predefinito `http://127.0.0.1:8765/`).

**Windows**: non ancora supportato del tutto. La pagina e il server partono (`avvia-windows.bat`), ma alcune parti sono
solo Mac: cosa manca e come portarle è in [`docs/WINDOWS.md`](docs/WINDOWS.md).

## Come parla il coordinatore con la pagina

La sessione che coordina usa `plancia/sup.py` (elenco completo in testa al file):

```
python3 plancia/sup.py nuove                 # messaggi nuovi scritti nella pagina
python3 plancia/sup.py rispondi <id> "testo" # risposta nel filo di quel messaggio
python3 plancia/sup.py sospeso aggiungi "testo"
```

### Elementi: testi, link, immagini, pdf, promemoria

Il coordinatore mette un elemento in una **zona fissa** della pagina: `testata`, `sup` (box del coordinatore),
`sospeso`, `token` (scheda Token) o `sessione:NOME` (sotto la riga di una sessione):

```
python3 plancia/sup.py elemento testo --zona sup --titolo "Nota" "testo con [link](https://esempio.it)"
python3 plancia/sup.py elemento immagine --zona sessione:NOME ~/Desktop/foto.png
python3 plancia/sup.py elemento promemoria --zona sup --quando "2026-12-01 17:00" "testo"
python3 plancia/sup.py elemento lista          # e: sposta, cambia, togli, zone
```

I file vengono **copiati** in `plancia/elementi/` (massimo 25 MB, tipi a elenco chiuso). Dopo ogni modifica parte da
solo **`verifica.py`**: controlla i dati, la pagina vera in Chrome senza finestra (l'elemento è nella zona giusta,
visibile, l'immagine si carica) e fa due schermate (tema chiaro e scuro) in `plancia/verifiche/`. Esito: `VERIFICATO`,
`NON VA: non consegnare`, `NON VERIFICATO` (server spento) o `VERIFICATO SOLO NEI DATI` (manca Chrome). Nessun costo
in token: è tutto Python.

## Impostazioni

Tutte facoltative. Ordine: variabile d'ambiente → `plancia/locale.json` (resta sul tuo computer, non va in git) →
predefinito.

| chiave | a cosa serve | predefinito |
|---|---|---|
| `PLANCIA_CTM` | cartella di dont-waste-your-token | accanto alla Regia |
| `PLANCIA_PASSAGGI` | percorso di `passaggi.py` | accanto alla Regia: `superagent-method/tools/passaggi.py` |
| `PLANCIA_HUB` | cartella con `SESSIONI.md` e `agende/` (metodo del superagente); vuota = colonne vuote | cartella sopra `plancia/` |
| `PLANCIA_LIMITI` | file dei limiti d'uso (scritto dalla barra di stato, se c'è) | `~/.claude/consumo/limiti.csv` |
| `PLANCIA_TRASCRIZIONI` | trascrizioni di Claude Code | `~/.claude/projects` |
| `PLANCIA_FILE_RADICI` | cartelle da cui la pagina può aprire file (separate da `:`) | `~/Desktop` |
| `PLANCIA_ALLEGATO_MB` | dimensione massima di un allegato o di un file di un elemento | `25` |
| `PLANCIA_PORTA` | porta che `verifica.py` controlla | `8765` |
| `PLANCIA_DATI` | dove salvare i dati (code, risposte, elementi…); diverso = server di prova | `plancia/` |
| `note_origini` (solo locale.json) | estensioni Chrome che possono mandare note: `{"chrome-extension://<id>": "SESSIONE"}` | nessuna |

Esempio di `plancia/locale.json`:

```json
{"PLANCIA_CTM": "~/codice/dont-waste-your-token",
 "PLANCIA_PASSAGGI": "~/codice/superagent-method/tools/passaggi.py"}
```

I dati (`coda.jsonl`, `risposte.jsonl`, `insospeso.json`, `elementi.json`…) restano nella cartella `plancia/` e non
vanno in git (`.gitignore`).

## Sicurezza

Il server ascolta solo su `127.0.0.1`: dagli altri computer della rete non si raggiunge. Accetta richieste solo con
Host locale (contro il DNS rebinding); i file aperti dalla pagina sono serviti in sandbox, solo da cartelle ammesse e
di tipi ammessi. **Non esporlo su internet**: non ha password.

## Licenza

[MIT](LICENSE).
