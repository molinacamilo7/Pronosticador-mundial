#!/usr/bin/env python3
"""
Script que corre automáticamente via GitHub Actions cada hora.
Descarga resultados + plantillas de openfootball y actualiza el HTML.
"""
import json, urllib.request, re, sys
from datetime import datetime

WC_URL    = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
SQUADS_URL= "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.squads.json"
HTML_FILE = "mundial2026_predictor.html"

NAME_MAP = {
    "Mexico":"México","South Korea":"Corea del Sur","South Africa":"Sudáfrica",
    "Czech Republic":"Czechia","Czechia":"Czechia","Canada":"Canadá",
    "Switzerland":"Suiza","Bosnia & Herzegovina":"Bosnia-Herzegovina",
    "Bosnia and Herzegovina":"Bosnia-Herzegovina","Brazil":"Brasil",
    "Morocco":"Marruecos","Scotland":"Escocia","Haiti":"Haití",
    "USA":"USA","United States":"USA","Paraguay":"Paraguay",
    "Australia":"Australia","Turkey":"Turquía","Germany":"Alemania",
    "Ecuador":"Ecuador","Ivory Coast":"Costa de Marfil","Cote d'Ivoire":"Costa de Marfil",
    "Curacao":"Curazao","Curaçao":"Curazao","Netherlands":"Países Bajos",
    "Japan":"Japón","Tunisia":"Túnez","Sweden":"Suecia","Belgium":"Bélgica",
    "Iran":"Irán","Egypt":"Egipto","New Zealand":"Nueva Zelanda","Spain":"España",
    "Uruguay":"Uruguay","Saudi Arabia":"Arabia Saudita","Cape Verde":"Cabo Verde",
    "France":"Francia","Senegal":"Senegal","Norway":"Noruega","Iraq":"Irak",
    "Argentina":"Argentina","Austria":"Austria","Algeria":"Argelia","Jordan":"Jordania",
    "Portugal":"Portugal","Colombia":"Colombia","Uzbekistan":"Uzbekistán",
    "DR Congo":"RD Congo","DRC":"RD Congo","England":"Inglaterra",
    "Croatia":"Croacia","Panama":"Panamá","Ghana":"Ghana",
    "Bosnia & Herzegovina":"Bosnia-Herzegovina",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"WorldCupUpdater/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def norm(name):
    if isinstance(name, dict): name = name.get("name","")
    return NAME_MAP.get(name, name)

def get_results(data):
    results = []
    for m in data.get("matches", []):
        sc = None
        if m.get("score"):
            sc = m["score"].get("ft") or m["score"].get("et")
        if not sc: continue
        try:
            gH, gA = int(sc[0]), int(sc[1])
        except:
            continue
        home = norm(m.get("team1",""))
        away = norm(m.get("team2",""))
        if not home or not away: continue
        grp = m.get("group","?").replace("Group ","")
        results.append({
            "home": home, "away": away,
            "gH": gH, "gA": gA,
            "grp": grp,
            "date": m.get("date",""),
            "round": m.get("round","")
        })
    return results

def get_squads(data):
    compact = []
    for t in data:
        compact.append({
            "name": t["name"],
            "group": t.get("group",""),
            "players": [
                {"n": p["number"], "p": p["pos"], "nm": p["name"], "d": p.get("date_of_birth","")}
                for p in t.get("players", [])
            ]
        })
    return compact

def update_html(results, squads, last_update):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace liveMatches
    results_json = json.dumps(results, ensure_ascii=False, separators=(",",":"))
    html = re.sub(
        r'let liveMatches=\[.*?\];',
        f'let liveMatches={results_json};',
        html, flags=re.DOTALL
    )

    # Replace squads
    squads_json = json.dumps(squads, ensure_ascii=False, separators=(",",":"))
    html = re.sub(
        r'const SQUADS_RAW=\[.*?\];',
        f'const SQUADS_RAW={squads_json};',
        html, flags=re.DOTALL
    )

    # Replace last update timestamp in chip
    html = re.sub(
        r"setChip\('results','ok',`✓ \$\{liveMatches\.length\}.*?`\);",
        f"setChip('results','ok',`✓ ${{liveMatches.length}} partido(s) · {last_update}`);",
        html
    )

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ HTML actualizado: {len(results)} resultados, {len(squads)} equipos, {last_update}")

def main():
    print("Descargando resultados...")
    wc_data   = fetch(WC_URL)
    print("Descargando plantillas...")
    sq_data   = fetch(SQUADS_URL)

    results = get_results(wc_data)
    squads  = get_squads(sq_data)
    last_update = datetime.utcnow().strftime("%d %b %H:%M UTC")

    print(f"Resultados encontrados: {len(results)}")
    print(f"Equipos con plantilla: {len(squads)}")

    update_html(results, squads, last_update)

if __name__ == "__main__":
    main()
