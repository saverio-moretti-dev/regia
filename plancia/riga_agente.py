#!/usr/bin/env python3
"""Riga dell'agente nella Regia (pezzi 1+4, ; idea dal comando `io` del pannello dell'ufficio).

  python3 plancia/riga_agente.py NOME --fatto "cosa ho finito"          riga «Fatto» sotto la sessione
  python3 plancia/riga_agente.py NOME --decidere "cosa serve dall'utente" riquadro «Da decidere» (+ filtro nella Regia)
  python3 plancia/riga_agente.py NOME --decidere-via                     tolto (deciso, o non serve più)
  (--fatto e --decidere insieme vanno bene)

Funziona solo se l'interruttore «Da decidere» della Regia è acceso (opzioni.json): spento → stampa «spento» ed
esce senza scrivere, così gli agenti non spendono niente. Quando usarlo: a fine pezzo (--fatto) e quando un lavoro
aspetta una scelta dell'utente (--decidere); MAI a ogni turno. Le domande vere all'utente restano del SUP (Regola 3):
--decidere dice soltanto all'utente, nella Regia, che quella sessione aspetta lui e su cosa.
Scrive SOLO plancia/righe-agenti.json (in .gitignore).
"""
import json, os, re, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.environ.get("PLANCIA_DATI", QUI)
RIGHE, OPZ = os.path.join(DATI, "righe-agenti.json"), os.path.join(DATI, "opzioni.json")
NOME_OK = re.compile(r"^[A-Z0-9_-]{1,40}$")
MAX = 300


def leggi(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def acceso():
    return bool((leggi(OPZ, {}) or {}).get("da_decidere"))


def main(a):
    if not a or a[0].startswith("-"):
        sys.exit(__doc__)
    nome = a[0].upper()
    if not NOME_OK.match(nome) or nome in ("SUP", "SUPERAGENTE"):
        sys.exit("nome della sessione non valido")
    if not acceso():
        print("spento: l'interruttore «Da decidere» della Regia è spento, niente scritto")
        return
    voce, i = {}, 1
    while i < len(a):
        k = a[i]
        if k in ("--fatto", "--decidere") and i + 1 < len(a):
            t = " ".join(a[i + 1].split())[:MAX]
            voce[k[2:]] = t
            i += 2
        elif k == "--decidere-via":
            voce["decidere"] = ""
            i += 1
        else:
            sys.exit(f"opzione sconosciuta: {k}")
    if not voce:
        sys.exit("serve --fatto, --decidere o --decidere-via")
    righe = leggi(RIGHE, {}) or {}
    r = righe.get(nome, {})
    ora = time.strftime("%Y-%m-%d %H:%M:%S")
    for k, v in voce.items():
        r[k] = v
        r[f"ora_{k}"] = ora
    righe[nome] = r
    tmp = RIGHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(righe, f, ensure_ascii=False, indent=1)
    os.replace(tmp, RIGHE)  # atomica: la Regia non legge mai un file a metà
    print(f"{nome}: " + ", ".join(f"{k} {'tolto' if not v else 'scritto'}" for k, v in voce.items()))


if __name__ == "__main__":
    main(sys.argv[1:])
