import os
import random
import pandas as pd


# Inputs/Outputs
INPUT_FILE = "857-vc-funds-with-gender.xlsx"
SHEET_NAME = 0
OUTPUT_FILE = "857-vc-funds-with-email-template.xlsx"


# Constants
LANDING_PAGE = "https://zarcoideas.com"


# Email template
SUBJECT_TEMPLATE = "CFA Charterholder | Exploring collaboration with {{fund_name}}"

BODY_TEMPLATE = (
    "{{honorific}} {{last_name}},\n\n"
    "I'm Victor G. Zarco, CFA Bs. in Actuarial Science and Financial Economist.  \n"
    "I came across your leadership in {{fund_name}}, particularly {{person_hook_sentence}}.\n\n"
    "I'm moving to the Middle East soon and eager to foster relationships within this magnificent region. That's why I'd greatly appreciate a short call with you.\n\n"
    "Most recently, I've  \n"
    "* supported a seven-figure equity raise for a U.S. diagnostics company,  \n"
    "* co-founded a consumer wellness brand in Mexico, scaling it nationwide through e-commerce, and  \n"
    "* partnered VC startups with tier-one brands such as lululemon.  \n\n"
    "Would you be open to a 15-minute call to explore potential synergies with {{short_name}}?\n\n"
    "Best regards,  \n"
    "Victor Gutierrez, CFA  \n"
    "+1 786 354 5031 • victor@zarcoideas.com  \n"
    "{{landing_page}}  \n"
    "CV attached"
)


def pick_fund_column(columns: list[str]) -> str | None:
    """Best-effort detection of the fund/firm name column."""
    lower = {c: str(c).strip().lower() for c in columns}

    # Common possibilities, ordered by preference
    preferred = [
        "investors", "fund name", "firm name", "organization", "organisation", "company",
        "investor", "fund", "firm", "name"
    ]
    for want in preferred:
        for c, lc in lower.items():
            if lc == want:
                return c

    # Fuzzy contains search fallbacks
    contains_order = ["investors", "fund", "firm", "investor", "organization", "company", "name"]
    for token in contains_order:
        for c, lc in lower.items():
            if token in lc:
                return c
    return None


def safe_get(row, col_name: str, default: str = "") -> str:
    try:
        v = row.get(col_name, default)
    except Exception:
        v = default
    return "" if pd.isna(v) else str(v).strip()


def build_tokens(row, fund_col: str):
    honorific = safe_get(row, "Honorific")
    last_name = safe_get(row, "Last Name") or safe_get(row, "Last name") or safe_get(row, "Last")
    fund_name = safe_get(row, fund_col) if fund_col else "your fund"
    
    # Get short name, fallback to fund name if not available
    short_name = safe_get(row, "Short_Name")
    if not short_name:
        short_name = fund_name

    # Default hook sentence placeholder
    person_hook_sentence = (
        f"your leadership at {fund_name} caught my attention"
        if fund_name else "your leadership caught my attention"
    )

    return {
        "{{honorific}}": honorific,
        "{{last_name}}": last_name,
        "{{fund_name}}": fund_name,
        "{{short_name}}": short_name,
        "{{person_hook_sentence}}": person_hook_sentence,
        "{{landing_page}}": LANDING_PAGE,
    }


def apply_tokens(template: str, tokens: dict[str, str]) -> str:
    text = template
    for k, v in tokens.items():
        text = text.replace(k, v)
    return text


def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    fund_col = pick_fund_column(list(df.columns))

    # Prepare output columns
    subjects, bodies, merged = [], [], []
    hooks, hook_urls, hook_conf = [], [], []

    for _, row in df.iterrows():
        tokens = build_tokens(row, fund_col)
        subject = apply_tokens(SUBJECT_TEMPLATE, tokens)
        body = apply_tokens(BODY_TEMPLATE, tokens)
        email_merged = f"Subject: {subject}\n\n{body}"

        subjects.append(subject)
        bodies.append(body)
        merged.append(email_merged)

        # Future automation stub columns (empty for now)
        hooks.append(tokens.get("{{person_hook_sentence}}", ""))
        hook_urls.append("")
        hook_conf.append("")

    df["Email_Subject"] = subjects
    df["Email_Body"] = bodies
    df["Email_Template"] = merged

    # Stub columns for future hook generation
    df["Person_Hook"] = hooks
    df["Hook_Source_URL"] = hook_urls
    df["Hook_Confidence"] = hook_conf

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Archivo generado: {OUTPUT_FILE}")

    # Print 5 random examples
    n = min(5, len(df))
    print("\n=== Sample emails (random) ===")
    for i in random.sample(range(len(df)), k=n):
        subj = df.at[i, "Email_Subject"]
        body = df.at[i, "Email_Body"]
        print("\n---")
        print(f"Row #{i}")
        print(f"Subject: {subj}")
        print(body)


if __name__ == "__main__":
    main()



