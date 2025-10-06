import os
import pandas as pd
import requests
import json
import time
from typing import Optional

# Configuración
INPUT_FILE = "857-vc-funds-with-email-template.csv"
OUTPUT_FILE = "857-vc-funds-with-email-template.csv"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # export OPENAI_API_KEY="tu_key"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # export ANTHROPIC_API_KEY="tu_key"

# Usar OpenAI por defecto, pero puedes cambiar a Anthropic
USE_OPENAI = True  # Cambiar a False para usar Anthropic

def generate_hook_openai(contact_data: dict, email_context: str) -> Optional[str]:
    """Genera un hook personalizado usando OpenAI GPT-4."""
    if not OPENAI_API_KEY:
        return None
    
    prompt = f"""
You are an expert in venture capital and networking. Your task is to create a personalized and specific phrase for a Middle East VC contact.

CONTACT CONTEXT:
- Name: {contact_data.get('Primary Contact', 'N/A')}
- Title: {contact_data.get('Primary Contact Title', 'N/A')}
- Fund: {contact_data.get('Investors', 'N/A')}
- Location: {contact_data.get('HQ Location', 'N/A')}
- Country: {contact_data.get('country', 'N/A')}
- Preferred investment types: {contact_data.get('Preferred Investment Types', 'N/A')}
- Preferred sectors: {contact_data.get('Preferred Verticals', 'N/A')}
- Last investment: {contact_data.get('Last Investment Company', 'N/A')}
- Investment geography: {contact_data.get('Preferred Geography', 'N/A')}
- Industry focus: {contact_data.get('Preferred Industry', 'N/A')}
- Fund description: {contact_data.get('Description', 'N/A')}

EMAIL CONTEXT:
{email_context}

INSTRUCTIONS:
1. Create ONE natural, conversational phrase to replace "your leadership at [fund] caught my attention"
2. Focus on their professional journey, achievements, or career path
3. Sound like a real person who researched their background
4. Be complimentary and show genuine interest in their work
5. Maximum 20 words
6. Professional but personal tone
7. RESPOND ONLY IN ENGLISH - no Spanish, Arabic, or other languages

GOOD EXAMPLES:
- "I followed your path from [previous company] to [current fund]"
- "your recent ventures in the [specific industry] space caught my attention"
- "your journey from [background] to [current role] is impressive"
- "your track record at [previous company] caught my attention"
- "your insights on [specific topic] particularly interested me"

AVOID:
- Generic statements about their "focus" or "expertise"
- Obvious facts they already know about themselves
- Robotic AI-sounding phrases
- Statements that sound like you're stating the obvious

RESPONSE: Only the phrase, no quotes or explanations. Make it sound natural and researched.
"""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            hook = result["choices"][0]["message"]["content"].strip()
            # Limpiar comillas si las hay
            hook = hook.strip('"').strip("'")
            return hook
        else:
            print(f"Error OpenAI: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error generando hook: {e}")
        return None

def generate_hook_anthropic(contact_data: dict, email_context: str) -> Optional[str]:
    """Genera un hook personalizado usando Anthropic Claude."""
    if not ANTHROPIC_API_KEY:
        return None
    
    prompt = f"""
You are an expert in venture capital and networking. Your task is to create a personalized and specific phrase for a Middle East VC contact.

CONTACT CONTEXT:
- Name: {contact_data.get('Primary Contact', 'N/A')}
- Title: {contact_data.get('Primary Contact Title', 'N/A')}
- Fund: {contact_data.get('Investors', 'N/A')}
- Location: {contact_data.get('HQ Location', 'N/A')}
- Country: {contact_data.get('country', 'N/A')}
- Preferred investment types: {contact_data.get('Preferred Investment Types', 'N/A')}
- Preferred sectors: {contact_data.get('Preferred Verticals', 'N/A')}
- Last investment: {contact_data.get('Last Investment Company', 'N/A')}
- Investment geography: {contact_data.get('Preferred Geography', 'N/A')}
- Industry focus: {contact_data.get('Preferred Industry', 'N/A')}
- Fund description: {contact_data.get('Description', 'N/A')}

EMAIL CONTEXT:
{email_context}

INSTRUCTIONS:
1. Create ONE natural, conversational phrase to replace "your leadership at [fund] caught my attention"
2. Focus on their professional journey, achievements, or career path
3. Sound like a real person who researched their background
4. Be complimentary and show genuine interest in their work
5. Maximum 20 words
6. Professional but personal tone
7. RESPOND ONLY IN ENGLISH - no Spanish, Arabic, or other languages

GOOD EXAMPLES:
- "I followed your path from [previous company] to [current fund]"
- "your recent ventures in the [specific industry] space caught my attention"
- "your journey from [background] to [current role] is impressive"
- "your track record at [previous company] caught my attention"
- "your insights on [specific topic] particularly interested me"

AVOID:
- Generic statements about their "focus" or "expertise"
- Obvious facts they already know about themselves
- Robotic AI-sounding phrases
- Statements that sound like you're stating the obvious

RESPONSE: Only the phrase, no quotes or explanations. Make it sound natural and researched.
"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            hook = result["content"][0]["text"].strip()
            # Limpiar comillas si las hay
            hook = hook.strip('"').strip("'")
            return hook
        else:
            print(f"Error Anthropic: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error generando hook: {e}")
        return None

def generate_hook(contact_data: dict, email_context: str) -> Optional[str]:
    """Genera hook usando el LLM configurado."""
    if USE_OPENAI:
        return generate_hook_openai(contact_data, email_context)
    else:
        return generate_hook_anthropic(contact_data, email_context)

def main():
    # Verificar API key
    if USE_OPENAI and not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no configurada")
        print("Ejecuta: export OPENAI_API_KEY='tu_key'")
        return
    
    if not USE_OPENAI and not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY no configurada")
        print("Ejecuta: export ANTHROPIC_API_KEY='tu_key'")
        return
    
    # Cargar datos
    df = pd.read_csv(INPUT_FILE)
    
    # Filtrar solo los que no tienen hook personalizado
    empty_hooks = df[df["Person_Hook"].isna() | (df["Person_Hook"] == "")]
    
    if len(empty_hooks) == 0:
        print("✅ Todos los hooks ya están generados")
        return
    
    print(f"🔄 Generando hooks para {len(empty_hooks)} contactos...")
    
    # Generar hooks
    generated_count = 0
    for idx, row in empty_hooks.iterrows():
        print(f"Procesando {row['Primary Contact']} - {row.get('Investors', 'N/A')}...")
        
        # Crear contexto del email
        email_context = f"""
Subject: {row.get('Email_Subject', '')}
Body: {row.get('Email_Body', '')}
"""
        
        # Generar hook
        hook = generate_hook(row.to_dict(), email_context)
        
        if hook:
            df.at[idx, "Person_Hook"] = hook
            df.at[idx, "Hook_Confidence"] = "8"  # Confianza alta para LLM
            generated_count += 1
            print(f"  ✅ Hook generado: {hook}")
        else:
            print(f"  ❌ Error generando hook")
        
        # Pausa más corta para ser más eficiente
        time.sleep(0.5)
    
    # Guardar resultados
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Proceso completado:")
    print(f"   - Hooks generados: {generated_count}")
    print(f"   - Archivo actualizado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
