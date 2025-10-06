import os
import pandas as pd
import requests
import json
import time
from typing import Optional
import re

# Configuración
INPUT_FILE = "857-vc-funds-with-email-template.csv"
OUTPUT_FILE = "857-vc-funds-with-email-template.csv"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # export SERPAPI_KEY="tu_key"
BING_API_KEY = os.getenv("BING_API_KEY")  # export BING_API_KEY="tu_key"

# Usar SerpAPI por defecto (más confiable), pero puedes cambiar a Bing
USE_SERPAPI = True  # Cambiar a False para usar Bing

def search_web_serpapi(query: str, num_results: int = 3) -> list[dict]:
    """Busca información en web usando SerpAPI."""
    if not SERPAPI_KEY:
        return []
    
    try:
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_results,
            "engine": "google"
        }
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "organic_results" in data:
                for result in data["organic_results"][:num_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", "")
                    })
            
            return results
        else:
            print(f"Error SerpAPI: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error en búsqueda web: {e}")
        return []

def search_web_bing(query: str, num_results: int = 3) -> list[dict]:
    """Busca información en web usando Bing Search API."""
    if not BING_API_KEY:
        return []
    
    try:
        headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
        params = {
            "q": query,
            "count": num_results,
            "mkt": "en-US"
        }
        
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "webPages" in data and "value" in data["webPages"]:
                for result in data["webPages"]["value"]:
                    results.append({
                        "title": result.get("name", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("url", "")
                    })
            
            return results
        else:
            print(f"Error Bing: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error en búsqueda web: {e}")
        return []

def search_web(query: str, num_results: int = 3) -> list[dict]:
    """Busca información en web usando el servicio configurado."""
    if USE_SERPAPI:
        return search_web_serpapi(query, num_results)
    else:
        return search_web_bing(query, num_results)

def generate_hook_with_web_context(contact_data: dict, email_context: str) -> tuple[Optional[str], str, str]:
    """
    Genera un hook personalizado usando información de web search.
    Retorna: (hook, source_url, confidence)
    """
    if not OPENAI_API_KEY:
        return None, "", ""
    
    # Crear query de búsqueda
    fund_name = contact_data.get('Investors', '')
    person_name = contact_data.get('Primary Contact', '')
    person_title = contact_data.get('Primary Contact Title', '')
    
    # Query principal: buscar información sobre la trayectoria profesional
    search_queries = [
        f'"{person_name}" "{person_title}" career background experience',
        f'"{person_name}" "{fund_name}" interview profile biography',
        f'"{person_name}" previous companies career path',
        f'"{fund_name}" "{person_name}" recent achievements awards',
        f'"{person_name}" "{person_title}" speaking events conferences',
        f'"{fund_name}" recent portfolio companies investments 2024'
    ]
    
    web_results = []
    source_url = ""
    
    # Buscar información web
    for query in search_queries:
        if query.strip():
            results = search_web(query, 2)
            web_results.extend(results)
            if results and not source_url:
                source_url = results[0].get("url", "")
        
        time.sleep(1)  # Pausa entre búsquedas
    
    # Crear contexto web
    web_context = ""
    if web_results:
        web_context = "RECENT WEB INFORMATION:\n"
        for i, result in enumerate(web_results[:3], 1):
            web_context += f"{i}. {result['title']}\n"
            web_context += f"   {result['snippet']}\n"
            web_context += f"   Source: {result['url']}\n\n"
    
    # Prompt mejorado con contexto web
    prompt = f"""
You are an expert in venture capital and networking. Create a personalized, natural-sounding phrase for a Middle East VC contact based on REAL, RECENT information.

CONTACT INFO:
- Name: {contact_data.get('Primary Contact', 'N/A')}
- Title: {contact_data.get('Primary Contact Title', 'N/A')}
- Fund: {contact_data.get('Investors', 'N/A')}
- Location: {contact_data.get('HQ Location', 'N/A')}
- Country: {contact_data.get('country', 'N/A')}

{web_context}

EMAIL CONTEXT:
{email_context}

INSTRUCTIONS:
1. Create ONE natural, conversational phrase to replace "your leadership at [fund] caught my attention"
2. Use the WEB INFORMATION above to make it specific and personal
3. Sound like a real person who actually researched this contact's CAREER and ACHIEVEMENTS
4. Focus on their professional journey, achievements, or recent activities
5. Be complimentary and show genuine interest in their work
6. Maximum 20 words
7. Professional but personal tone
8. ENGLISH ONLY

GOOD EXAMPLES (based on real info):
- "I followed your path from [previous company] to [current fund]"
- "your recent ventures in the [specific industry] space caught my attention"
- "your insights on [specific topic] in [publication/interview] resonated with me"
- "your journey from [background] to [current role] is impressive"
- "your recent comments on [specific trend] particularly interested me"
- "your track record at [previous company] caught my attention"

AVOID:
- Generic statements about their "focus" or "expertise"
- Obvious facts they already know about themselves
- Robotic AI-sounding phrases
- Statements that sound like you're stating the obvious

RESPONSE: Only the phrase, no quotes or explanations. Make it sound like a real person who researched their career.
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
                "temperature": 0.8  # Más creatividad para sonar natural
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            hook = result["choices"][0]["message"]["content"].strip()
            hook = hook.strip('"').strip("'")
            
            # Determinar confianza basada en si encontramos info web
            confidence = "9" if web_results else "6"
            
            return hook, source_url, confidence
        else:
            print(f"Error OpenAI: {response.status_code}")
            return None, "", ""
            
    except Exception as e:
        print(f"Error generando hook: {e}")
        return None, "", ""

def main():
    # Verificar API keys
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no configurada")
        return
    
    if USE_SERPAPI and not SERPAPI_KEY:
        print("❌ SERPAPI_KEY no configurada")
        print("Ejecuta: export SERPAPI_KEY='tu_key'")
        return
    
    if not USE_SERPAPI and not BING_API_KEY:
        print("❌ BING_API_KEY no configurada")
        print("Ejecuta: export BING_API_KEY='tu_key'")
        return
    
    # Cargar datos
    df = pd.read_csv(INPUT_FILE)
    
    # Filtrar solo los que no tienen hook personalizado
    empty_hooks = df[df["Person_Hook"].isna() | (df["Person_Hook"] == "")]
    
    if len(empty_hooks) == 0:
        print("✅ Todos los hooks ya están generados")
        return
    
    print(f"🔄 Generando hooks con búsqueda web para {len(empty_hooks)} contactos...")
    print("⚠️ Esto tomará más tiempo debido a las búsquedas web...")
    
    # Generar hooks
    generated_count = 0
    for idx, row in empty_hooks.iterrows():
        print(f"Procesando {row['Primary Contact']} - {row.get('Investors', 'N/A')}...")
        
        # Crear contexto del email
        email_context = f"""
Subject: {row.get('Email_Subject', '')}
Body: {row.get('Email_Body', '')}
"""
        
        # Generar hook con búsqueda web
        hook, source_url, confidence = generate_hook_with_web_context(row.to_dict(), email_context)
        
        if hook:
            df.at[idx, "Person_Hook"] = hook
            df.at[idx, "Hook_Source_URL"] = source_url
            df.at[idx, "Hook_Confidence"] = confidence
            generated_count += 1
            print(f"  ✅ Hook generado: {hook}")
            if source_url:
                print(f"  📰 Fuente: {source_url}")
        else:
            print(f"  ❌ Error generando hook")
        
        # Pausa más larga para no sobrecargar APIs
        time.sleep(2)
    
    # Guardar resultados
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Proceso completado:")
    print(f"   - Hooks generados: {generated_count}")
    print(f"   - Archivo actualizado: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
