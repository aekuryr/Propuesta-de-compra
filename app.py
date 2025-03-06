import pandas as pd
import streamlit as st

# Configuración de la aplicación
st.set_page_config(page_title="📊 Análisis de Inventario de Farmacia", layout="wide")

# Título de la aplicación
st.title("📊 Análisis de Inventario de Farmacia")

# Explicación
st.markdown("""
### ℹ️ Instrucciones y Explicaciones

**Interpretación de `Cantidad_Necesaria`**
- El cálculo estima la cantidad necesaria para cubrir un número configurable de meses, basado en el **Consumo Promedio Mensual (CPM)**.

🔹 **Valores negativos en `Cantidad_Necesaria`**  
Si la cantidad necesaria es negativa, significa que el stock actual **ya es suficiente** para cubrir los meses requeridos.

🔹 **Interpretación de `Critico_Abastecimiento`**  
- **"Crítico para abastecimiento"** → Medicamentos con **alta rotación** (`Código_Consumo A`) pero **bajo stock** (`Código_Stock C`), por lo que su compra es prioritaria.  
- **"No es crítico"** → No cumple con estas condiciones.

🔹 **Interpretación de `Stock_Vencimiento_Alto`**  
- **"Alta cantidad se vence"** → Más del **50% del stock actual** se vencerá en los próximos **90 días**, por lo que puede requerir reposición.  
- **"Baja cantidad de vencimiento"** → Menos del **50% del stock** está próximo a vencer.
""")

# 📌 Instrucciones para descargar el archivo correcto
st.markdown("""
### 🛠 **Paso previo: Descarga del archivo correcto**
Antes de subir el archivo, asegúrate de descargar la **primera tabla** llamada  
**"Existencia y cobertura de medicamentos a nivel nacional"** en el apartado de **Existencias**.
""")

# Mostrar imagen con la instrucción
image_path = "tablero existencias.png"  # Nombre del archivo de la imagen
st.image(image_path, caption="Ubicación del archivo a descargar", use_container_width=True)

# Configuración del número de meses
meses_abastecimiento = st.slider("📅 Selecciona la cantidad de meses para calcular el abastecimiento", min_value=1, max_value=12, value=6)

# Opción para considerar o no las existencias que vencerán pronto
considerar_vencimiento = st.checkbox("📌 No tomar en cuenta existencias próximas a vencerse", value=True)

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
        # Calcular la cantidad necesaria considerando todo el stock
        df["Cantidad_Necesaria"] = (df["CPM Nacional"] * meses_abastecimiento) - df["Existencias totales"]
        
        # Calcular la cantidad necesaria sin contar el stock próximo a vencer
        df["Cantidad_Necesaria_SinVencimiento"] = (df["CPM Nacional"] * meses_abastecimiento) - (
            df["Existencias totales"] - df["Total de existencias que vencen en los próximos 90 días"]
        )

        # Determinar cuál de los valores usar según la opción seleccionada por el usuario
        if considerar_vencimiento:
            df["Cantidad_Necesaria_Final"] = df["Cantidad_Necesaria_SinVencimiento"]
        else:
            df["Cantidad_Necesaria_Final"] = df["Cantidad_Necesaria"]

        # Identificar medicamentos críticos para abastecimiento (baja cobertura nacional)
        df["Critico_Abastecimiento"] = df["Cobertura Nacional"] < meses_abastecimiento

        # Identificar medicamentos con más del 50% del stock venciendo en 90 días
        df["Stock_Vencimiento_Alto"] = df["Total de existencias que vencen en los próximos 90 días"] > (df["Existencias totales"] * 0.5)

        # Filtrar los medicamentos que necesitan compra
        df_compra = df[
            (df["Cantidad_Necesaria_Final"] > 0) |  
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

        # Seleccionar columnas a mostrar
        columnas_mostrar = ["CPM Nacional", "Existencias totales", "Cobertura Nacional", 
                            "Total de existencias que vencen en los próximos 90 días",
                            "Cantidad_Necesaria", "Cantidad_Necesaria_SinVencimiento",
                            "Cantidad_Necesaria_Final", "Critico_Abastecimiento",
                            "Stock_Vencimiento_Alto"]
        
        df_compra = df_compra[columnas_mostrar]

        # Mostrar resultados
        st.subheader(f"📌 Medicamentos que requieren compra ({meses_abastecimiento} meses de abastecimiento)")
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
