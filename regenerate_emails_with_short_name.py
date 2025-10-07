#!/usr/bin/env python3
"""
Script para regenerar todos los emails usando el nuevo template con {{short_name}}.
"""

import pandas as pd

# Landing page
LANDING_PAGE = "https://zarcoideas.com"

# Email template actualizado con {{short_name}}
SUBJECT_TEMPLATE = "CFA Charterholder | Exploring collaboration with {{fund_name}}"

BODY_TEMPLATE = (
    "{{honorific}} {{last_name}},\n\n"
    "I'm Victor G. Zarco, CFA Bs. in Actuarial Science and Financial Economist.  \n"
    "I came across your leadership in {{fund_name}}, particularly {{person_hook_sentence}}.\n\n"
    "I am eager to foster relationships within the magnificent Middle East in collaboration with {{short_name}}.\n\n"
    "Most recently, I've  \n"
    "* supported a seven-figure equity raise for a U.S. diagnostics company,  \n"
    "* co-founded a consumer wellness brand in Mexico, scaling it nationwide through e-commerce, and  \n"
    "* partnered VC startups with tier-one brands such as lululemon.  \n\n"
    "Would you be open to a 15-minute call to explore potential synergies with {{fund_name}}?\n\n"
    "Best regards,  \n"
    "Victor Gutierrez, CFA  \n"
    "+1 786 354 5031 • victor@zarcoideas.com  \n"
    "{{landing_page}}  \n"
    "CV attached"
)


def safe_get(row, col_name: str, default: str = "") -> str:
    """Obtener valor de manera segura del DataFrame."""
    try:
        v = row.get(col_name, default)
    except Exception:
        v = default
    return "" if pd.isna(v) else str(v).strip()


def build_email_body(row):
    """
    Construye el cuerpo del email con todos los tokens reemplazados.
    """
    honorific = safe_get(row, "Honorific")
    last_name = safe_get(row, "Last Name")
    fund_name = safe_get(row, "Investors")
    short_name = safe_get(row, "Short_Name")
    
    # Si no hay short_name, usar fund_name
    if not short_name:
        short_name = fund_name
    
    # Usar Person_Hook si existe, sino usar el hook genérico
    person_hook = safe_get(row, "Person_Hook")
    if person_hook and person_hook.strip():
        person_hook_sentence = person_hook
    else:
        person_hook_sentence = f"your leadership at {fund_name} caught my attention"
    
    # Reemplazar tokens
    body = BODY_TEMPLATE
    body = body.replace("{{honorific}}", honorific)
    body = body.replace("{{last_name}}", last_name)
    body = body.replace("{{fund_name}}", fund_name)
    body = body.replace("{{short_name}}", short_name)
    body = body.replace("{{person_hook_sentence}}", person_hook_sentence)
    body = body.replace("{{landing_page}}", LANDING_PAGE)
    
    return body


def build_email_subject(row):
    """Construye el asunto del email."""
    fund_name = safe_get(row, "Investors")
    subject = SUBJECT_TEMPLATE.replace("{{fund_name}}", fund_name)
    return subject


def main():
    """Función principal."""
    print("📂 Leyendo archivo CSV...")
    df = pd.read_csv("857-vc-funds-with-email-template.csv")
    
    print(f"✅ Cargados {len(df)} registros")
    
    # Regenerar emails
    print("\n🔄 Regenerando emails con el nuevo template...")
    
    emails_updated = 0
    for idx, row in df.iterrows():
        # Regenerar asunto y cuerpo
        df.at[idx, "Email_Subject"] = build_email_subject(row)
        df.at[idx, "Email_Body"] = build_email_body(row)
        df.at[idx, "Email_Template"] = f"Subject: {df.at[idx, 'Email_Subject']}\n\n{df.at[idx, 'Email_Body']}"
        emails_updated += 1
    
    print(f"✅ {emails_updated} emails regenerados")
    
    # Mostrar algunos ejemplos
    print("\n📧 Ejemplos de emails regenerados:")
    print("=" * 80)
    
    for idx in df.sample(3).index:
        row = df.loc[idx]
        print(f"\n👤 Contacto: {row['Primary Contact']}")
        print(f"🏢 Fondo: {row['Investors']}")
        print(f"📝 Nombre corto: {row['Short_Name']}")
        print(f"🔗 Hook: {safe_get(row, 'Person_Hook') or 'Genérico'}")
        print("\n📧 Email Body (extracto):")
        body_lines = row['Email_Body'].split('\n')
        for i, line in enumerate(body_lines):
            if i < 8:  # Mostrar primeras 8 líneas
                print(f"   {line}")
        print("   ...")
        print("-" * 80)
    
    # Guardar
    print("\n💾 Guardando cambios...")
    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
    print("✅ Todos los emails han sido regenerados con el nuevo template")
    print(f"✅ Archivo actualizado: 857-vc-funds-with-email-template.csv")


if __name__ == "__main__":
    main()

