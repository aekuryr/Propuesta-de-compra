import pandas as pd
import streamlit as st

# Configurar la aplicación
st.set_page_config(page_title="📊 Análisis de Inventario de Farmacia", layout="wide")

# Título de la aplicación
st.title("📊 Análisis de Inventario de Farmacia")

# Entrada del usuario para definir el tiempo de abastecimiento
tiempo_abastecimiento = st.number_input("Ingrese el número de meses para calcular la cantidad necesaria de abastecimiento:", min_value=1, max_value=24, value=6)

# Cargar archivo CSV
uploaded_file = st.file_uploader("📂 Sube tu archivo CSV con el inventario", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Limpiar nombres de columnas eliminando espacios extra
    df.columns = df.columns.str.strip()
    
    # Calcular la cantidad necesaria para abastecer según el tiempo configurado
    df["Cantidad_Necesaria"] = (df["CPM Nacional"] * tiempo_abastecimiento) - df["Existencias totales"]
    
    # Identificar medicamentos críticos para abastecimiento (baja cobertura nacional)
    df["Critico_Abastecimiento"] = df["Cobertura Nacional"] < tiempo_abastecimiento
    
    # Identificar medicamentos con más del 50% del stock venciendo en 90 días
    df["Stock_Vencimiento_Alto"] = df["Total de existencias que vencen en los próximos 90 días"] > (df["Existencias totales"] * 0.5)
    
    # Asignar Clasificación ABC basada en consumo promedio
    df["Contribucion_Consumo"] = (df["CPM Nacional"] / df["CPM Nacional"].sum()) * 100
    df = df.sort_values(by="CPM Nacional", ascending=False)
    df["Consumo_Acumulado"] = df["Contribucion_Consumo"].cumsum()
    df["Codigo_Consumo"] = df["Consumo_Acumulado"].apply(lambda x: "A" if x <= 80 else ("B" if x <= 95 else "C"))
    
    # Asignar Clasificación ABC basada en existencias
    df["Contribucion_Stock"] = (df["Existencias totales"] / df["Existencias totales"].sum()) * 100
    df = df.sort_values(by="Existencias totales", ascending=False)
    df["Stock_Acumulado"] = df["Contribucion_Stock"].cumsum()
    df["Codigo_Stock"] = df["Stock_Acumulado"].apply(lambda x: "A" if x <= 80 else ("B" if x <= 95 else "C"))
    
    # Relacionar ambas clasificaciones ABC para establecer la prioridad de compra
    df["Prioridad_Compra"] = df.apply(
        lambda row: "Alta" if row["Codigo_Consumo"] == "A" and row["Codigo_Stock"] == "C" else 
                    ("Media" if row["Codigo_Consumo"] == "B" and row["Codigo_Stock"] == "C" else 
                    ("Baja" if row["Codigo_Consumo"] == "C" and row["Codigo_Stock"] == "C" else "No Prioritario")), axis=1
    )
    
    # Filtrar medicamentos que vencen en los próximos 90 días
    df_vencimiento = df[df["Total de existencias que vencen en los próximos 90 días"] > 0].copy()
    
    # Calcular el porcentaje de existencias que se vencerán
    df_vencimiento["Porcentaje_Vencimiento"] = (df_vencimiento["Total de existencias que vencen en los próximos 90 días"] / df_vencimiento["Existencias totales"]) * 100
    
    # Clasificar la urgencia según el porcentaje de vencimiento
    df_vencimiento["Urgencia"] = df_vencimiento["Porcentaje_Vencimiento"].apply(
        lambda x: "Alta" if x > 50 else ("Media" if x > 25 else "Baja")
    )
    
    # Ordenar por urgencia y porcentaje de vencimiento
    df_vencimiento = df_vencimiento.sort_values(by=["Urgencia", "Porcentaje_Vencimiento"], ascending=[False, False])
    
    # Seleccionar columnas relevantes para el informe
    df_vencimiento_resumen = df_vencimiento[[
        "Código", "Medicamento", "Existencias totales", 
        "Total de existencias que vencen en los próximos 90 días", 
        "Porcentaje_Vencimiento", "Urgencia", "Codigo_Consumo", "Codigo_Stock", "Prioridad_Compra"
    ]]
    
    # Mostrar el informe en Streamlit
    st.subheader("📌 Informe de Medicamentos Próximos a Vencer")
    st.dataframe(df_vencimiento_resumen)
    
    # Permitir descarga del archivo procesado
    csv = df_vencimiento_resumen.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar informe de medicamentos próximos a vencer",
        data=csv,
        file_name="Informe_Medicamentos_Proximos_Vencer.csv",
        mime="text/csv"
    )
else:
    st.info("⚠️ Por favor, sube un archivo CSV para analizar el inventario.")
