#!/usr/bin/env python3
"""Promemoria della Regia (pezzo 2, ; idea da guarda.py dell'ufficio): niente richiesta dell'utente
si perde. Calcolo puro, 0 token, nessuna scrittura: lo usano raccogli.py (riquadro nell'app) e sup.py (righe nel giro).

  NON GIRATO    richiesta scritta a una sessione, il SUP non l'ha ancora presa (nuova/letta) da più di 3 min
  SENZA RISPOSTA richiesta scritta al SUP, ancora senza risposta (nuova/letta) da più di 3 min
  FERMA         sessione a cui il SUP ha girato una richiesta (verde/giallo, nessuna risposta del SUP dopo il giro) e che
                da allora NON ha più lavorato (ultima attività prima del giro) da più di 5 min: l'ordine non le è arrivato
                o non l'ha preso. Una riga per sessione. Se la sessione ha lavorato dopo il giro ha risposto nella sua chat:
                niente avviso (12/11: con «nessuna risposta» e basta uscivano 19 falsi allarmi sui dati veri)

Fuori: richieste più vecchie di 24 h, richieste trattenute mentre il SUP è in pausa (stato «attesa»), sessioni in pausa,
sessioni non più vive (FERMA). Con il SUP in pausa i NON GIRATO / SENZA RISPOSTA non escono: li rilascia `sup.py riprendi`.
"""
import time

ATTESA_GIRO = 3 * 60       # NON GIRATO / SENZA RISPOSTA
ATTESA_FERMA = 5 * 60      # FERMA: ordine girato e sessione ferma
FINESTRA = 24 * 3600
APERTI = ("nuova", "letta")


def _ts(ora):
    try:
        return time.mktime(time.strptime(str(ora)[:19], "%Y-%m-%d %H:%M:%S"))
    except (TypeError, ValueError):
        return None


def _risposta(stato):
    return any(x.get("stato") == "risposta" for x in (stato or {}).get("storia") or [])


def _giro(stato):
    """Ora dell'ultimo «girata a» (verde/giallo con a) nella storia."""
    ore = [x.get("ora") for x in (stato or {}).get("storia") or [] if x.get("stato") in ("verde", "giallo") and x.get("a")]
    return max(ore) if ore else (stato or {}).get("ora")


def _risposta_dopo_giro(stato):
    """Il SUP ha scritto una risposta DOPO aver girato la richiesta (di solito l'esito dell'agente riferito all'utente).
    La risposta nello stesso secondo del giro è la conferma «girata a X» di `sup.py rispondi --a`, non un esito."""
    g = _giro(stato) or ""
    return any(x.get("stato") == "risposta" and (x.get("ora") or "") > g for x in (stato or {}).get("storia") or [])


def calcola(coda, richieste, sessioni, sup_in_pausa=False, ora=None):
    """coda: voci di coda.jsonl (già unite); richieste: richieste.json; sessioni: {NOME: {"stato", "ultima"}} delle
    sessioni vive (ultima = epoch dell'ultima attività) (stato come raccogli: al lavoro / ferma / in attesa / in pausa). Ritorna una lista ordinata dalla più
    vecchia: {"tipo", "id", "sessione", "a", "minuti", "testo"}."""
    ora = ora or time.time()
    out, ferme = [], {}
    for r in coda:
        if r.get("attesa"):
            continue
        t0 = _ts(r.get("ora"))
        if t0 is None or ora - t0 > FINESTRA:
            continue
        s = richieste.get(r.get("id"), {}) or {}
        st = s.get("stato", "nuova")
        dest = (r.get("sessione") or "").upper()
        if st in APERTI and not _risposta(s):
            if sup_in_pausa or ora - t0 < ATTESA_GIRO:
                continue
            out.append({"tipo": "SENZA RISPOSTA" if dest == "SUP" else "NON GIRATO", "id": r.get("id"), "sessione": dest,
                        "a": None, "minuti": int((ora - t0) // 60), "testo": r.get("testo", "")})
        elif st in ("verde", "giallo") and s.get("a") and not _risposta_dopo_giro(s):
            a = s["a"].upper()
            v = sessioni.get(a)
            girata = _ts(_giro(s)) or t0
            if not v or v.get("stato") != "ferma" or ora - girata < ATTESA_FERMA:
                continue
            if (v.get("ultima") or 0) >= girata:  # ha lavorato dopo il giro: ha preso l'ordine
                continue
            f = ferme.setdefault(a, {"tipo": "FERMA", "id": r.get("id"), "sessione": dest, "a": a, "minuti": 0,
                                     "testo": r.get("testo", ""), "n": 0, "ids": []})
            f["n"] += 1
            f["ids"].append(r.get("id"))
            if int((ora - girata) // 60) >= f["minuti"]:  # testo e minuti della richiesta più vecchia
                f.update(minuti=int((ora - girata) // 60), id=r.get("id"), testo=r.get("testo", ""))
    out += list(ferme.values())
    out.sort(key=lambda x: -x["minuti"])
    return out


def riga(p, lung=120):
    """Riga per il SUP (stessa forma di guarda.py dell'ufficio)."""
    t = " ".join(str(p.get("testo") or "").split())
    t = t if len(t) <= lung else t[:lung - 1] + "…"
    if p["tipo"] == "FERMA":
        altre = f" (+{p['n'] - 1} altre)" if p.get("n", 1) > 1 else ""
        return f"FERMA sessione={p['a']} da {p['minuti']} min :: ordine girato e mai preso id={p['id']}{altre} :: {t}"
    return f"{p['tipo']} da {p['minuti']} min: id={p['id']} sessione={p['sessione']} :: {t}"


if __name__ == "__main__":  # prova veloce: python3 promemoria.py
    adesso = time.time()
    f = lambda m: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(adesso - m * 60))
    coda = [{"id": "a", "sessione": "SUP", "testo": "al sup", "ora": f(10)},
            {"id": "b", "sessione": "METODO", "testo": "a metodo", "ora": f(4)},
            {"id": "c", "sessione": "METODO", "testo": "girata", "ora": f(30)},
            {"id": "d", "sessione": "SUP", "testo": "fresca", "ora": f(1)},
            {"id": "e", "sessione": "SUP", "testo": "risposta", "ora": f(20)},
            {"id": "g", "sessione": "SUP", "testo": "trattenuta", "ora": f(20), "attesa": True}]
    rich = {"c": {"stato": "verde", "a": "METODO", "ora": f(25),
                  "storia": [{"stato": "verde", "ora": f(25), "a": "METODO"}, {"stato": "risposta", "ora": f(25), "a": "SUP"}]},
            "e": {"stato": "letta", "storia": [{"stato": "risposta"}]}}
    for p in calcola(coda, rich, {"METODO": {"stato": "ferma", "ultima": adesso - 40 * 60}}, ora=adesso):
        print(riga(p))
