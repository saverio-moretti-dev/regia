#!/usr/bin/env python3
"""Impostazioni locali della Regia, senza percorsi personali nel codice.

Ordine: variabile d'ambiente → plancia/locale.json (facoltativo, git-ignorato, resta sul computer) → valore predefinito.
Esempio di locale.json (solo le chiavi che servono):
  {"PLANCIA_CTM": "~/codice/dont-waste-your-token",
   "PLANCIA_PASSAGGI": "~/codice/superagent-method/tools/passaggi.py",
   "note_origini": {"chrome-extension://<id di 32 lettere>": "NOME-SESSIONE"},
   "inizio_lavori": "testo mandato al SUP dal bottone Inizio lavori"}
Predefiniti: le repo compagne messe ACCANTO alla cartella della Regia (…/regia, …/dont-waste-your-token, …/superagent-method).
"""
import json, os

QUI = os.path.dirname(os.path.abspath(__file__))
ACCANTO = os.path.dirname(os.path.dirname(QUI))  # cartella che contiene la Regia
FILE = os.path.join(QUI, "locale.json")


def _locale():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def valore(chiave, predefinito=None):
    if os.environ.get(chiave):
        return os.environ[chiave]
    v = _locale().get(chiave)
    if isinstance(v, str):
        return os.path.expanduser(v) if v else predefinito
    return predefinito if v is None else v


def percorso(chiave, *accanto):
    """Percorso di una repo compagna: impostato, altrimenti accanto alla Regia."""
    return os.path.expanduser(valore(chiave, os.path.join(ACCANTO, *accanto)))
