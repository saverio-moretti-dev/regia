#!/usr/bin/env python3
"""Controllo del risultato prima della consegna. 0 token: Python di base + Chrome senza finestra. Non scrive niente fuori da <dati>/verifiche/.

  python3 plancia/verifica.py <id> [--porta 8765] [--senza-schermata]
  python3 plancia/verifica.py --tutti [--porta 8765] [--senza-schermata]

Per ogni elemento:
  1. DATI    /api/stato del server acceso: l'elemento c'è, nella zona giusta; se ha un file, /elemento/<id> risponde 200
             col tipo atteso.
  2. PAGINA  Chrome --dump-dom (la pagina vera, JavaScript eseguito): nel DOM c'è data-el="<id>" DENTRO il contenitore
             data-zona="<zona>", senza antenati nascosti; immagini: data-caricata="1" (scritto da app.js all'onload).
             Promemoria non ancora visibili: devono NON esserci. Sessione non viva: l'elemento non può esserci (avviso).
  3. SCHERMATA Chrome --screenshot 1280×2400 px, tema scuro e chiaro, con ?evidenzia=<id> (la pagina lo contorna;
             nella scheda Token la apre) → <dati>/verifiche/AAAAMMGG-HHMMSS-<id>-{scuro,chiaro}.png
Esito: righe OK/KO, codice 0 = tutto ok · 1 = qualcosa KO · 2 = non verificabile (server spento).
Chrome cercato nei percorsi di Mac, Windows e Linux; se manca, solo il punto 1 e un avviso (in ufficio non blocca).
Limite: sotto ~500 px Chrome senza finestra non si stringe: il telefono si prova nel collaudo, non qui.
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elementi  # noqa: E402

CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
]


def trova_chrome():
    for c in CHROME:
        if os.path.isfile(c):
            return c
    for n in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def get(porta, percorso, json_=True):
    req = urllib.request.Request(f"http://127.0.0.1:{porta}{percorso}", headers={"Host": f"127.0.0.1:{porta}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        corpo = r.read()
        return (json.loads(corpo) if json_ else corpo), r.status, r.headers.get("Content-Type", "")


class Dom(HTMLParser):
    """Per ogni data-el: zona dell'antenato data-zona più vicino, se un antenato è nascosto, se l'immagine è caricata."""
    VUOTI = {"img", "br", "hr", "input", "meta", "link", "source", "area", "base", "col", "embed", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.pila, self.el = [], {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        # una scheda (Sessioni/Token) chiusa non è un difetto: si vede aprendola (?evidenzia la apre per la schermata)
        nascosto = ("hidden" in a and a.get("role") != "tabpanel") or "display:none" in (a.get("style") or "").replace(" ", "")
        voce = {"tag": tag, "zona": a.get("data-zona"), "nascosto": nascosto, "el": a.get("data-el")}
        zona = next((x["zona"] for x in reversed(self.pila) if x["zona"]), None)
        if voce["el"]:
            self.el[voce["el"]] = {"zona": zona, "nascosto": nascosto or any(x["nascosto"] for x in self.pila), "img": None}
        if tag == "img":
            padre = next((x["el"] for x in reversed(self.pila) if x["el"]), None)
            if padre in self.el:
                self.el[padre]["img"] = a.get("data-caricata") == "1"
        if tag not in self.VUOTI:
            self.pila.append(voce)

    def handle_endtag(self, tag):
        for i in range(len(self.pila) - 1, -1, -1):
            if self.pila[i]["tag"] == tag:
                del self.pila[i:]
                break


def chrome(exe, url, extra, timeout=40):
    with tempfile.TemporaryDirectory(prefix="regia-verifica-") as prof:  # profilo usa e getta: mai quello dell'utente
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={prof}", "--hide-scrollbars", "--virtual-time-budget=8000"] + extra + [url]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def controlla(porta, ids, schermata=True):
    righe, ko = [], False

    def ok(cosa, bene, nota=""):
        nonlocal ko
        ko |= not bene
        righe.append(f"{'OK' if bene else 'KO'}  {cosa}{(' — ' + nota) if nota else ''}")

    try:
        stato, _, _ = get(porta, "/api/stato")
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 2, [f"NON VERIFICATO: Regia su 127.0.0.1:{porta} non risponde ({e})"]
    voci = {v["id"]: v for v in (stato.get("elementi") or {}).get("voci", [])}
    vive = {s.get("nome") for s in stato.get("sessioni", []) if isinstance(s, dict)}
    if ids == ["--tutti"]:
        ids = sorted(voci)
        if not ids:
            return 0, ["(nessun elemento)"]
    attesi = {}
    for i in ids:
        v = voci.get(i)
        ok(f"{i} nei dati", bool(v), "" if v else "non c'è in /api/stato (elementi.json?)")
        if not v:
            continue
        attesi[i] = v
        if v.get("src"):
            try:
                _, st, ct = get(porta, v["src"], json_=False)
                atteso = elementi.EST.get(os.path.splitext(v.get("nome", ""))[1].lower(), (None, ""))[1]
                ok(f"{i} file {v['src']}", st == 200 and ct.split(";")[0] == atteso, f"{st} {ct}")
            except (urllib.error.URLError, OSError) as e:
                ok(f"{i} file {v['src']}", False, str(e))
    exe = trova_chrome()
    if not exe:
        righe.append("AVVISO  Chrome non trovato: controllo della pagina e schermate saltati")
        return (1 if ko else 3), righe
    if attesi:
        r = chrome(exe, f"http://127.0.0.1:{porta}/", ["--dump-dom", "--window-size=1280,900"])
        dom = Dom()
        dom.feed(r.stdout)
        if not r.stdout.strip():
            ok("pagina caricata da Chrome", False, (r.stderr or "")[-200:])
        for i, v in attesi.items():
            d, zona = dom.el.get(i), v["zona"]
            if v["tipo"] == "promemoria" and not v.get("visibile"):
                ok(f"{i} promemoria non ancora visibile (da {v.get('quando')})", d is None)
                continue
            if zona.startswith("sessione:") and zona[9:] not in vive:
                righe.append(f"AVVISO  {i}: la sessione {zona[9:]} non è viva → l'elemento resta in attesa, non si vede")
                ok(f"{i} non mostrato (sessione non viva)", d is None)
                continue
            ok(f"{i} nella pagina", bool(d))
            if not d:
                continue
            ok(f"{i} nella zona {zona}", d["zona"] == zona, f"trovato in {d['zona']}")
            ok(f"{i} visibile", not d["nascosto"])
            if v["tipo"] == "immagine":
                ok(f"{i} immagine caricata", d["img"] is True)
    if schermata and attesi and not ko:
        cart = os.path.join(elementi.DATI, "verifiche")
        os.makedirs(cart, exist_ok=True)
        base = time.strftime("%Y%m%d-%H%M%S")
        primo = next(iter(attesi))
        for tema, n in (("scuro", 0), ("chiaro", 1)):
            png = os.path.join(cart, f"{base}-{primo if len(attesi) == 1 else 'tutti'}-{tema}.png")
            # pagina alta e niente scorrimento (scorri=0): in Chrome senza finestra lo scorrimento lascia una fascia vuota
            chrome(exe, f"http://127.0.0.1:{porta}/?evidenzia={primo if len(attesi) == 1 else ''}&scorri=0",
                   [f"--screenshot={png}", "--window-size=1280,2400", f"--blink-settings=preferredColorScheme={n}"])
            ok(f"schermata {tema}", os.path.isfile(png) and os.path.getsize(png) > 5000, png)
    return (1 if ko else 0), righe


def main(a):
    porta = int(os.environ.get("PLANCIA_PORTA", "8765"))
    schermata, ids, i = True, [], 0
    while i < len(a):
        if a[i] == "--porta" and i + 1 < len(a):
            porta, i = int(a[i + 1]), i + 2
            continue
        if a[i] == "--senza-schermata":
            schermata = False
        else:
            ids.append(a[i].lower() if a[i] != "--tutti" else a[i])
        i += 1
    if not ids:
        print(__doc__.split("\n\n")[1])
        return 1
    codice, righe = controlla(porta, ids, schermata)
    print("\n".join(righe))
    print({0: "VERIFICATO", 1: "NON VA: non consegnare", 2: "NON VERIFICATO",
           3: "VERIFICATO SOLO NEI DATI (pagina non controllata: manca Chrome)"}[codice])
    return 0 if codice == 3 else codice


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
