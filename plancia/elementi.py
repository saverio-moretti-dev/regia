#!/usr/bin/env python3
"""Elementi della Regia.

Testo, link, immagini, pdf, file e promemoria messi dal SUP in una zona fissa della pagina, con `sup.py elemento …`.
0 token: solo Python di base. Scrive SOLO in <dati>/elementi.json e <dati>/elementi/ (file copiati, cestino).

  Zone:  testata · sup · sospeso · token · sessione:NOME
  Tipi:  testo · link · immagine · pdf · file · promemoria

I file (immagine/pdf/file) si COPIANO in <dati>/elementi/<id>-<nome>: non spariscono se l'originale si sposta e si
aprono anche sul PC dell'ufficio; la pagina li chiede a GET /elemento/<id>. Togliere un elemento sposta il suo file in
<dati>/elementi/cestino/ (niente cancellazioni: si chiedono all'utente).
La riga «Fissati» di prima (fissati.json, `sup.py fissa`) resta com'è: i link della zona testata si uniscono a quella riga.
"""
import json, os, re, secrets, shutil, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.environ.get("PLANCIA_DATI", QUI)
FILE = os.path.join(DATI, "elementi.json")
CARTELLA = os.path.join(DATI, "elementi")

ZONE = ("testata", "sup", "sospeso", "token")  # + "sessione:NOME"
ZONE_NOMI = {"testata": "testata (riga Fissati in alto)", "sup": "box «Al superagente»", "sospeso": "riquadro «In sospeso»",
             "token": "scheda Token", "sessione:NOME": "sotto la riga della sessione NOME"}
TIPI = ("testo", "link", "immagine", "pdf", "file", "promemoria")
EST = {  # estensione → (tipo minimo, Content-Type). «file» = qualunque di questi, scaricato o aperto dal browser
    ".png": ("immagine", "image/png"), ".jpg": ("immagine", "image/jpeg"), ".jpeg": ("immagine", "image/jpeg"),
    ".gif": ("immagine", "image/gif"), ".webp": ("immagine", "image/webp"), ".svg": ("immagine", "image/svg+xml"),
    ".pdf": ("pdf", "application/pdf"), ".txt": ("file", "text/plain"), ".md": ("file", "text/plain"),
    ".csv": ("file", "text/plain"), ".json": ("file", "text/plain"), ".html": ("file", "text/plain"),
    ".mp4": ("file", "video/mp4"), ".mov": ("file", "video/quicktime"), ".mp3": ("file", "audio/mpeg"),
    ".wav": ("file", "audio/wav"), ".zip": ("file", "application/zip"), ".docx": ("file", "application/octet-stream"),
    ".xlsx": ("file", "application/octet-stream"), ".pptx": ("file", "application/octet-stream"),
}
MAX_FILE = int(os.environ.get("PLANCIA_ALLEGATO_MB", "25")) * 1_000_000
MAX_TESTO, MAX_TITOLO, MAX_VOCI = 2000, 80, 200
NOME_SESS = re.compile(r"^[A-Z0-9_-]{1,40}$")
ID_RE = re.compile(r"^[0-9a-f]{4}$")
QUANDO_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


class Errore(ValueError):
    """Dato non valido: nessuna scrittura."""


def ora():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def carica():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        return {"versione": 1, "voci": []}
    except ValueError:
        raise Errore("elementi.json rotto: correggerlo a mano prima di riscriverlo")
    if not isinstance(d, dict) or not isinstance(d.get("voci"), list):
        raise Errore("elementi.json senza «voci»: correggerlo a mano")
    return d


def salva(d):  # atomico: la pagina non legge mai un file a metà
    os.makedirs(DATI, exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, FILE)


def zona_ok(z):
    z = str(z or "").strip()
    if z in ZONE:
        return z
    if z.lower().startswith("sessione:") and NOME_SESS.match(z[9:].strip().upper()):
        return "sessione:" + z[9:].strip().upper()
    raise Errore(f"zona «{z}» non valida: " + ", ".join(list(ZONE) + ["sessione:NOME"]))


