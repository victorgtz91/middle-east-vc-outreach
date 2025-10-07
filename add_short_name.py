#!/usr/bin/env python3
"""
Script para agregar la columna Short_Name a los fondos.
Elimina sufijos comunes como "Venture Partners", "Investment Manager", "Ventures", etc.
"""

import pandas as pd
import re

def extract_short_name(fund_name):
    """
    Extrae el nombre corto del fondo eliminando sufijos comunes.
    
    Args:
        fund_name: Nombre completo del fondo
        
    Returns:
        Nombre corto del fondo
    """
    if pd.isna(fund_name) or not fund_name.strip():
        return fund_name
    
    # Lista de sufijos comunes a eliminar (ordenados de más específico a más general)
    suffixes = [
        # Sufijos con "Venture"
        r'\s+Venture\s+Capital\s+Partners?',
        r'\s+Venture\s+Partners?',
        r'\s+Venture\s+Capital',
        r'\s+Ventures',
        r'\s+Venture',
        
        # Sufijos con "Investment"
        r'\s+Investment\s+Management',
        r'\s+Investment\s+Manager',
        r'\s+Investment\s+Partners?',
        r'\s+Investment\s+Group',
        r'\s+Investments?',
        
        # Sufijos con "Capital"
        r'\s+Capital\s+Partners?',
        r'\s+Capital\s+Management',
        r'\s+Capital\s+Group',
        r'\s+Capital',
        
        # Sufijos con "Partners"
        r'\s+Partners?\s+LP',
        r'\s+Partners?\s+LLC',
        r'\s+Partners?',
        
        # Sufijos con "Management"
        r'\s+Management\s+Company',
        r'\s+Management',
        
        # Otros sufijos comunes
        r'\s+Group',
        r'\s+Fund',
        r'\s+Holdings?',
        r'\s+LLC',
        r'\s+LP',
        r'\s+Ltd\.?',
        r'\s+Limited',
        r'\s+Inc\.?',
        r'\s+Incorporated',
        r'\s+Corp\.?',
        r'\s+Corporation',
        r'\s+Company',
        r'\s+Co\.?',
        
        # Abreviaciones comunes
        r'\s+VC',
    ]
    
    short_name = fund_name.strip()
    
    # Intentar eliminar sufijos (case-insensitive)
    for suffix in suffixes:
        pattern = suffix + r'$'  # Solo al final del nombre
        short_name = re.sub(pattern, '', short_name, flags=re.IGNORECASE)
    
    # Limpiar espacios extras
    short_name = ' '.join(short_name.split())
    
    # Si el nombre quedó muy corto (menos de 2 caracteres), usar el original
    if len(short_name) < 2:
        return fund_name.strip()
    
    return short_name


def main():
    """Función principal."""
    print("📂 Leyendo archivo CSV...")
    df = pd.read_csv("857-vc-funds-with-email-template.csv")
    
    print(f"✅ Cargados {len(df)} registros")
    
    # Agregar columna Short_Name
    print("\n🔄 Generando nombres cortos...")
    df["Short_Name"] = df["Investors"].apply(extract_short_name)
    
    # Mostrar algunos ejemplos
    print("\n📊 Ejemplos de nombres cortos generados:")
    print("-" * 80)
    sample_df = df[["Investors", "Short_Name"]].dropna()
    
    # Mostrar 15 ejemplos aleatorios
    for idx, row in sample_df.sample(min(15, len(sample_df))).iterrows():
        original = row["Investors"]
        short = row["Short_Name"]
        if original != short:
            print(f"  {original:50} → {short}")
        else:
            print(f"  {original:50} (sin cambio)")
    
    # Estadísticas
    changed_count = (df["Investors"] != df["Short_Name"]).sum()
    print("\n" + "=" * 80)
    print(f"📊 Se generaron {changed_count} nombres cortos diferentes del original")
    print(f"📊 {len(df) - changed_count} nombres se mantuvieron igual")
    
    # Guardar
    print("\n💾 Guardando cambios...")
    df.to_csv("857-vc-funds-with-email-template.csv", index=False)
    print("✅ Archivo actualizado con la columna Short_Name")
    
    # Verificar posición de la columna
    print(f"\n📋 Columnas actuales ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"  {i}: {col}")


if __name__ == "__main__":
    main()

