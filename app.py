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

st.markdown("---") # Línea divisoria para separar secciones

# Función para calcular la cantidad recomendada de compra y ROP
def calcular_compra(df):
    if "Frecuencia Administración" in df.columns:
        df["Frecuencia Administración"] = df["Frecuencia Administración"].astype(str).str.lower()
        df["Frecuencia Administración"] = df["Frecuencia Administración"].apply(
            lambda x: 1 if x == "diaria" else 7 if x == "semanal" else 30 if x == "mensual" else 
            6 if x == "cada 4 horas" else 4 if x == "cada 6 horas" else 3 if x == "cada 8 horas" else 2 if x == "cada 12 horas" else 1)
    
    # Calcular el consumo mensual correctamente
    df["Consumo Total Mensual"] = df["Pacientes Estimados"] * df["Dosis Por Administración"] * (df["Frecuencia Administración"] * 30)
    
    # Calcular el consumo diario promedio
    df["Consumo Diario Promedio"] = df["Consumo Total Mensual"] / 30

    # Calcular el stock de seguridad (20% del consumo mensual)
    df["Stock de Seguridad"] = df["Consumo Total Mensual"] * 0.2

    # Calcular el Punto de Reorden (ROP)
    df["Punto de Reorden (ROP)"] = (df["Consumo Diario Promedio"] * df["Tiempo de Entrega"]) + df["Stock de Seguridad"]

    # 🔹 **Corrección: convertir a cientos si es CTO**
    columnas_a_convertir = ["Consumo Total Mensual", "Consumo Diario Promedio", "Stock de Seguridad", "Punto de Reorden (ROP)", "Cantidad Recomendada a Comprar", "Stock Actual"]
    df.loc[df["Unidad de Medida"] == "CTO", columnas_a_convertir] /= 100
    df.loc[df["Unidad de Medida"] == "CTO", columnas_a_convertir] = df.loc[df["Unidad de Medida"] == "CTO", columnas_a_convertir].round(2)

    return df

# Configurar la aplicación Streamlit
st.title("Gestión de Compra de Medicamentos - Modelo de Reposición con Punto de Reorden")

st.markdown("---") # Línea divisoria para separar secciones

# Crear o cargar el DataFrame global
if "medicamentos_df" not in st.session_state:
    st.session_state.medicamentos_df = pd.DataFrame(columns=[
        "Medicamento", "Presentación", "Unidad de Medida", "Frecuencia Administración", "Dosis Por Administración",
        "Duración del Tratamiento", "Pacientes Estimados", "Stock Actual", "Tiempo de Entrega"
    ])

# Ingreso de un solo medicamento a la vez
st.subheader("Ingreso de Medicamento")
nombre = st.text_input("Nombre del medicamento:")
presentacion = st.selectbox("Presentación:", ["Tableta", "Ampolla", "Frasco", "Cápsula"], index=0)
unidad_medida = st.selectbox("Unidad de Medida:", ["C/U", "CTO"], index=0)
frecuencia_administracion = st.selectbox("Frecuencia de Administración:", ["Diaria", "Semanal", "Mensual", "Cada 4 horas", "Cada 6 horas", "Cada 8 horas", "Cada 12 horas"], index=0)
dosis_por_administracion = st.number_input("Dosis por Administración, use solo números desde 0.1 en adelante:", min_value=0.1, step=0.1, value=0.1)
tipo_duracion = st.radio("¿La duración del tratamiento será en días o semanas?", ["Días", "Semanas"], index=0)

if tipo_duracion == "Semanas":
    duracion_tratamiento = st.number_input("Duración del tratamiento en semanas:", min_value=1, step=1, value=1) * 7
else:
    duracion_tratamiento = st.number_input("Duración del tratamiento en días:", min_value=1, step=1, value=1)

pacientes_estimados = st.number_input("Número estimado de pacientes por mes:", min_value=1, step=1, value=1)
stock_actual = st.number_input("Stock actual disponible:", min_value=0, step=1, value=0)
tiempo_entrega = st.number_input("Tiempo de entrega (días):", min_value=1, step=1, value=1)

# Validación para evitar datos vacíos
if st.button("Agregar Medicamento"):
    if nombre.strip() == "":
        st.error("El nombre del medicamento no puede estar vacío.")
    else:
        nuevo_medicamento = pd.DataFrame([[
            nombre.strip(), presentacion, unidad_medida, frecuencia_administracion,
            float(dosis_por_administracion), int(duracion_tratamiento), int(pacientes_estimados), int(stock_actual), int(tiempo_entrega)
        ]], columns=st.session_state.medicamentos_df.columns)
        
        st.session_state.medicamentos_df = pd.concat([st.session_state.medicamentos_df, nuevo_medicamento], ignore_index=True)
        st.success(f"Medicamento {nombre} agregado exitosamente!")

st.markdown("---") # Línea divisoria para separar secciones

# Mostrar la tabla solo si hay datos
if not st.session_state.medicamentos_df.empty:
    st.subheader("Medicamentos Ingresados")
    st.write(st.session_state.medicamentos_df)

    # **🔴 Nueva sección: Eliminar Medicamento**
    st.subheader("Eliminar Medicamento")
    
    # Obtener lista de medicamentos para eliminar
    medicamentos_lista = st.session_state.medicamentos_df["Medicamento"].tolist()
    
    # Verificar que hay medicamentos disponibles para eliminar
    if medicamentos_lista:
        medicamento_a_eliminar = st.selectbox("Seleccione el medicamento a eliminar:", medicamentos_lista)
        
        if st.button("Eliminar Medicamento"):
            st.session_state.medicamentos_df = st.session_state.medicamentos_df[st.session_state.medicamentos_df["Medicamento"] != medicamento_a_eliminar]
            st.success(f"Medicamento {medicamento_a_eliminar} eliminado exitosamente.")
    
    # Calcular las compras recomendadas y el ROP
    df_calculado = calcular_compra(st.session_state.medicamentos_df.copy())
    st.subheader("Resultados de la Estimación")
    st.write(df_calculado)

    # Alerta si el stock está por debajo del ROP
    for index, row in df_calculado.iterrows():
        if row["Stock Actual"] < row["Punto de Reorden (ROP)"]:
            st.warning(f"⚠️ ¡El medicamento {row['Medicamento']} está por debajo del punto de reorden ({row['Punto de Reorden (ROP)']})! Se recomienda hacer un nuevo pedido.")