def nome_pulito(grezzo):
    base = os.path.basename(str(grezzo).replace("\\", "/"))
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base).lstrip("._-")[-60:] or "file"


def _testo(t, obbl=False, quale="testo", lung=MAX_TESTO):
    t = str(t or "").strip()
    if obbl and not t:
        raise Errore(f"{quale} vuoto")
    if len(t) > lung:
        raise Errore(f"{quale} oltre {lung} caratteri ({len(t)})")
    return t


def _nuovo_id(voci):
    usati = {v.get("id") for v in voci}
    while True:
        i = secrets.token_hex(2)
        if i not in usati:
            return i


def _riordina(voci, zona):
    for n, v in enumerate([v for v in voci if v["zona"] == zona], 1):
        v["pos"] = n


def aggiungi(tipo, zona, testo="", titolo="", url="", percorso="", quando="", ripeti="no", da="SUP"):
    """Controlla tutto PRIMA di scrivere; torna l'elemento creato. Errore → niente scritto, niente copiato."""
    if tipo not in TIPI:
        raise Errore(f"tipo «{tipo}» non valido: {', '.join(TIPI)}")
    zona = zona_ok(zona)
    d = carica()
    if len(d["voci"]) >= MAX_VOCI:
        raise Errore(f"già {MAX_VOCI} elementi: togliene qualcuno")
    v = {"id": _nuovo_id(d["voci"]), "tipo": tipo, "zona": zona, "titolo": _testo(titolo, quale="titolo", lung=MAX_TITOLO),
         "testo": _testo(testo, obbl=tipo in ("testo", "promemoria", "link"), quale="testo"), "creato": ora(), "da": da}
    if tipo == "link":
        url = str(url or "").strip()
        if not re.match(r"^https?://[^\s<>\"']+$", url):
            raise Errore("link: serve un URL http:// o https://")
        v["url"] = url
    if tipo == "promemoria":
        quando = str(quando or "").strip()
        if not QUANDO_RE.match(quando):
            raise Errore("promemoria: --quando \"AAAA-MM-GG HH:MM\"")
        try:
            time.strptime(quando, "%Y-%m-%d %H:%M")
        except ValueError:
            raise Errore(f"promemoria: data «{quando}» inesistente")
        if ripeti not in ("no", "giorno", "settimana"):
            raise Errore("--ripeti no|giorno|settimana")
        v.update(quando=quando, ripeti=ripeti)
    if tipo in ("immagine", "pdf", "file"):
        sorg = os.path.realpath(os.path.expanduser(str(percorso or "").strip()))
        if not percorso or not os.path.isfile(sorg):
            raise Errore(f"file «{percorso}» non trovato")
        est = os.path.splitext(sorg)[1].lower()
        if est not in EST:
            raise Errore(f"estensione «{est or '(nessuna)'}» non ammessa: {' '.join(sorted(EST))}")
        if tipo != "file" and EST[est][0] != tipo:
            raise Errore(f"«{os.path.basename(sorg)}» non è un/una {tipo} (è {EST[est][0]}): usa il tipo giusto o «file»")
        n = os.path.getsize(sorg)
        if not 0 < n <= MAX_FILE:
            raise Errore(f"file vuoto o oltre {MAX_FILE // 1_000_000} MB ({n} byte)")
        nome = f"{v['id']}-{nome_pulito(sorg)}"
        os.makedirs(CARTELLA, exist_ok=True)
        shutil.copyfile(sorg, os.path.join(CARTELLA, nome))
        v.update(file=nome, nome=os.path.basename(sorg), byte=n)
    d["voci"].append(v)
    _riordina(d["voci"], zona)
    salva(d)
    return v


def trova(d, i):
    i = str(i or "").strip().lower()
    for v in d["voci"]:
        if v["id"] == i:
            return v
    raise Errore(f"elemento «{i}» non c'è (elenco: sup.py elemento lista)")


