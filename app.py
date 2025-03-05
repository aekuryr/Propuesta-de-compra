import pandas as pd
import streamlit as st

# Configuración de la aplicación
st.set_page_config(page_title="📊 Propuesta de Compra de Farmacia", layout="wide")

# Título de la aplicación
st.title("📊 Propuesta de Compra de Farmacia")

# Sección de introducción con explicaciones
st.markdown("""
### ℹ️ Instrucciones y Explicaciones

🔹 **Valores negativos en `Cantidad_Necesaria`**  
Si la cantidad necesaria es negativa, significa que el stock actual **ya es suficiente** para cubrir los 6 meses requeridos.

🔹 **Interpretación de `Critico_Abastecimiento`**  
- **"Crítico para abastecimiento"** → Medicamentos con **alta rotación** (`Código_Consumo A`) pero **bajo stock** (`Código_Stock C`), por lo que su compra es prioritaria.  
- **"No es crítico"** → No cumple con estas condiciones.

🔹 **Interpretación de `Stock_Vencimiento_Alto`**  
- **"Alta cantidad se vence"** → Más del **50% del stock actual** se vencerá en los próximos **90 días**, por lo que puede requerir reposición.  
- **"Baja cantidad de vencimiento"** → Menos del **50% del stock** está próximo a vencer.
""")

# Cargar archivo CSV
uploaded_file = st.file_uploader("📂 Sube tu archivo CSV con el inventario", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Calcular la cantidad necesaria para abastecer 6 meses
    df["Cantidad_Necesaria"] = (df["CPM Nacional"] * 6) - df["Existencias totales"]

    # Identificar medicamentos críticos para abastecimiento (baja cobertura nacional)
    df["Critico_Abastecimiento"] = df["Cobertura Nacional"] < 6

    # Identificar medicamentos con más del 50% del stock venciendo en 90 días
    df["Stock_Vencimiento_Alto"] = df["Total de existencias que vencen en los próximos 90 días"] > (df["Existencias totales"] * 0.5)

    # Filtrar los medicamentos que necesitan compra
    df_compra = df[
        (df["Propuesta_de_compra"] > 0) |  
        df["Critico_Abastecimiento"] |  
        df["Stock_Vencimiento_Alto"]
    ].copy()  

    # Reemplazar valores en las columnas con etiquetas más descriptivas
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
    st.dataframe(df_compra)

    # Permitir descarga del archivo procesado
    csv = df_compra.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar propuesta de compra",
        data=csv,
        file_name="Propuesta_Compra_Medicamentos.csv",
        mime="text/csv"
    )
else:
    st.info("⚠️ Por favor, sube un archivo CSV para analizar el inventario.")
