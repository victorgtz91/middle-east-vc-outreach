import os
import re
import time
import json
import pandas as pd
import requests

INPUT_FILE  = "857-vc-funds-with-country.xlsx"
SHEET_NAME  = 0
OUTPUT_FILE = "857-vc-funds-with-gender.xlsx"
CACHE_FILE  = "genderize_cache.json"

GENDERIZE_KEY = os.getenv("GENDERIZE_KEY")  # export GENDERIZE_KEY="..."
GENDERIZE_URL = "https://api.genderize.io"

# Probabilidad mínima para aceptar el género inferido
PROB_THRESHOLD = 0.85
# Pausa entre requests para mantener buen comportamiento
SLEEP_SECONDS = 0.25

# Ciertos títulos regionales mejor no mapear a Mr./Ms. automáticamente
REGIONAL_TITLES = re.compile(r"\b(sheikh|shaikh|h\.e\.|his excellency|her excellency)\b", re.I)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def split_name(full_name: str):
    if not isinstance(full_name, str) or not full_name.strip():
        return "", ""
    name = re.sub(r",.*$", "", full_name).strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])

def honorific_from_title(title: str) -> str:
    if not isinstance(title, str):
        return ""
    t = title.lower()
    if re.search(r"\bdr\b|doctor", t):
        return "Dr."
    if REGIONAL_TITLES.search(t):
        # Dejar vacío para tratar manualmente
        return ""
    if re.search(r"\bmr\b", t):
        return "Mr."
    if re.search(r"\bms\b|\bmrs\b|\bmadam\b|\bmiss\b", t):
        return "Ms."
    return ""

def genderize_name(first_name: str, cache: dict) -> tuple[str, float]:
    """
    Devuelve (honorific_sugerido, probabilidad) a partir de Genderize.
    honorific_sugerido: 'Mr.' / 'Ms.' / '' si no confiable o sin key.
    """
    if not first_name:
        return "", 0.0
    key = first_name.strip().lower()
    if key in cache:
        g = cache[key]
        gender = g.get("gender")
        prob = float(g.get("probability") or 0)
    else:
        if not GENDERIZE_KEY:
            return "", 0.0
        try:
            r = requests.get(GENDERIZE_URL, params={"name": first_name, "apikey": GENDERIZE_KEY}, timeout=10)
            r.raise_for_status()
            data = r.json() or {}
            gender = data.get("gender")
            prob = float(data.get("probability") or 0)
            cache[key] = {"gender": gender, "probability": prob}
            time.sleep(SLEEP_SECONDS)
        except Exception:
            return "", 0.0

    if gender and prob >= PROB_THRESHOLD:
        return ("Ms." if gender == "female" else "Mr."), prob
    return "", prob

def build_salutation(honorific, first_name, last_name, full_name):
    # Preferimos: Dear {Honorific} {Last Name},
    if honorific and last_name:
        return f"Dear {honorific} {last_name},"
    # Si no hay honorific, pero sí apellido:
    if last_name:
        return f"Dear {last_name},"
    # Si solo tenemos el nombre completo:
    if full_name:
        return f"Dear {full_name},"
    return "Dear Sir or Madam,"

def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    # Detectar columna de título si existe
    title_col = None
    for c in df.columns:
        if str(c).strip().lower() in {"primary contact title", "contact title", "title"}:
            title_col = c; break

    # Asegurar First/Last Name
    if "First Name" not in df.columns or "Last Name" not in df.columns:
        first_last = df["Primary Contact"].apply(split_name)
        df["First Name"] = [fl[0] for fl in first_last]
        df["Last Name"]  = [fl[1] for fl in first_last]

    # Intento 1: por título
    honorifics = []
    for _, row in df.iterrows():
        title = row[title_col] if title_col else ""
        honorifics.append(honorific_from_title(title))
    df["Honorific"] = honorifics

    # Intento 2: Genderize para los vacíos
    cache = load_cache()
    genders, probs = [], []
    for i, row in df.iterrows():
        if df.at[i, "Honorific"] == "":
            h, p = genderize_name(row["First Name"], cache)
            if h:
                df.at[i, "Honorific"] = h
            genders.append(h)
            probs.append(p)
        else:
            genders.append("")  # ya definido por título
            probs.append(1.0 if df.at[i, "Honorific"] in ("Mr.","Ms.","Dr.") else 0.0)
    save_cache(cache)

    # Métricas
    total = len(df)
    ms_cnt  = (df["Honorific"] == "Ms.").sum()
    mr_cnt  = (df["Honorific"] == "Mr.").sum()
    dr_cnt  = (df["Honorific"] == "Dr.").sum()
    unk_cnt = (df["Honorific"] == "").sum()

    print("=== Honorific assignment summary ===")
    print(f"Total contacts: {total}")
    print(f"Ms.: {ms_cnt}")
    print(f"Mr.: {mr_cnt}")
    print(f"Dr.: {dr_cnt}")
    print(f"Unknown / needs review: {unk_cnt}")

    # Salutation final
    df["Salutation"] = df.apply(
        lambda r: build_salutation(r["Honorific"], r["First Name"], r["Last Name"], r["Primary Contact"]),
        axis=1
    )

    # Guardar
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Archivo generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