def togli(i):
    d = carica()
    v = trova(d, i)
    d["voci"].remove(v)
    if v.get("file"):
        sorg = os.path.join(CARTELLA, v["file"])
        if os.path.isfile(sorg):
            os.makedirs(os.path.join(CARTELLA, "cestino"), exist_ok=True)
            os.replace(sorg, os.path.join(CARTELLA, "cestino", time.strftime("%Y%m%d-%H%M%S-") + v["file"]))
    _riordina(d["voci"], v["zona"])
    salva(d)
    return v


def sposta(i, zona, pos=None):
    zona = zona_ok(zona)
    d = carica()
    v = trova(d, i)
    vecchia = v["zona"]
    d["voci"].remove(v)
    v["zona"] = zona
    stessa = [x for x in d["voci"] if x["zona"] == zona]
    if pos is None or pos > len(stessa):
        d["voci"].append(v)
    else:
        pos = max(1, int(pos))
        d["voci"].insert(d["voci"].index(stessa[pos - 1]), v)
    _riordina(d["voci"], vecchia)
    _riordina(d["voci"], zona)
    salva(d)
    return v


def cambia(i, testo=None, titolo=None):
    d = carica()
    v = trova(d, i)
    if testo is not None:
        v["testo"] = _testo(testo, obbl=v["tipo"] in ("testo", "promemoria", "link"))
    if titolo is not None:
        v["titolo"] = _testo(titolo, quale="titolo", lung=MAX_TITOLO)
    v["cambiato"] = ora()
    salva(d)
    return v


def per_pagina(adesso=None):
    """Campo «elementi» di /api/stato: solo ciò che serve alla pagina, mai percorsi del disco.
    Promemoria: «visibile» da «quando» in poi (ora del Mac, calcolata qui: niente fusi nel browser)."""
    try:
        voci = carica()["voci"]
    except Errore as e:
        return {"errore": str(e), "voci": []}
    adesso = adesso or time.strftime("%Y-%m-%d %H:%M")
    fuori = []
    for v in voci:
        if not isinstance(v, dict) or v.get("tipo") not in TIPI or not v.get("id"):
            continue
        x = {k: v.get(k) for k in ("id", "tipo", "zona", "titolo", "testo", "url", "nome", "byte", "quando", "ripeti", "pos")
             if v.get(k) not in (None, "")}
        if v.get("file"):
            x["src"] = f"/elemento/{v['id']}"
        if v["tipo"] == "promemoria":
            x["visibile"] = str(v.get("quando", "")) <= adesso
        fuori.append(x)
    fuori.sort(key=lambda x: (x.get("zona", ""), x.get("pos") or 0))
    return {"voci": fuori}


def file_di(i):
    """Per GET /elemento/<id>: (percorso, Content-Type, nome) oppure None. Solo dentro <dati>/elementi/."""
    if not ID_RE.match(str(i)):
        return None
    try:
        v = next((v for v in carica()["voci"] if v.get("id") == i and v.get("file")), None)
    except Errore:
        return None
    if not v:
        return None
    p = os.path.realpath(os.path.join(CARTELLA, v["file"]))
    if not p.startswith(os.path.realpath(CARTELLA) + os.sep) or not os.path.isfile(p):
        return None
    tipo = EST.get(os.path.splitext(p)[1].lower(), (None, "application/octet-stream"))[1]
    return p, tipo, v.get("nome") or v["file"]


def riga(v):
    cosa = v.get("testo") or v.get("nome") or v.get("url") or ""
    cosa = re.sub(r"\s+", " ", cosa)
    extra = f" · quando {v['quando']}" + (f" ripeti {v['ripeti']}" if v.get("ripeti", "no") != "no" else "") if v.get("tipo") == "promemoria" else ""
    return f"{v['id']}  {v['tipo']:<10} {v['zona']:<18} {v.get('pos', '')}. {(v.get('titolo') + ': ') if v.get('titolo') else ''}{cosa[:90]}{extra}"


def occupato():
    tot = 0
    for radice in (CARTELLA, os.path.join(DATI, "allegati")):
        for r, _, fs in os.walk(radice):
            tot += sum(os.path.getsize(os.path.join(r, f)) for f in fs)
    return tot


