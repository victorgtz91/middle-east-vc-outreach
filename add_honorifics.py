import os, time, re, requests, pandas as pd

INPUT_FILE  = "857-vc-funds-in-middle-east.xlsx"
SHEET_NAME  = 0
OUTPUT_FILE = "857-vc-funds-with-names.xlsx"
REVIEW_FILE = "857-vc-funds-with-names_needs_review.xlsx"

GENDERIZE_KEY = os.getenv("GENDERIZE_KEY")  # export GENDERIZE_KEY="tu_api_key"

def split_name(full_name: str):
    if pd.isna(full_name) or not str(full_name).strip():
        return "", ""
    name = re.sub(r",.*$", "", str(full_name)).strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])

def honorific_from_title(title: str) -> str:
    if not title: return ""
    t = title.lower()
    if re.search(r"\bdr\b|\bdoctor\b", t): return "Dr."
    if re.search(r"\bmr\b", t):            return "Mr."
    if re.search(r"\bms\b|\bmrs\b|\bmadam\b", t): return "Ms."
    if re.search(r"\bsheikh\b|\bshaikh\b|\bh\.e\.\b", t): return ""  # revisar manualmente
    return ""

def genderize(first_name: str) -> str:
    if not GENDERIZE_KEY or not first_name:
        return ""
    try:
        r = requests.get(
            "https://api.genderize.io",
            params={"name": first_name, "apikey": GENDERIZE_KEY},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        gender = (data or {}).get("gender")
        prob = (data or {}).get("probability", 0)
        if gender and float(prob) >= 0.85:  # umbral conservador
            return "Ms." if gender == "female" else "Mr."
    except Exception:
        pass
    return ""

def build_salutation(honorific, first_name, last_name, full_name):
    if honorific and last_name:
        return f"Dear {honorific} {last_name},"
    # Fallbacks respetuosos si no hay honorific claro
    if last_name:
        return f"Dear {last_name},"
    if full_name:
        return f"Dear {full_name},"
    return "Dear Sir or Madam,"

def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    # detectar columna de título si existe
    title_col = None
    for c in df.columns:
        if str(c).strip().lower() in {"primary contact title","contact title","title"}:
            title_col = c; break

    df["First Name"], df["Last Name"] = zip(*df["Primary Contact"].apply(split_name))
    # 1) por título
    df["Honorific"] = df[title_col].apply(honorific_from_title) if title_col else ""
    # 2) por Genderize en los que siguen vacíos
    if GENDERIZE_KEY:
        for i, row in df[df["Honorific"] == ""].iterrows():
            h = genderize(row["First Name"])
            if h:
                df.at[i, "Honorific"] = h
            time.sleep(0.25)  # cortesía para rate limit

    # salutation final
    df["Salutation"] = df.apply(
        lambda r: build_salutation(r["Honorific"], r["First Name"], r["Last Name"], r["Primary Contact"]),
        axis=1
    )

    # métricas
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

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Archivo generado: {OUTPUT_FILE}")

    needs_review = df[df["Honorific"] == ""].copy()
    if not needs_review.empty:
        needs_review.to_excel(REVIEW_FILE, index=False)
        print(f"⚠️ Casos a revisar exportados a: {REVIEW_FILE}")
    else:
        print("✅ No hay casos pendientes de revisión.")

if __name__ == "__main__":
    main()
