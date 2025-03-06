import pandas as pd
import streamlit as st

# Configuración de la aplicación
st.set_page_config(page_title="📊 Análisis de Inventario de Farmacia", layout="wide")

# Título de la aplicación
st.title("📊 Análisis de Inventario de Farmacia")

# Explicación
st.markdown("""
### ℹ️ Instrucciones y Explicaciones

🔹 **Nueva clasificación de `Critico_Abastecimiento`**  
Ahora se categoriza en 4 niveles según la cantidad necesaria para lograr la cobertura deseada:
- 🟥 **Alta** → Más del **75%** de la cantidad deseada falta en stock.
- 🟧 **Media** → Entre **50% y 75%** de la cantidad deseada falta en stock.
- 🟨 **Baja** → Entre **25% y 50%** de la cantidad deseada falta en stock.
- 🟩 **No es crítico** → Menos del **25%** o el stock es suficiente.
""")

# 📌 Agregar instrucciones para descargar el archivo correcto
st.markdown("""
### 🛠 **Paso previo: Descarga del archivo correcto**
Antes de subir el archivo, asegúrate de descargar la **primera tabla** llamada  
**"Existencia y cobertura de medicamentos a nivel nacional"** en el apartado de **Existencias**.
""")

# Opción 1: Agregar la imagen con la instrucción
image_path = "tablero existencias.png"  # Nombre del archivo de la imagen
st.image(image_path, caption="Ubicación del archivo a descargar", use_container_width=True)

# Configuración del número de meses
meses_abastecimiento = st.slider("📅 Selecciona la cantidad de meses para calcular el abastecimiento", min_value=1, max_value=12, value=6)

# Cargar archivo CSV
uploaded_file = st.file_uploader("📂 Sube tu archivo CSV con el inventario", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Limpiar nombres de columnas eliminando espacios extra
    df.columns = df.columns.str.strip()

    # Verificar si las columnas necesarias existen en el archivo subido
    required_columns = ["CPM Nacional", "Existencias totales", "Cobertura Nacional", 
                        "Total de existencias que vencen en los próximos 90 días"]
    
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"⚠️ Error: El archivo no contiene las siguientes columnas requeridas: {', '.join(missing_columns)}")
    else:
        # Calcular la cantidad necesaria para abastecer los meses seleccionados
        df["Cantidad_Necesaria"] = (df["CPM Nacional"] * meses_abastecimiento) - df["Existencias totales"]

        # Nueva columna: Ajustar cantidad necesaria restando los medicamentos que se vencerán
        df["Cantidad_Necesaria_Ajustada"] = df["Cantidad_Necesaria"] - df["Total de existencias que vencen en los próximos 90 días"]

        # Si el valor es negativo, se cambia a 0
        df["Cantidad_Necesaria_Ajustada"] = df["Cantidad_Necesaria_Ajustada"].apply(lambda x: max(x, 0))

        # Cantidad deseada para la cobertura total
        df["Cantidad_Deseada"] = df["CPM Nacional"] * meses_abastecimiento

        # Clasificación de Criticidad
        def categorizar_criticidad(cantidad_necesaria, cantidad_deseada):
            if cantidad_necesaria >= cantidad_deseada * 0.75:
                return "🟥 Alta"
            elif cantidad_necesaria >= cantidad_deseada * 0.50:
                return "🟧 Media"
            elif cantidad_necesaria >= cantidad_deseada * 0.25:
                return "🟨 Baja"
            else:
                return "🟩 No es crítico"

        df["Critico_Abastecimiento"] = df.apply(lambda row: categorizar_criticidad(row["Cantidad_Necesaria_Ajustada"], row["Cantidad_Deseada"]), axis=1)

        # Identificar medicamentos con más del 50% del stock venciendo en 90 días
        df["Stock_Vencimiento_Alto"] = df["Total de existencias que vencen en los próximos 90 días"] > (df["Existencias totales"] * 0.5)

        # Filtrar los medicamentos que necesitan compra
        df_compra = df[
            (df["Cantidad_Necesaria_Ajustada"] > 0) |  
            (df["Critico_Abastecimiento"] != "🟩 No es crítico") |  
            df["Stock_Vencimiento_Alto"]
        ].copy()

        # Reemplazar valores en la columna `Stock_Vencimiento_Alto`
        df_compra["Stock_Vencimiento_Alto"] = df_compra["Stock_Vencimiento_Alto"].replace({
            True: "Alta cantidad se vence",
            False: "Baja cantidad de vencimiento"
        })

        # Mostrar resultados
        st.subheader(f"📌 Medicamentos que requieren compra ({meses_abastecimiento} meses de abastecimiento)")

        # Mostrar DataFrame en Streamlit
        st.dataframe(df_compra)

        # Permitir descarga del archivo procesado
        csv = df_compra.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Descargar propuesta de compra ({meses_abastecimiento} meses)",
            data=csv,
            file_name=f"Propuesta_Compra_Medicamentos_{meses_abastecimiento}M.csv",
            mime="text/csv"
        )
else:
    st.info("⚠️ Por favor, sube un archivo CSV para analizar el inventario.")
