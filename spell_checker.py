#!/usr/bin/env python3
"""
Aplicación Streamlit para revisar ortografía y redacción de emails.
Sube un CSV y revisa la columna 'body' para asegurar inglés natural y sin errores.
"""

import streamlit as st
import pandas as pd
import re
from typing import List, Dict, Tuple
import openai
import os

# Configuración de la página
st.set_page_config(
    page_title="Email Spell Checker",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Email Spell Checker & Grammar Review")
st.markdown("Revisa ortografía, gramática y naturalidad del inglés en tus emails.")

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# API Key para OpenAI
api_key = st.sidebar.text_input(
    "OpenAI API Key (opcional)",
    type="password",
    help="Para revisión avanzada con GPT-4"
)

if api_key:
    openai.api_key = api_key
    use_ai_review = True
else:
    use_ai_review = False
    st.sidebar.info("💡 Sin API key: solo revisión básica de ortografía")

# Función para revisión básica de ortografía
def basic_spell_check(text: str) -> List[Dict]:
    """Revisión básica de ortografía y gramática."""
    issues = []
    
    # Palabras comunes mal escritas
    common_mistakes = {
        "recieve": "receive",
        "seperate": "separate", 
        "definately": "definitely",
        "occured": "occurred",
        "begining": "beginning",
        "accomodate": "accommodate",
        "acheive": "achieve",
        "beleive": "believe",
        "calender": "calendar",
        "cemetary": "cemetery",
        "concious": "conscious",
        "embarass": "embarrass",
        "existance": "existence",
        "goverment": "government",
        "independant": "independent",
        "occassion": "occasion",
        "priviledge": "privilege",
        "rythm": "rhythm",
        "seige": "siege",
        "tommorrow": "tomorrow",
        "untill": "until",
        "writting": "writing"
    }
    
    # Revisar palabras mal escritas
    for mistake, correction in common_mistakes.items():
        if mistake in text.lower():
            issues.append({
                "type": "spelling",
                "issue": f"'{mistake}' should be '{correction}'",
                "severity": "medium"
            })
    
    # Revisar dobles espacios
    if "  " in text:
        issues.append({
            "type": "formatting",
            "issue": "Double spaces found",
            "severity": "low"
        })
    
    # Revisar espacios antes de puntuación
    if re.search(r'\s+[.,!?;:]', text):
        issues.append({
            "type": "formatting", 
            "issue": "Spaces before punctuation",
            "severity": "low"
        })
    
    return issues

# Función para revisión con AI
def ai_review(text: str) -> List[Dict]:
    """Revisión avanzada con OpenAI GPT-4."""
    if not use_ai_review:
        return []
    
    try:
        prompt = f"""
        Review this email text for:
        1. Spelling errors
        2. Grammar mistakes  
        3. Natural English flow
        4. Professional tone
        5. Clarity and directness
        
        Text to review:
        {text}
        
        Respond in JSON format with this structure:
        {{
            "issues": [
                {{
                    "type": "spelling|grammar|style|clarity",
                    "issue": "description of the issue",
                    "suggestion": "suggested improvement",
                    "severity": "low|medium|high"
                }}
            ],
            "overall_score": 1-10,
            "is_english": true/false
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        # Parse JSON response
        import json
        return json.loads(result)
        
    except Exception as e:
        st.error(f"Error en revisión AI: {e}")
        return []

# Función principal de revisión
def review_email_body(body: str, row_idx: int) -> Dict:
    """Revisar un email body completo."""
    if pd.isna(body) or not body.strip():
        return {"issues": [], "score": 0, "is_english": False}
    
    # Revisión básica
    basic_issues = basic_spell_check(body)
    
    # Revisión AI si está disponible
    ai_result = ai_review(body) if use_ai_review else {"issues": [], "overall_score": 8, "is_english": True}
    
    # Combinar resultados
    all_issues = basic_issues + ai_result.get("issues", [])
    
    return {
        "issues": all_issues,
        "score": ai_result.get("overall_score", 8),
        "is_english": ai_result.get("is_english", True),
        "row_idx": row_idx
    }

# Interfaz principal
st.header("📤 Subir Archivo CSV")

uploaded_file = st.file_uploader(
    "Selecciona tu archivo CSV",
    type=['csv'],
    help="El archivo debe contener una columna 'body' con los emails"
)

if uploaded_file is not None:
    try:
        # Leer CSV
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Archivo cargado: {len(df)} registros")
        
        # Verificar que existe la columna 'body'
        if 'body' not in df.columns:
            st.error("❌ No se encontró la columna 'body' en el CSV")
            st.info("💡 El CSV debe contener una columna llamada 'body'")
        else:
            st.info(f"📋 Columnas encontradas: {', '.join(df.columns)}")
            
            # Mostrar preview
            st.subheader("📋 Preview del archivo")
            st.dataframe(df.head(), use_container_width=True)
            
            # Botón para iniciar revisión
            if st.button("🔍 Iniciar Revisión de Emails", type="primary"):
                st.subheader("🔍 Revisando emails...")
                
                # Crear contenedores para resultados
                results_container = st.container()
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                all_results = []
                total_rows = len(df)
                
                # Revisar cada email
                for idx, row in df.iterrows():
                    status_text.text(f"Revisando email {idx + 1} de {total_rows}")
                    progress_bar.progress((idx + 1) / total_rows)
                    
                    result = review_email_body(row['body'], idx)
                    all_results.append(result)
                
                # Mostrar resultados
                with results_container:
                    st.subheader("📊 Resultados de la Revisión")
                    
                    # Estadísticas generales
                    total_issues = sum(len(r['issues']) for r in all_results)
                    avg_score = sum(r['score'] for r in all_results) / len(all_results)
                    english_emails = sum(1 for r in all_results if r['is_english'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total emails", len(all_results))
                    with col2:
                        st.metric("Total issues", total_issues)
                    with col3:
                        st.metric("Score promedio", f"{avg_score:.1f}/10")
                    with col4:
                        st.metric("En inglés", f"{english_emails}/{len(all_results)}")
                    
                    # Filtros para resultados
                    st.subheader("🔧 Filtros")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        min_score = st.slider("Score mínimo", 1, 10, 7)
                    with col2:
                        severity_filter = st.selectbox(
                            "Severidad mínima",
                            ["Todas", "low", "medium", "high"]
                        )
                    
                    # Mostrar emails con problemas
                    st.subheader("⚠️ Emails que necesitan revisión")
                    
                    emails_to_review = []
                    for result in all_results:
                        if result['score'] < min_score or len(result['issues']) > 0:
                            # Filtrar por severidad
                            if severity_filter != "Todas":
                                filtered_issues = [i for i in result['issues'] if i.get('severity') == severity_filter]
                                if not filtered_issues:
                                    continue
                            
                            emails_to_review.append(result)
                    
                    if emails_to_review:
                        for result in emails_to_review:
                            row_idx = result['row_idx']
                            row = df.iloc[row_idx]
                            
                            with st.expander(f"📧 Email {row_idx + 1} - Score: {result['score']}/10"):
                                # Información del contacto
                                if 'Full_name' in df.columns:
                                    st.write(f"**Contacto:** {row.get('Full_name', 'N/A')}")
                                if 'email' in df.columns:
                                    st.write(f"**Email:** {row.get('email', 'N/A')}")
                                
                                # Issues encontrados
                                if result['issues']:
                                    st.write("**Problemas encontrados:**")
                                    for issue in result['issues']:
                                        severity_color = {
                                            "low": "🟡",
                                            "medium": "🟠", 
                                            "high": "🔴"
                                        }.get(issue.get('severity', 'low'), "🟡")
                                        
                                        st.write(f"{severity_color} **{issue.get('type', 'unknown').title()}:** {issue.get('issue', 'N/A')}")
                                        if 'suggestion' in issue:
                                            st.write(f"   💡 *Sugerencia: {issue['suggestion']}*")
                                
                                # Email body
                                st.write("**Email body:**")
                                st.text_area(
                                    "Contenido del email",
                                    value=row['body'],
                                    height=200,
                                    key=f"body_{row_idx}"
                                )
                    else:
                        st.success("🎉 ¡Todos los emails están en buen estado!")
                    
                    # Botón para exportar resultados
                    if st.button("📥 Exportar Reporte"):
                        # Crear reporte
                        report_df = pd.DataFrame()
                        report_df['row_index'] = [r['row_idx'] for r in all_results]
                        report_df['score'] = [r['score'] for r in all_results]
                        report_df['is_english'] = [r['is_english'] for r in all_results]
                        report_df['total_issues'] = [len(r['issues']) for r in all_results]
                        
                        # Agregar columnas del CSV original
                        for col in df.columns:
                            report_df[col] = df[col].values
                        
                        # Guardar reporte
                        report_file = "email_review_report.csv"
                        report_df.to_csv(report_file, index=False)
                        st.success(f"✅ Reporte exportado: {report_file}")
                        
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")

else:
    st.info("👆 Sube un archivo CSV para comenzar la revisión")
    
    # Mostrar ejemplo de formato esperado
    st.subheader("📋 Formato esperado del CSV")
    example_df = pd.DataFrame({
        'Full_name': ['John Smith', 'Jane Doe'],
        'email': ['john@example.com', 'jane@example.com'],
        'body': [
            'Dear John,\n\nI hope this email finds you well...',
            'Hello Jane,\n\nThank you for your interest...'
        ],
        'subject': ['Subject 1', 'Subject 2']
    })
    st.dataframe(example_df, use_container_width=True)