USO = """uso: sup.py elemento …
  zone                                        zone valide
  lista [--zona Z]
  testo  --zona Z "testo" [--titolo T]
  link   --zona Z "Testo" URL
  immagine|pdf|file --zona Z PERCORSO [--titolo T] [--testo "didascalia"]
  promemoria --zona Z --quando "AAAA-MM-GG HH:MM" [--ripeti giorno|settimana] "testo"
  sposta <id> <zona> [--pos N]
  cambia <id> ["testo"] [--titolo T]
  togli <id>                                  (il file va in elementi/cestino/)
  opzione --no-verifica: niente controllo automatico dopo la modifica"""


def _opzioni(a):
    o, resto, i = {}, [], 0
    while i < len(a):
        if a[i] == "--no-verifica":
            i += 1
        elif a[i].startswith("--"):
            if i + 1 >= len(a):
                raise Errore(f"{a[i]} senza valore")
            o[a[i][2:]] = a[i + 1]
            i += 2
        else:
            resto.append(a[i])
            i += 1
    return o, resto


def cli(a):
    """`sup.py elemento …`: torna (codice, testo, id da verificare o None)."""
    if not a:
        return 1, USO, None
    cmd, o, r = a[0], *_opzioni(a[1:])
    if cmd == "zone":
        return 0, "\n".join(f"{k:<16} {v}" for k, v in ZONE_NOMI.items()), None
    if cmd == "lista":
        voci = carica()["voci"]
        if o.get("zona"):
            voci = [v for v in voci if v["zona"] == zona_ok(o["zona"])]
        voci = sorted(voci, key=lambda v: (v["zona"], v.get("pos") or 0))
        mb = occupato() / 1_000_000
        return 0, "\n".join([riga(v) for v in voci] + [f"({len(voci)} elementi · file di elementi+allegati {mb:.1f} MB)"]), None
    if cmd in ("testo", "promemoria"):
        v = aggiungi(cmd, o.get("zona"), testo=" ".join(r), titolo=o.get("titolo", ""), quando=o.get("quando", ""),
                     ripeti=o.get("ripeti", "no"))
    elif cmd == "link":
        if len(r) != 2:
            raise Errore('uso: sup.py elemento link --zona Z "Testo" https://…')
        v = aggiungi("link", o.get("zona"), testo=r[0], url=r[1], titolo=o.get("titolo", ""))
    elif cmd in ("immagine", "pdf", "file"):
        if len(r) != 1:
            raise Errore(f"uso: sup.py elemento {cmd} --zona Z PERCORSO (un file, fra virgolette se ha spazi)")
        v = aggiungi(cmd, o.get("zona"), percorso=r[0], titolo=o.get("titolo", ""), testo=o.get("testo", ""))
    elif cmd == "sposta":
        if len(r) != 2:
            raise Errore("uso: sup.py elemento sposta <id> <zona> [--pos N]")
        if "pos" in o and not o["pos"].isdigit():
            raise Errore("--pos vuole un numero")
        v = sposta(r[0], r[1], int(o["pos"]) if "pos" in o else None)
    elif cmd == "cambia":
        if not r or (len(r) == 1 and "titolo" not in o):
            raise Errore('uso: sup.py elemento cambia <id> ["testo"] [--titolo T]')
        v = cambia(r[0], " ".join(r[1:]) if len(r) > 1 else None, o.get("titolo"))
    elif cmd == "togli":
        if len(r) != 1:
            raise Errore("uso: sup.py elemento togli <id>")
        v = togli(r[0])
        return 0, f"tolto {riga(v)}", None
    else:
        return 1, USO, None
    return 0, riga(v), v["id"]


if __name__ == "__main__":
    try:
        c, t, _ = cli(sys.argv[1:])
    except Errore as e:
        c, t = 1, f"ERRORE: {e}"
    print(t, file=sys.stderr if c else sys.stdout)
    sys.exit(c)
