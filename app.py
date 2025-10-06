import streamlit as st
import pandas as pd
import os
import subprocess
import sys
import random

# Configuración de la página
st.set_page_config(
    page_title="VC Outreach Editor",
    page_icon="📧",
    layout="wide"
)

st.title("📧 VC Outreach Email Editor")
st.markdown("Edita hooks personalizados y cualquier columna de tu base de datos de VC.")

# Tabs para organizar funcionalidades
tab1, tab2, tab3, tab4 = st.tabs(["📝 Editor de Datos", "🤖 Generador de Hooks", "👀 Revisión de Hooks", "🎲 Vista Previa Aleatoria"])

# Cargar datos
@st.cache_data
def load_data():
    if os.path.exists("857-vc-funds-with-email-template.csv"):
        return pd.read_csv("857-vc-funds-with-email-template.csv")
    return None

df = load_data()

if df is None:
    st.error("❌ No se encontró el archivo '857-vc-funds-with-email-template.csv'")
    st.info("💡 Ejecuta primero: `python generate_personalized_emails.py`")
    st.stop()

with tab1:
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros")

    # Filtro por país
    countries = ["Todos"] + sorted(df["country"].dropna().unique().tolist())
    selected_country = st.sidebar.selectbox("País", countries)

    # Filtro por honorífico
    honorifics = ["Todos"] + sorted(df["Honorific"].dropna().unique().tolist())
    selected_honorific = st.sidebar.selectbox("Honorífico", honorifics)

    # Aplicar filtros
    filtered_df = df.copy()
    if selected_country != "Todos":
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if selected_honorific != "Todos":
        filtered_df = filtered_df[filtered_df["Honorific"] == selected_honorific]

    st.sidebar.metric("Registros mostrados", len(filtered_df))

    # Editor de datos
    st.header("📝 Editor de Datos")

    # Seleccionar columnas editables
    editable_columns = [
        "Person_Hook", "Hook_Source_URL", "Hook_Confidence",
        "First Name", "Last Name", "Honorific", "Email_Subject", "Email_Body"
    ]

    # Mostrar columnas disponibles
    available_columns = [col for col in editable_columns if col in filtered_df.columns]
    selected_columns = st.multiselect(
        "Selecciona columnas para editar:",
        available_columns,
        default=["Person_Hook", "First Name", "Last Name", "Honorific"]
    )

    if selected_columns:
        # Crear editor de datos - limpiar NaN values
        editor_df = filtered_df[["Primary Contact"] + selected_columns].copy()
        for col in selected_columns:
            if col in editor_df.columns:
                editor_df[col] = editor_df[col].fillna("").astype(str)
        
        edited_df = st.data_editor(
            editor_df,
            num_rows="dynamic",
            use_container_width=True,
            key="data_editor"
        )
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Guardar cambios al CSV", type="primary"):
                # Actualizar el DataFrame original con los cambios
                for idx, row in edited_df.iterrows():
                    # Usar el índice original del filtered_df
                    original_idx = filtered_df.index[idx]
                    for col in selected_columns:
                        if col in row:
                            df.at[original_idx, col] = row[col]
                
                # Guardar CSV
                df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                st.success("✅ Cambios guardados en CSV")
                st.cache_data.clear()
        
        with col2:
            if st.button("📊 Exportar a Excel"):
                df.to_excel("857-vc-funds-with-email-template-updated.xlsx", index=False)
                st.success("✅ Exportado a Excel")
        
        with col3:
            if st.button("🔄 Regenerar emails"):
                # Regenerar emails con los nuevos hooks
                for idx, row in df.iterrows():
                    if pd.notna(row.get("Person_Hook")) and row["Person_Hook"].strip():
                        # Actualizar el email body con el nuevo hook
                        old_hook = "your leadership at {{fund_name}} caught my attention"
                        new_hook = row["Person_Hook"]
                        
                        if "Email_Body" in df.columns:
                            df.at[idx, "Email_Body"] = df.at[idx, "Email_Body"].replace(old_hook, new_hook)
                
                df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                st.success("✅ Emails regenerados con nuevos hooks")
                st.cache_data.clear()
                st.rerun()

    # Vista previa de emails
    st.header("👀 Vista Previa de Emails")

    if len(filtered_df) > 0:
        # Selector de fila para preview
        row_idx = st.selectbox(
            "Selecciona un contacto para ver su email:",
            range(len(filtered_df)),
            format_func=lambda x: f"{filtered_df.iloc[x]['Primary Contact']} - {filtered_df.iloc[x].get('Investors', 'N/A')}"
        )
        
        selected_row = filtered_df.iloc[row_idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Asunto")
            st.code(selected_row.get("Email_Subject", "N/A"))
        
        with col2:
            st.subheader("📝 Cuerpo")
            st.code(selected_row.get("Email_Body", "N/A"))
        
        # Información del contacto
        st.subheader("👤 Información del Contacto")
        info_cols = ["Primary Contact", "First Name", "Last Name", "Honorific", "country", "Person_Hook"]
        available_info = [col for col in info_cols if col in selected_row.index]
        
        for col in available_info:
            if pd.notna(selected_row[col]):
                st.write(f"**{col}:** {selected_row[col]}")

    # Estadísticas
    st.header("📊 Estadísticas")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total contactos", len(df))

    with col2:
        hooks_filled = df["Person_Hook"].notna().sum() if "Person_Hook" in df.columns else 0
        st.metric("Hooks personalizados", hooks_filled)

    with col3:
        countries_count = df["country"].nunique() if "country" in df.columns else 0
        st.metric("Países únicos", countries_count)

    with col4:
        honorifics_count = df["Honorific"].nunique() if "Honorific" in df.columns else 0
        st.metric("Tipos de honoríficos", honorifics_count)

    # Instrucciones
    st.header("📋 Instrucciones")
    st.markdown("""
    1. **Filtra** los contactos usando la barra lateral
    2. **Selecciona** las columnas que quieres editar
    3. **Modifica** los datos directamente en la tabla
    4. **Guarda** los cambios al CSV
    5. **Regenera** los emails si cambiaste hooks
    6. **Exporta** a Excel cuando termines

    **Columnas importantes:**
    - `Person_Hook`: Frase personalizada para cada contacto
    - `Hook_Source_URL`: URL de donde sacaste la información
    - `Hook_Confidence`: Confianza en el hook (1-10)
    """)

# Tab 2: Generador de Hooks
with tab2:
    st.header("🤖 Generador Automático de Hooks")
    
    # Verificar API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    serpapi_key = os.getenv("SERPAPI_KEY")
    bing_key = os.getenv("BING_API_KEY")
    
    if not openai_key and not anthropic_key:
        st.error("❌ No hay API keys configuradas")
        st.info("""
        Configura una de estas opciones:
        
        **OpenAI (recomendado):**
        ```bash
        export OPENAI_API_KEY="tu_key_aqui"
        ```
        
        **Anthropic Claude:**
        ```bash
        export ANTHROPIC_API_KEY="tu_key_aqui"
        ```
        """)
    else:
        # Mostrar qué API está configurada
        if openai_key:
            st.success("✅ OpenAI API configurada")
        if anthropic_key:
            st.success("✅ Anthropic API configurada")
        if serpapi_key:
            st.success("✅ SerpAPI configurada (búsqueda web)")
        if bing_key:
            st.success("✅ Bing Search API configurada (búsqueda web)")
        
        # Mostrar opciones de generación
        st.subheader("🎯 Opciones de Generación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🚀 Generación Rápida (solo dataset)**")
            st.markdown("Usa solo la información del dataset. Más rápido pero menos específico.")
        
        with col2:
            st.markdown("**🌐 Generación con Búsqueda Web**")
            st.markdown("Busca información real en internet. Más lento pero mucho más natural y específico.")
        
        # Estadísticas de hooks
        total_contacts = len(df)
        hooks_generated = df["Person_Hook"].notna().sum() if "Person_Hook" in df.columns else 0
        hooks_empty = total_contacts - hooks_generated
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total contactos", total_contacts)
        with col2:
            st.metric("Hooks generados", hooks_generated)
        with col3:
            st.metric("Pendientes", hooks_empty)
        
        if hooks_empty > 0:
            st.warning(f"⚠️ {hooks_empty} contactos sin hook personalizado")
            
            # Opciones de generación
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚀 Generación Rápida**")
                if st.button("🚀 Generar hooks automáticamente", type="primary"):
                    with st.spinner("Generando hooks... Esto puede tomar varios minutos"):
                        try:
                            result = subprocess.run([
                                sys.executable, "generate_hooks.py"
                            ], capture_output=True, text=True, timeout=1800)
                            
                            if result.returncode == 0:
                                st.success("✅ Hooks generados exitosamente")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {result.stderr}")
                        except subprocess.TimeoutExpired:
                            st.error("❌ Timeout: El proceso tardó demasiado (30 min)")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                
                # Lote pequeño rápido
                batch_size = st.number_input("Tamaño del lote:", min_value=10, max_value=100, value=50)
                if st.button("🔄 Generar lote pequeño"):
                    with st.spinner(f"Generando {batch_size} hooks..."):
                        try:
                            temp_script = f"""
import os
import pandas as pd
import requests
import time
from generate_hooks import generate_hook

df = pd.read_csv("857-vc-funds-with-email-template.csv")
empty_hooks = df[df["Person_Hook"].isna() | (df["Person_Hook"] == "")]
batch = empty_hooks.head({batch_size})

generated_count = 0
for idx, row in batch.iterrows():
    print(f"Procesando {{row['Primary Contact']}}...")
    email_context = f"Subject: {{row.get('Email_Subject', '')}}\\nBody: {{row.get('Email_Body', '')}}"
    hook = generate_hook(row.to_dict(), email_context)
    if hook:
        df.at[idx, "Person_Hook"] = hook
        df.at[idx, "Hook_Confidence"] = "8"
        generated_count += 1
        print(f"  ✅ Hook generado: {{hook}}")
    time.sleep(0.5)

df.to_csv("857-vc-funds-with-email-template.csv", index=False)
print(f"✅ Lote completado: {{generated_count}} hooks generados")
"""
                            
                            with open("temp_batch.py", "w") as f:
                                f.write(temp_script)
                            
                            result = subprocess.run([
                                sys.executable, "temp_batch.py"
                            ], capture_output=True, text=True, timeout=600)
                            
                            if os.path.exists("temp_batch.py"):
                                os.remove("temp_batch.py")
                            
                            if result.returncode == 0:
                                st.success(f"✅ Lote de {batch_size} hooks generado")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {result.stderr}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            
            with col2:
                st.markdown("**🌐 Generación con Búsqueda Web**")
                
                # Verificar si hay API de búsqueda web
                if not serpapi_key and not bing_key:
                    st.error("❌ Necesitas configurar una API de búsqueda web:")
                    st.info("""
                    **SerpAPI (recomendado):**
                    ```bash
                    export SERPAPI_KEY="tu_key"
                    ```
                    
                    **O Bing Search API:**
                    ```bash
                    export BING_API_KEY="tu_key"
                    ```
                    """)
                else:
                    if st.button("🌐 Generar hooks con búsqueda web", type="primary"):
                        with st.spinner("Generando hooks con búsqueda web... Esto tomará más tiempo"):
                            try:
                                result = subprocess.run([
                                    sys.executable, "generate_hooks_with_web_search.py"
                                ], capture_output=True, text=True, timeout=3600)  # 1 hora
                                
                                if result.returncode == 0:
                                    st.success("✅ Hooks con búsqueda web generados exitosamente")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error: {result.stderr}")
                            except subprocess.TimeoutExpired:
                                st.error("❌ Timeout: El proceso tardó demasiado (1 hora)")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    # Lote pequeño con búsqueda web
                    web_batch_size = st.number_input("Tamaño del lote web:", min_value=5, max_value=20, value=10)
                    if st.button("🌐 Generar lote pequeño con web"):
                        with st.spinner(f"Generando {web_batch_size} hooks con búsqueda web..."):
                            try:
                                temp_script = f"""
import os
import pandas as pd
import requests
import time
from generate_hooks_with_web_search import generate_hook_with_web_context

df = pd.read_csv("857-vc-funds-with-email-template.csv")
empty_hooks = df[df["Person_Hook"].isna() | (df["Person_Hook"] == "")]
batch = empty_hooks.head({web_batch_size})

generated_count = 0
for idx, row in batch.iterrows():
    print(f"Procesando {{row['Primary Contact']}}...")
    email_context = f"Subject: {{row.get('Email_Subject', '')}}\\nBody: {{row.get('Email_Body', '')}}"
    hook, source_url, confidence = generate_hook_with_web_context(row.to_dict(), email_context)
    if hook:
        df.at[idx, "Person_Hook"] = hook
        df.at[idx, "Hook_Source_URL"] = source_url
        df.at[idx, "Hook_Confidence"] = confidence
        generated_count += 1
        print(f"  ✅ Hook generado: {{hook}}")
        if source_url:
            print(f"  📰 Fuente: {{source_url}}")
    time.sleep(2)  # Pausa más larga para búsquedas web

df.to_csv("857-vc-funds-with-email-template.csv", index=False)
print(f"✅ Lote web completado: {{generated_count}} hooks generados")
"""
                                
                                with open("temp_web_batch.py", "w") as f:
                                    f.write(temp_script)
                                
                                result = subprocess.run([
                                    sys.executable, "temp_web_batch.py"
                                ], capture_output=True, text=True, timeout=1200)  # 20 minutos
                                
                                if os.path.exists("temp_web_batch.py"):
                                    os.remove("temp_web_batch.py")
                                
                                if result.returncode == 0:
                                    st.success(f"✅ Lote web de {web_batch_size} hooks generado")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error: {result.stderr}")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
        else:
            st.success("✅ Todos los hooks ya están generados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Regenerar todos los hooks"):
                    # Limpiar hooks existentes
                    df["Person_Hook"] = ""
                    df["Hook_Confidence"] = ""
                    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                    st.success("✅ Hooks limpiados. Ejecuta 'Generar hooks automáticamente' para regenerar")
                    st.cache_data.clear()
                    st.rerun()
            
            with col2:
                if st.button("🔧 Regenerar hooks en español"):
                    # Buscar hooks que puedan estar en español
                    spanish_hooks = df[
                        (df["Person_Hook"].str.contains("tu|tu liderazgo|tu experiencia|tu enfoque", case=False, na=False)) |
                        (df["Person_Hook"].str.contains("su|su liderazgo|su experiencia|su enfoque", case=False, na=False))
                    ]
                    
                    if len(spanish_hooks) > 0:
                        st.warning(f"⚠️ Encontrados {len(spanish_hooks)} hooks que parecen estar en español")
                        
                        # Limpiar solo esos hooks
                        for idx in spanish_hooks.index:
                            df.at[idx, "Person_Hook"] = ""
                            df.at[idx, "Hook_Confidence"] = ""
                        
                        df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                        st.success("✅ Hooks en español limpiados. Ejecuta 'Generar hooks automáticamente' para regenerar")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.info("✅ No se encontraron hooks en español")

# Tab 3: Revisión de Hooks
with tab3:
    st.header("👀 Revisión y Edición de Hooks")
    
    # Filtros para revisión
    col1, col2, col3 = st.columns(3)
    
    with col1:
        hook_status = st.selectbox(
            "Estado del hook:",
            ["Todos", "Con hook", "Sin hook", "Confianza baja"]
        )
    
    with col2:
        countries_review = ["Todos"] + sorted(df["country"].dropna().unique().tolist())
        country_review = st.selectbox("País:", countries_review)
    
    with col3:
        confidence_threshold = st.slider("Confianza mínima:", 1, 10, 7)
    
    # Aplicar filtros
    review_df = df.copy()
    
    if hook_status == "Con hook":
        review_df = review_df[review_df["Person_Hook"].notna() & (review_df["Person_Hook"] != "")]
    elif hook_status == "Sin hook":
        review_df = review_df[review_df["Person_Hook"].isna() | (review_df["Person_Hook"] == "")]
    elif hook_status == "Confianza baja":
        review_df = review_df[
            (review_df["Person_Hook"].notna()) & 
            (review_df["Person_Hook"] != "") &
            (review_df["Hook_Confidence"].astype(str).str.isdigit()) &
            (review_df["Hook_Confidence"].astype(int) < confidence_threshold)
        ]
    
    if country_review != "Todos":
        review_df = review_df[review_df["country"] == country_review]
    
    st.write(f"**Mostrando {len(review_df)} de {len(df)} contactos**")
    
    if len(review_df) > 0:
        # Editor específico para hooks
        hook_columns = ["Primary Contact", "Investors", "Person_Hook", "Hook_Confidence", "Hook_Source_URL"]
        available_hook_cols = [col for col in hook_columns if col in review_df.columns]
        
        # Convertir NaN a string vacío para evitar errores de tipo
        review_df_clean = review_df[available_hook_cols].copy()
        if "Person_Hook" in review_df_clean.columns:
            review_df_clean["Person_Hook"] = review_df_clean["Person_Hook"].fillna("").astype(str)
        if "Hook_Source_URL" in review_df_clean.columns:
            review_df_clean["Hook_Source_URL"] = review_df_clean["Hook_Source_URL"].fillna("").astype(str)
        if "Hook_Confidence" in review_df_clean.columns:
            review_df_clean["Hook_Confidence"] = review_df_clean["Hook_Confidence"].fillna("").astype(str)
        
        edited_hooks = st.data_editor(
            review_df_clean,
            num_rows="dynamic",
            use_container_width=True,
            key="hook_editor",
            column_config={
                "Person_Hook": st.column_config.TextColumn(
                    "Hook Personalizado",
                    help="Frase específica para este contacto",
                    width="large"
                ),
                "Hook_Confidence": st.column_config.SelectboxColumn(
                    "Confianza",
                    options=["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    help="Confianza en el hook (1-10)"
                )
            }
        )
        
        # Botones de acción
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Guardar cambios de hooks", type="primary"):
                # Actualizar el DataFrame original
                for idx, row in edited_hooks.iterrows():
                    original_idx = review_df.index[idx]
                    for col in available_hook_cols:
                        if col in ["Person_Hook", "Hook_Confidence", "Hook_Source_URL"] and col in row:
                            df.at[original_idx, col] = row[col]
                
                df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                st.success("✅ Cambios de hooks guardados")
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("🔄 Regenerar emails con nuevos hooks"):
                # Regenerar emails con los hooks actualizados
                for idx, row in df.iterrows():
                    if pd.notna(row.get("Person_Hook")) and row["Person_Hook"].strip():
                        # Actualizar el email body con el nuevo hook
                        old_hook = "your leadership at {{fund_name}} caught my attention"
                        new_hook = row["Person_Hook"]
                        
                        if "Email_Body" in df.columns:
                            df.at[idx, "Email_Body"] = df.at[idx, "Email_Body"].replace(old_hook, new_hook)
                
                df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                st.success("✅ Emails regenerados con hooks actualizados")
                st.cache_data.clear()
                st.rerun()
        
        # Vista previa de hooks
        st.subheader("🔍 Vista Previa de Hooks")
        
        if len(review_df) > 0:
            hook_idx = st.selectbox(
                "Selecciona un contacto para ver su hook:",
                range(len(review_df)),
                format_func=lambda x: f"{review_df.iloc[x]['Primary Contact']} - {review_df.iloc[x].get('Investors', 'N/A')}"
            )
            
            selected_hook_row = review_df.iloc[hook_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Hook actual:**")
                st.code(selected_hook_row.get("Person_Hook", "Sin hook"))
                
                st.write("**Confianza:**")
                st.code(selected_hook_row.get("Hook_Confidence", "N/A"))
            
            with col2:
                st.write("**Contexto del contacto:**")
                context_info = [
                    f"**Fondo:** {selected_hook_row.get('Investors', 'N/A')}",
                    f"**Título:** {selected_hook_row.get('Primary Contact Title', 'N/A')}",
                    f"**País:** {selected_hook_row.get('country', 'N/A')}",
                    f"**Ubicación:** {selected_hook_row.get('HQ Location', 'N/A')}",
                    f"**Sectores preferidos:** {selected_hook_row.get('Preferred Verticals', 'N/A')}",
                    f"**Tipos de inversión:** {selected_hook_row.get('Preferred Investment Types', 'N/A')}",
                    f"**Geografía preferida:** {selected_hook_row.get('Preferred Geography', 'N/A')}",
                    f"**Industria:** {selected_hook_row.get('Preferred Industry', 'N/A')}",
                    f"**Última inversión:** {selected_hook_row.get('Last Investment Company', 'N/A')}",
                    f"**Descripción del fondo:** {selected_hook_row.get('Description', 'N/A')[:200]}..."
                ]
                for info in context_info:
                    st.write(info)
                
                # Botones para regenerar hook individual
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Regenerar hook (rápido)", key=f"regenerate_{hook_idx}"):
                        with st.spinner("Regenerando hook..."):
                            try:
                                # Importar función de generación
                                import sys
                                sys.path.append('.')
                                from generate_hooks import generate_hook
                                
                                # Crear contexto del email
                                email_context = f"""
Subject: {selected_hook_row.get('Email_Subject', '')}
Body: {selected_hook_row.get('Email_Body', '')}
"""
                                
                                # Generar nuevo hook
                                new_hook = generate_hook(selected_hook_row.to_dict(), email_context)
                                
                                if new_hook:
                                    # Actualizar en el DataFrame
                                    original_idx = review_df.index[hook_idx]
                                    df.at[original_idx, "Person_Hook"] = new_hook
                                    df.at[original_idx, "Hook_Confidence"] = "8"
                                    
                                    # Guardar cambios
                                    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                                    st.success(f"✅ Hook regenerado: {new_hook}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("❌ Error regenerando hook")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                
                with col2:
                    if st.button("🌐 Regenerar con búsqueda web", key=f"regenerate_web_{hook_idx}"):
                        with st.spinner("Regenerando hook con búsqueda web..."):
                            try:
                                # Importar función de generación con web
                                import sys
                                sys.path.append('.')
                                from generate_hooks_with_web_search import generate_hook_with_web_context
                                
                                # Crear contexto del email
                                email_context = f"""
Subject: {selected_hook_row.get('Email_Subject', '')}
Body: {selected_hook_row.get('Email_Body', '')}
"""
                                
                                # Generar nuevo hook con búsqueda web
                                new_hook, source_url, confidence = generate_hook_with_web_context(selected_hook_row.to_dict(), email_context)
                                
                                if new_hook:
                                    # Actualizar en el DataFrame
                                    original_idx = review_df.index[hook_idx]
                                    df.at[original_idx, "Person_Hook"] = new_hook
                                    df.at[original_idx, "Hook_Source_URL"] = source_url
                                    df.at[original_idx, "Hook_Confidence"] = confidence
                                    
                                    # Guardar cambios
                                    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                                    st.success(f"✅ Hook regenerado: {new_hook}")
                                    if source_url:
                                        st.info(f"📰 Fuente: {source_url}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("❌ Error regenerando hook")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
    else:
        st.info("No hay contactos que coincidan con los filtros seleccionados")

# Tab 4: Vista Previa Aleatoria
with tab4:
    st.header("🎲 Vista Previa Aleatoria")
    st.markdown("Explora contactos aleatorios y ve cómo se ven los emails completos.")
    
    # Botón para randomizar
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🎲 Seleccionar contacto aleatorio", type="primary"):
            st.rerun()
    
    with col2:
        # Filtro por país para randomizar
        countries_random = ["Todos"] + sorted(df["country"].dropna().unique().tolist())
        country_filter = st.selectbox("Filtrar por país:", countries_random, key="random_country")
    
    with col3:
        # Filtro por estado del hook
        hook_status_filter = st.selectbox("Estado del hook:", ["Todos", "Con hook", "Sin hook"], key="random_hook_status")
    
    # Aplicar filtros para randomizar
    random_df = df.copy()
    if country_filter != "Todos":
        random_df = random_df[random_df["country"] == country_filter]
    if hook_status_filter == "Con hook":
        random_df = random_df[random_df["Person_Hook"].notna() & (random_df["Person_Hook"] != "")]
    elif hook_status_filter == "Sin hook":
        random_df = random_df[random_df["Person_Hook"].isna() | (random_df["Person_Hook"] == "")]
    
    if len(random_df) > 0:
        # Seleccionar contacto aleatorio
        random_idx = st.session_state.get('random_idx', 0)
        if 'random_idx' not in st.session_state:
            random_idx = random_df.index[0]
        
        # Botón para cambiar contacto aleatorio
        if st.button("🎲 Cambiar contacto aleatorio"):
            random_idx = random.choice(random_df.index)
            st.session_state['random_idx'] = random_idx
            st.rerun()
        
        # Obtener contacto seleccionado
        selected_contact = random_df.loc[random_idx]
        
        # Mostrar información del contacto
        st.subheader("👤 Información del Contacto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Nombre:** {selected_contact.get('Primary Contact', 'N/A')}")
            st.write(f"**Título:** {selected_contact.get('Primary Contact Title', 'N/A')}")
            st.write(f"**Fondo:** {selected_contact.get('Investors', 'N/A')}")
            st.write(f"**País:** {selected_contact.get('country', 'N/A')}")
            st.write(f"**Ubicación:** {selected_contact.get('HQ Location', 'N/A')}")
        
        with col2:
            st.write(f"**Sectores preferidos:** {selected_contact.get('Preferred Verticals', 'N/A')}")
            st.write(f"**Tipos de inversión:** {selected_contact.get('Preferred Investment Types', 'N/A')}")
            st.write(f"**Geografía preferida:** {selected_contact.get('Preferred Geography', 'N/A')}")
            st.write(f"**Industria:** {selected_contact.get('Preferred Industry', 'N/A')}")
            st.write(f"**Última inversión:** {selected_contact.get('Last Investment Company', 'N/A')}")
        
        # Descripción del fondo
        if selected_contact.get('Description'):
            st.write(f"**Descripción del fondo:** {selected_contact.get('Description', 'N/A')[:300]}...")
        
        st.divider()
        
        # Hook personalizado
        st.subheader("🎯 Hook Personalizado")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            current_hook = selected_contact.get('Person_Hook', 'Sin hook')
            if current_hook and current_hook != 'Sin hook':
                st.success(f"**Hook actual:** {current_hook}")
            else:
                st.warning("**Hook actual:** Sin hook personalizado")
        
        with col2:
            if st.button("🔄 Regenerar hook", key=f"regenerate_random_{random_idx}"):
                with st.spinner("Regenerando hook..."):
                    try:
                        # Importar función de generación
                        import sys
                        sys.path.append('.')
                        from generate_hooks import generate_hook
                        
                        # Crear contexto del email
                        email_context = f"""
Subject: {selected_contact.get('Email_Subject', '')}
Body: {selected_contact.get('Email_Body', '')}
"""
                        
                        # Generar nuevo hook
                        new_hook = generate_hook(selected_contact.to_dict(), email_context)
                        
                        if new_hook:
                            # Actualizar en el DataFrame
                            df.at[random_idx, "Person_Hook"] = new_hook
                            df.at[random_idx, "Hook_Confidence"] = "8"
                            
                            # Guardar cambios
                            df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                            st.success(f"✅ Hook regenerado: {new_hook}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Error regenerando hook")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        st.divider()
        
        # Vista previa del email completo
        st.subheader("📧 Vista Previa del Email")
        
        # Asunto
        st.markdown("**Asunto:**")
        st.code(selected_contact.get('Email_Subject', 'N/A'))
        
        # Cuerpo del email
        st.markdown("**Cuerpo del email:**")
        email_body = selected_contact.get('Email_Body', 'N/A')
        
        # Resaltar el hook en el email
        if current_hook and current_hook != 'Sin hook':
            # Reemplazar el hook genérico con el personalizado para mostrar
            fund_name = selected_contact.get('Investors', '')
            generic_hook = f"your leadership at {fund_name} caught my attention"
            
            # Intentar diferentes variaciones del hook genérico
            highlighted_body = email_body
            if generic_hook in email_body:
                highlighted_body = email_body.replace(generic_hook, f"**{current_hook}**")
            elif "your leadership at {{fund_name}} caught my attention" in email_body:
                highlighted_body = email_body.replace("your leadership at {{fund_name}} caught my attention", f"**{current_hook}**")
            elif "your leadership at" in email_body and "caught my attention" in email_body:
                # Buscar y reemplazar cualquier variación
                import re
                pattern = r"your leadership at [^,]*caught my attention"
                highlighted_body = re.sub(pattern, f"**{current_hook}**", email_body)
            
            st.markdown(highlighted_body)
        else:
            st.markdown(email_body)
        
        st.divider()
        
        # Estadísticas del contacto
        st.subheader("📊 Estadísticas del Contacto")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Confianza del hook", selected_contact.get('Hook_Confidence', 'N/A'))
        
        with col2:
            st.metric("Honorífico", selected_contact.get('Honorific', 'N/A'))
        
        with col3:
            st.metric("Email disponible", "Sí" if selected_contact.get('Primary Contact Email') else "No")
        
        with col4:
            st.metric("Teléfono disponible", "Sí" if selected_contact.get('Primary Contact Phone') else "No")
        
        # Botones de acción
        st.subheader("🔧 Acciones")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ Editar en Tab 3", key=f"edit_{random_idx}"):
                st.info("Ve al Tab 3 y filtra por este contacto para editarlo")
        
        with col2:
            if st.button("📊 Exportar este contacto", key=f"export_{random_idx}"):
                # Crear DataFrame con solo este contacto
                single_contact = df[df.index == random_idx]
                single_contact.to_excel("contacto_individual.xlsx", index=False)
                st.success("✅ Contacto exportado a 'contacto_individual.xlsx'")
        
        with col3:
            if st.button("🔄 Regenerar email completo", key=f"regenerate_email_{random_idx}"):
                # Regenerar email con el hook actual
                if selected_contact.get('Person_Hook'):
                    fund_name = selected_contact.get('Investors', '')
                    new_hook = selected_contact.get('Person_Hook')
                    
                    # Intentar diferentes variaciones del hook genérico
                    email_body = df.at[random_idx, "Email_Body"]
                    updated_body = email_body
                    
                    # Reemplazar diferentes variaciones
                    generic_hook = f"your leadership at {fund_name} caught my attention"
                    if generic_hook in email_body:
                        updated_body = email_body.replace(generic_hook, new_hook)
                    elif "your leadership at {{fund_name}} caught my attention" in email_body:
                        updated_body = email_body.replace("your leadership at {{fund_name}} caught my attention", new_hook)
                    elif "your leadership at" in email_body and "caught my attention" in email_body:
                        import re
                        pattern = r"your leadership at [^,]*caught my attention"
                        updated_body = re.sub(pattern, new_hook, email_body)
                    
                    df.at[random_idx, "Email_Body"] = updated_body
                    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
                    st.success("✅ Email regenerado con hook actual")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("⚠️ No hay hook personalizado para regenerar")
        
        # Información adicional
        st.subheader("ℹ️ Información Adicional")
        
        if selected_contact.get('Hook_Source_URL'):
            st.write(f"**Fuente del hook:** {selected_contact.get('Hook_Source_URL')}")
        
        if selected_contact.get('Website'):
            st.write(f"**Website del fondo:** {selected_contact.get('Website')}")
        
        if selected_contact.get('Primary Contact Email'):
            st.write(f"**Email de contacto:** {selected_contact.get('Primary Contact Email')}")
        
        if selected_contact.get('Primary Contact Phone'):
            st.write(f"**Teléfono:** {selected_contact.get('Primary Contact Phone')}")
    
    else:
        st.warning("⚠️ No hay contactos que coincidan con los filtros seleccionados")
        st.info("💡 Cambia los filtros para ver más contactos")
