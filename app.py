import pandas as pd
import streamlit as st

# Título de la aplicación
st.title("📊 Análisis de Inventario de Farmacia")

# Cargar archivo CSV
uploaded_file = st.file_uploader("Sube tu archivo CSV con el inventario", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Calcular la cantidad necesaria para abastecer 6 meses
    df["Cantidad_Necesaria"] = (df["CPM"] * 6) - df["Stock"]

    # Identificar medicamentos críticos para abastecimiento
    df["Critico_Abastecimiento"] = df["Codigo_Consumo"].str.startswith("A") & df["Codigo_Stock"].str.startswith("C")

    # Identificar medicamentos con más del 50% del stock venciendo en 90 días
    df["Stock_Vencimiento_Alto"] = df["Total de existencias que vencen en los próximos 90 días"] > (df["Stock"] * 0.5)

    # Filtro de medicamentos que necesitan compra
    df_compra = df[
        (df["Cantidad_Necesaria"] > 0) |
        df["Critico_Abastecimiento"] |
        df["Stock_Vencimiento_Alto (>50%)"]
    ].copy()

    # Etiquetas más descriptivas
    df_compra["Critico_Abastecimiento"] = df_compra["Critico_Abastecimiento"].replace({
        True: "Crítico para abastecimiento",
        False: "No es crítico"
    })
    
    df_compra["Stock_Vencimiento_Alto"] = df_compra["Stock_Vencimiento_Alto"].replace({
        True: "Alta cantidad se vence",
        False: "Baja cantidad de vencimiento"
    })

    # Mostrar resultados
    st.subheader("📌 Medicamentos que requieren compra")
    st.write(df_compra)

    # Permitir descarga del archivo procesado
    csv = df_compra.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar propuesta de compra",
        data=csv,
        file_name="Propuesta_Compra_Medicamentos.csv",
        mime="text/csv"
    )
