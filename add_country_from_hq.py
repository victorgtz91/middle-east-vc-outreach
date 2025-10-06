import re
import unicodedata
import pandas as pd
from rapidfuzz import process, fuzz
import country_converter as coco

INPUT_FILE  = "857-vc-funds-with-names.xlsx"
SHEET_NAME  = 0
OUTPUT_FILE = "857-vc-funds-with-country.xlsx"
REVIEW_FILE = "857-vc-funds-with-country_needs_review.xlsx"

# 1) Sinónimos / variantes frecuentes -> nombre canónico en inglés
COUNTRY_SYNONYMS = {
    # MENA
    "uae": "United Arab Emirates", "u.a.e.": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates", "emiratos arabes unidos": "United Arab Emirates",
    "emiratos árabes unidos": "United Arab Emirates", "dubai, uae": "United Arab Emirates",
    "ksa": "Saudi Arabia", "kingdom of saudi arabia": "Saudi Arabia", "saudi": "Saudi Arabia",
    "qatar": "Qatar", "doha, qatar": "Qatar",
    "bahrain": "Bahrain", "manama, bahrain": "Bahrain",
    "oman": "Oman", "muscat, oman": "Oman",
    "kuwait": "Kuwait", "kuwait city, kuwait": "Kuwait",
    "egypt": "Egypt", "cairo, egypt": "Egypt",
    "jordan": "Jordan", "amman, jordan": "Jordan",
    "lebanon": "Lebanon", "beirut, lebanon": "Lebanon",
    "turkey": "Turkey", "türkiye": "Turkey", "istanbul, turkey": "Turkey",
    "israel": "Israel", "tel aviv, israel": "Israel",

    # Otros comunes
    "usa": "United States", "u.s.a.": "United States", "us": "United States", "u.s.": "United States",
    "united states": "United States", "united states of america": "United States",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "united kingdom": "United Kingdom",
    "england": "United Kingdom", "scotland": "United Kingdom", "wales": "United Kingdom",
    "hong kong": "Hong Kong", "hong kong sar": "Hong Kong",
    "china": "China", "prc": "China",
    "india": "India",
    "mexico": "Mexico", "méxico": "Mexico",
    "spain": "Spain", "españa": "Spain",
    "france": "France", "germany": "Germany",
    "switzerland": "Switzerland", "swiss": "Switzerland",
    "netherlands": "Netherlands",
    "singapore": "Singapore",
    "canada": "Canada",
    "brazil": "Brazil",
    "uae-dubai": "United Arab Emirates", "dubai": "United Arab Emirates",
    "abu dhabi": "United Arab Emirates", "sharjah": "United Arab Emirates",
    "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia", "dammam": "Saudi Arabia",
    "doha": "Qatar", "manama": "Bahrain", "muscat": "Oman", "kuwait city": "Kuwait",
    "cairo": "Egypt", "amman": "Jordan", "beirut": "Lebanon", "istanbul": "Turkey",
    "tel aviv": "Israel", "jerusalem": "Israel",
}

# 2) Mapa explícito de ciudades -> país (sobre todo MENA)
CITY_TO_COUNTRY = {
    "dubai": "United Arab Emirates", "abu dhabi": "United Arab Emirates", "sharjah": "United Arab Emirates",
    "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia", "dammam": "Saudi Arabia", "khobar": "Saudi Arabia",
    "doha": "Qatar", "manama": "Bahrain", "muscat": "Oman", "kuwait city": "Kuwait",
    "cairo": "Egypt", "giza": "Egypt", "alexandria": "Egypt",
    "amman": "Jordan", "beirut": "Lebanon",
    "istanbul": "Turkey", "ankara": "Turkey",
    "tel aviv": "Israel", "jerusalem": "Israel", "haifa": "Israel",
    # global frecuentes
    "london": "United Kingdom", "paris": "France", "madrid": "Spain",
    "barcelona": "Spain", "berlin": "Germany", "munich": "Germany",
    "zurich": "Switzerland", "geneva": "Switzerland",
    "amsterdam": "Netherlands",
    "new york": "United States", "san francisco": "United States", "boston": "United States",
    "miami": "United States", "los angeles": "United States", "austin": "United States",
    "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "mexico city": "Mexico", "cdmx": "Mexico", "guadalajara": "Mexico", "monterrey": "Mexico",
    "singapore": "Singapore", "hong kong": "Hong Kong"
}

# Lista de países canónicos para fuzzy matching
cc = coco.CountryConverter()
CANON_COUNTRIES = cc.data['name_short'].dropna().tolist()

def normalize(s: str) -> str:
    if not isinstance(s, str) or not s.strip():
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.replace("/", ",").replace("|", ",").replace(";", ",")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def try_synonyms(norm: str):
    # intenta por segmentos separados por coma
    parts = [p.strip() for p in norm.split(",") if p.strip()]
    # prueba cada parte de derecha a izquierda (lo último suele ser país)
    for token in reversed(parts):
        if token in COUNTRY_SYNONYMS:
            return COUNTRY_SYNONYMS[token]
    # prueba string completo
    return COUNTRY_SYNONYMS.get(norm, None)

def try_city_map(norm: str):
    parts = [p.strip() for p in norm.split(",") if p.strip()]
    for token in parts:
        if token in CITY_TO_COUNTRY:
            return CITY_TO_COUNTRY[token]
    # prueba palabras sueltas
    words = norm.split()
    for w in words:
        if w in CITY_TO_COUNTRY:
            return CITY_TO_COUNTRY[w]
    return None

def try_fuzzy(norm: str, score_cutoff=90):
    # intenta sobre cada segmento separado por coma
    parts = [p.strip() for p in norm.split(",") if p.strip()]
    for token in reversed(parts):
        match = process.extractOne(token, CANON_COUNTRIES, scorer=fuzz.WRatio, score_cutoff=score_cutoff)
        if match:
            return match[0]
    # como último recurso, fuzzy sobre toda la cadena
    match = process.extractOne(norm, CANON_COUNTRIES, scorer=fuzz.WRatio, score_cutoff=94)
    return match[0] if match else None

def resolve_country(hq_value: str):
    norm = normalize(hq_value)
    if not norm:
        return ""
    # Capa 1: sinónimos/variantes
    c = try_synonyms(norm)
    if c:
        return c
    # Capa 2: ciudades conocidas
    c = try_city_map(norm)
    if c:
        return c
    # Capa 3: fuzzy contra lista de países
    c = try_fuzzy(norm)
    if c:
        return c
    return ""  # revisar manual

def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    # verificación de columna
    hq_col = None
    for c in df.columns:
        if str(c).strip().lower() in {"hq location", "hq", "headquarters", "headquarter location"}:
            hq_col = c
            break
    if hq_col is None:
        raise ValueError("No encuentro la columna 'HQ Location' (o equivalente) en el Excel.")

    df["country"] = df[hq_col].apply(resolve_country)

    # métricas
    total = len(df)
    resolved = (df["country"] != "").sum()
    unresolved = total - resolved

    print("=== Country extraction summary ===")
    print(f"Total rows: {total}")
    print(f"Resolved countries: {resolved}")
    print(f"Needs review (empty): {unresolved}")

    # exportar
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Archivo generado: {OUTPUT_FILE}")

    if unresolved > 0:
        needs = df[df["country"] == ""].copy()
        needs.to_excel(REVIEW_FILE, index=False)
        print(f"⚠️ Casos a revisar exportados a: {REVIEW_FILE}")

if __name__ == "__main__":
    main()
