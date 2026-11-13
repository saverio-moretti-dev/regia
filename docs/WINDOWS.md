# Regia su Windows: cosa manca e come portarla

Stato: la Regia è costruita e provata **sul Mac**. Su Windows il server e la pagina partono (`avvia-windows.bat`), ma
alcune parti usano strumenti che esistono solo su macOS. Questo documento serve a **un altro sviluppatore o agente** che
voglia completare il port: dice cosa è solo Mac, file per file, come sostituirlo e quanta fatica stimiamo.
**Nessuna di queste modifiche è stata fatta né provata su un Windows vero.**

## Cosa funziona già (da verificare comunque su una macchina vera)
- `plancia/server.py` (solo libreria standard, file letti/scritti con `encoding="utf-8"`), la pagina in `plancia/web/`,
  messaggi, sospesi, fissati, allegati, elementi (`elementi.py`).
- `verifica.py` cerca Chrome ed Edge nei percorsi di Windows (`%ProgramFiles%`, `%LocalAppData%`); senza, controlla solo i
  dati e lo dice («VERIFICATO SOLO NEI DATI»).
- Il pulsante Terminale è già nascosto quando `sys.platform != "darwin"` (`raccogli.py`, campo `terminale`).
- Percorsi: `os.path` ovunque; `PLANCIA_FILE_RADICI` si separa con `;` su Windows (`os.pathsep`).

## Cosa è solo Mac, file per file

| File:riga (circa) | Cosa fa sul Mac | Su Windows oggi | Come portarlo | Fatica |
|---|---|---|---|---|
| `raccogli.py` `ps -A -o ppid=,etime=,command=` (~239) | comando in corso e da quanto, per ogni sessione | lista vuota: niente «comando in corso», niente banner «ferma su un comando» | PowerShell: `Get-CimInstance Win32_Process \| Select ProcessId,ParentProcessId,CreationDate,CommandLine \| ConvertTo-Json`, poi stessa struttura `{ppid: [(secondi, comando)]}` | media (2-3 h con prove) |
| `sup.py` `ps -A -E -ww -o command=` (~79) | trova Regie di prova accese (variabile `PLANCIA_DATI` nell'ambiente dei processi) | avviso «regie di prova» assente (solo un aiuto, non blocca) | Windows non espone l'ambiente di altri processi: cercare `server.py` nella `CommandLine` e scrivere un file `prova-attiva.json` all'avvio del server di prova | bassa |
| `server.py` `/api/terminale` (~150-176): `ps -o tty=` + `osascript` su Terminal.app | porta in primo piano la scheda del Terminale di quella sessione | pulsante nascosto | Windows Terminal non sa portare in primo piano una scheda esistente da fuori. Alternativa: aprire una **scheda nuova** con `wt.exe -w 0 nt -d <cartella> claude --resume <session_id>` (riprende la sessione, non la stessa finestra) | media; scelta di prodotto (riprendere ≠ riportare in primo piano) |
| `server.py` `_sorveglia` → `os.execv` (~102) | si rilancia da solo quando cambia un `.py` | `execv` su Windows avvia un processo nuovo e il vecchio esce: la console di `avvia-windows.bat` può chiudersi | su Windows: `subprocess.Popen([sys.executable] + sys.argv)` + `os._exit(0)` dopo aver chiuso il socket, oppure niente rilancio (`PLANCIA_RILANCIO=0`) e si rilancia a mano | bassa |
| `plancia/avvio/regia.server.plist.esempio` (launchd) | avvio automatico al login | a mano | `installa-windows.bat`: `schtasks /Create /SC ONLOGON /TN Regia /TR "py -3 <percorso>\plancia\server.py 8765"` (senza amministratore) + `disinstalla-windows.bat` con `schtasks /Delete` | bassa (1 h) |
| `plancia/app-mac/` (Swift, `Regia.app`) | finestra dedicata con icona nel Dock | — | non serve: Chrome/Edge → «Installa app» sulla pagina (manifest e service worker ci sono già) | nessuna |
| `avvia-mac.command` | avvio a doppio clic | `avvia-windows.bat` (c'è già) | — | — |

## Non fanno parte della Regia
L'apertura di nuove sessioni nelle schede del Terminale e il riavvio degli agenti sono strumenti del metodo di chi la
usa, non della Regia: non sono in questa repo.

## Come provarlo senza un PC Windows
GitHub Actions con `runs-on: windows-latest`: avvia `py -3 plancia/server.py 8799` in sottofondo con
`PLANCIA_DATI` in una cartella temporanea e `PLANCIA_STATO_FINTO` (stato finto, vedi `server.py`), chiede `/api/stato`,
aggiunge un elemento con `sup.py elemento testo --zona sup "prova" --no-verifica`, poi `verifica.py --tutti --porta 8799`
(Edge è preinstallato sulle macchine Windows di GitHub). È gratis per le repo pubbliche. La prova vera resta su un PC
con Claude Code installato.

## Stima complessiva
Port completo (processi, rilancio, avvio automatico, pulsante Terminale come «riprendi in una scheda nuova», workflow
di prova): **circa una giornata di lavoro** di uno sviluppatore che conosce Python, più le prove su una macchina vera.
Ordine consigliato: avvio automatico e rilancio (piccoli, utili subito) → processi → workflow di prova → pulsante Terminale.
