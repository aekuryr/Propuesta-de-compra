import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# Configuración de la aplicación
st.set_page_config(page_title="📊 Análisis de Inventario de Farmacia", layout="wide")

# Título de la aplicación
st.title("📊 Análisis de Inventario de Farmacia")

# Explicación
st.markdown("""
### ℹ️ Instrucciones y Explicaciones

🔹 **Clasificación de `Critico_Abastecimiento`**  
Ahora se categoriza en 4 niveles según la cantidad necesaria para lograr la cobertura deseada:
- 🟥 **Alta** → Más del **75%** de la cantidad deseada falta en stock.
- 🟧 **Media** → Entre **50% y 75%** de la cantidad deseada falta en stock.
- 🟨 **Baja** → Entre **25% y 50%** de la cantidad deseada falta en stock.
- 🟩 **No es crítico** → Menos del **25%** o el stock es suficiente.
""")

with st.expander("ℹ️ Explicación de las columnas"):
    st.markdown("""
    - **Cantidad_Necesaria:** Diferencia entre la cantidad deseada y el stock actual. Indica cuánto medicamento hace falta para alcanzar la cobertura establecida.
    - **Cantidad_Deseada:** Cantidad óptima de medicamentos para garantizar el abastecimiento durante el período de tiempo seleccionado.
    - **Cantidad_Necesaria_Ajustada:** Cantidad necesaria ajustada considerando las unidades que vencerán en los próximos 90 días.
    - **Clasificación ABC:** Prioriza medicamentos según su importancia en consumo. Letra "A" representa el medicamentos más críticos (80% del consumo total).
    - **Índice de Rotación:** Veces que el inventario se renueva en un año. Si es bajo, indica riesgo de caducidad.
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
        # 📌 Cálculo de métricas básicas
        df["Cantidad_Deseada"] = df["CPM Nacional"] * meses_abastecimiento
        df["Cantidad_Necesaria"] = df["Cantidad_Deseada"] - df["Existencias totales"]
        df["Cantidad_Necesaria_Ajustada"] = df["Cantidad_Necesaria"] - df["Total de existencias que vencen en los próximos 90 días"]
        df["Cantidad_Necesaria_Ajustada"] = df["Cantidad_Necesaria_Ajustada"].apply(lambda x: max(x, 0))

        # 📌 Cálculo del índice de rotación de inventario
        df["Consumo_Anual"] = df["CPM Nacional"] * 12
        df["Rotacion_Inventario"] = df["Consumo_Anual"] / df["Existencias totales"]
        df["Rotacion_Inventario"] = df["Rotacion_Inventario"].round(2)  # 🔄 Redondeo a 2 decimales

        # 📌 Clasificación ABC (Análisis de Pareto 80/20)
        df = df.sort_values(by="Consumo_Anual", ascending=False)
        total_consumo = df["Consumo_Anual"].sum()
        df["Consumo_Acumulado"] = df["Consumo_Anual"].cumsum()  # Esta columna NO se mostrará

        def clasificar_abc(x):
            if x <= total_consumo * 0.80:
                return "A"
            elif x <= total_consumo * 0.95:
                return "B"
            else:
                return "C"

        df["Clasificacion_ABC"] = df["Consumo_Acumulado"].apply(clasificar_abc)

        # 📌 Clasificación de Criticidad
        def categorizar_criticidad(cantidad_necesaria, cantidad_deseada):
            if cantidad_deseada == 0:
                return "🟩 No es crítico"
            porcentaje_faltante = cantidad_necesaria / cantidad_deseada
            if porcentaje_faltante >= 0.75:
                return "🟥 Alta"
            elif porcentaje_faltante >= 0.50:
                return "🟧 Media"
            elif porcentaje_faltante >= 0.25:
                return "🟨 Baja"
            else:
                return "🟩 No es crítico"

        df["Critico_Abastecimiento"] = df.apply(lambda row: categorizar_criticidad(row["Cantidad_Necesaria_Ajustada"], row["Cantidad_Deseada"]), axis=1)

        # 📌 Filtrar medicamentos que necesitan compra o análisis
        df_compra = df[
            (df["Cantidad_Necesaria_Ajustada"] > 0) |  
            (df["Critico_Abastecimiento"] != "🟩 No es crítico")
        ].copy()

        df_compra["Critico_Abastecimiento"] = df_compra["Critico_Abastecimiento"].astype(str)
        df_compra["Clasificacion_ABC"] = df_compra["Clasificacion_ABC"].astype(str)

        # 📌 Redondear todas las columnas numéricas a 2 decimales
        columnas_redondeo = [
            "Cantidad_Necesaria", "Cantidad_Necesaria_Ajustada", 
            "Consumo_Anual", "Rotacion_Inventario"
        ]
        df_compra[columnas_redondeo] = df_compra[columnas_redondeo].round(2)

        # 📌 Eliminar la columna "Consumo_Acumulado" para que no se muestre
        df_compra = df_compra.drop(columns=["Consumo_Acumulado"])

        # 📌 Mostrar tabla con análisis
        st.subheader(f"📊 Análisis de Inventario ({meses_abastecimiento} meses de abastecimiento)")
        st.dataframe(df_compra)

        # 📥 Permitir descarga del archivo procesado SIN la columna "Consumo_Acumulado"
        csv = df_compra.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Descargar análisis de inventario",
            data=csv,
            file_name=f"Analisis_Inventario_{meses_abastecimiento}M.csv",
            mime="text/csv"
        )
else:
    st.info("⚠️ Por favor, sube un archivo CSV para analizar el inventario.")

# Función para calcular la cantidad recomendada de compra
def calcular_compra(df):
    df["Frecuencia Administración"] = df["Frecuencia Administración"].apply(lambda x: 1 if x.lower() == "diaria" else 7 if x.lower() == "semanal" else 30)
    df["Consumo Total Mensual"] = df["Pacientes Estimados"] * df["Dosis Por Administración"] * (30 / df["Frecuencia Administración"])
    df["Stock de Seguridad"] = df["Consumo Total Mensual"] * 0.2  # 20% de margen de seguridad
    df["Cantidad Recomendada a Comprar"] = np.maximum(df["Consumo Total Mensual"] - df["Stock Actual"], 0) + df["Stock de Seguridad"]
    return df

st.markdown("---") # Línea divisoria para separar secciones

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Función para calcular la cantidad recomendada de compra
def calcular_compra(df):
    df["Frecuencia Administración"] = df["Frecuencia Administración"].apply(lambda x: 1 if x.lower() == "diaria" else 7 if x.lower() == "semanal" else 30)
    df["Consumo Total Mensual"] = df["Pacientes Estimados"] * df["Dosis Por Administración"] * (30 / df["Frecuencia Administración"])
    df["Stock de Seguridad"] = df["Consumo Total Mensual"] * 0.2  # 20% de margen de seguridad
    df["Cantidad Recomendada a Comprar"] = np.maximum(df["Consumo Total Mensual"] - df["Stock Actual"], 0) + df["Stock de Seguridad"]
    return df

# Configurar la aplicación Streamlit
st.title("Gestión de Compra de Medicamentos")

st.markdown("""
### Descripción de las variables:
- **Medicamento**: Nombre del medicamento a evaluar.
- **Presentación**: Forma en la que se comercializa (Tableta, Ampolla, Frasco, etc.).
- **Unidad de Medida**: Define si la compra se gestiona en "C/U" (cantidad unitaria) o "CTO" (cajas o conjuntos de unidades).
- **Frecuencia Administración**: Intervalo de administración (Diaria, Semanal, Mensual).
- **Dosis Por Administración**: Cantidad administrada por toma.
- **Duración del Tratamiento**: Duración en días o semanas.
- **Pacientes Estimados**: Número de pacientes que lo utilizarán por mes.
- **Stock Actual**: Cantidad de unidades en inventario.
""")

st.markdown("---") # Línea divisoria para separar secciones

# Número de medicamentos a evaluar
n = st.number_input("Ingrese el número de medicamentos a evaluar:", min_value=1, step=1)

# Listas para almacenar los datos ingresados
medicamentos = []
presentaciones = []
unidad_medida = []
frecuencia_administracion = []
dosis_por_administracion = []
duracion_tratamiento = []
pacientes_estimados = []
stock_actual = []

# Ingreso de datos de los medicamentos
for i in range(n):
    st.subheader(f"Datos del Medicamento {i+1}")
    medicamentos.append(st.text_input(f"Nombre del medicamento {i+1}:"))
    presentaciones.append(st.selectbox(f"Presentación del medicamento {i+1}:", ["Tableta", "Ampolla", "Frasco", "Cápsula", "Jarabe"]))
    unidad_medida.append(st.selectbox(f"Unidad de Medida del medicamento {i+1}:", ["C/U", "CTO"]))
    frecuencia_administracion.append(st.selectbox(f"Frecuencia de administración del medicamento {i+1}:", ["Diaria", "Semanal", "Mensual"]))
    dosis_por_administracion.append(st.number_input(f"Dosis por administración del medicamento {i+1}:", min_value=0.1, step=0.1))
    tipo_duracion = st.radio(f"¿La duración del tratamiento del medicamento {i+1} será en días o semanas?", ["Días", "Semanas"])
    if tipo_duracion == "Semanas":
        semanas = st.number_input(f"Duración del tratamiento en semanas del medicamento {i+1}:", min_value=1, step=1)
        duracion_tratamiento.append(semanas * 7)
    else:
        dias = st.number_input(f"Duración del tratamiento en días del medicamento {i+1}:", min_value=1, step=1)
        duracion_tratamiento.append(dias)
    pacientes_estimados.append(st.number_input(f"Número estimado de pacientes por mes para el medicamento {i+1}:", min_value=1, step=1))
    stock_actual.append(st.number_input(f"Stock actual disponible del medicamento {i+1}:", min_value=0, step=1))

st.markdown("---") # Línea divisoria para separar secciones

# Crear DataFrame con los datos ingresados
datos = {
    "Medicamento": medicamentos,
    "Presentación": presentaciones,
    "Unidad de Medida": unidad_medida,
    "Frecuencia Administración": frecuencia_administracion,
    "Dosis Por Administración": dosis_por_administracion,
    "Duración del Tratamiento": duracion_tratamiento,
    "Pacientes Estimados": pacientes_estimados,
    "Stock Actual": stock_actual
}
df = pd.DataFrame(datos)

# Calcular las compras recomendadas
if not df.empty:
    df = calcular_compra(df)
    st.subheader("Resultados de la Estimación")
    st.write(df)

    # Graficar los resultados
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["Medicamento"], df["Consumo Total Mensual"], label="Consumo Mensual", alpha=0.7, color='brown')
    ax.bar(df["Medicamento"], df["Cantidad Recomendada a Comprar"], label="Compra Recomendada", alpha=0.7, color='orange')
    ax.set_xticklabels(df["Medicamento"], rotation=45)
    ax.set_ylabel("Cantidad de Unidades")
    ax.set_title("Estimación de Consumo y Compra Recomendada")
    ax.legend()
    st.pyplot(fig)
