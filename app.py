import streamlit as st
import requests
import pandas as pd

# Configuración básica de la página de la Intranet
st.set_page_config(page_title="Intranet DORMAN LATAM", page_icon="🏢", layout="wide")

# URL del puente de Google que creaste
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwJoUMjlCg5lA19Dzd5H_Wdpxm5zhyasCeErLnzGGX6thpABMLAWac0-WC6rnCe3s4_8w/exec"

st.title("🏢 Intranet Operativa - DORMAN LATAM")
st.subheader("🧰 Módulo: Materiales y Equipos para Instalación")
st.markdown("---")

# 1. PASO A: Datos de la visita técnica
st.sidebar.header("📋 Datos del Edificio")
nombre_edificio = st.sidebar.text_input("Nombre del Edificio / Condominio:", placeholder="Ej: Mirador del Parque")

# 2. PASO B: Conexión y lectura del Catálogo de Precios Maestro
@st.cache_data(ttl=60)  # Recarga los precios del Sheet automáticamente cada minuto
def obtener_catalogo_maestro():
    try:
        respuesta = requests.get(APPS_SCRIPT_URL)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            # Convertimos la respuesta en una tabla limpia de Python
            df = pd.DataFrame(datos)
            df.columns = ["Equipo / Material", "Precio", "Unidad"]
            return df
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return pd.DataFrame(columns=["Equipo / Material", "Precio", "Unidad"])

df_maestro = obtener_catalogo_maestro()

# Inicializar la lista de materiales elegidos si no existe en la sesión
if "carrito_instalacion" not in st.session_state:
    st.session_state.carrito_instalacion = []

# Interfaz para añadir materiales
if not df_maestro.empty:
    st.markdown("### ➕ Añadir Elementos a la Instalación")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        item_seleccionado = st.selectbox("Selecciona el Equipo o Material:", df_maestro["Equipo / Material"].unique())
    with col2:
        cantidad = st.number_input("Cantidad Requerida:", min_value=1, value=1, step=1)
        
    if st.button("🚀 Añadir a la Lista"):
        # Buscar el precio unitario del ítem seleccionado
        fila_item = df_maestro[df_maestro["Equipo / Material"] == item_seleccionado].iloc[0]
        precio_unid = float(fila_item["Precio"])
        subtotal = precio_unid * cantidad
        
        # Guardar en la lista temporal de la pantalla
        st.session_state.carrito_instalacion.append({
            "material": item_seleccionado,
            "precio": precio_unid,
            "cantidad": cantidad,
            "subtotal": subtotal
        })
        st.success(f"Añadido: {cantidad}x {item_seleccionado}")
else:
    st.warning("No se pudieron cargar datos. Asegúrate de que el archivo Master_Precios_Doorman tenga datos cargados.")

st.markdown("---")

# 3. PASO C: Mostrar resumen del presupuesto y enviar a Google Drive
if st.session_state.carrito_instalacion:
    st.markdown(f"### 📊 Resumen de Requerimientos: **{nombre_edificio if nombre_edificio else 'Edificio por definir'}**")
    
    # Mostrar tabla bonita en pantalla
    df_instalacion = pd.DataFrame(st.session_state.carrito_instalacion)
    df_instalacion.columns = ["Equipo / Material", "Precio Unitario", "Cantidad", "Subtotal"]
    
    # Formatear la tabla visual para que use signos de dinero
    df_visual = df_instalacion.copy()
    df_visual["Precio Unitario"] = df_visual["Precio Unitario"].apply(lambda x: f"${x:,.0f}")
    df_visual["Subtotal"] = df_visual["Subtotal"].apply(lambda x: f"${x:,.0f}")
    st.table(df_visual)
    
    # Calcular e indicar el Gran Total
    gran_total = df_instalacion["Subtotal"].sum()
    st.metric(label="💰 COSTO TOTAL ESTIMADO DE INSTALACIÓN", value=f"${gran_total:,.0f}")
    
    # Botón para limpiar la lista si el técnico se equivoca
    if st.button("🗑️ Limpiar Todo e Iniciar de Nuevo"):
        st.session_state.carrito_instalacion = []
        st.rerun()
        
    st.markdown("---")
    
    # Botón de Guardado Final
    if st.button("💾 GUARDAR Y CREAR DOCUMENTO EN GOOGLE DRIVE"):
        if not nombre_edificio.strip():
            st.error("⚠️ Por favor, ingresa el NOMBRE DEL EDIFICIO en la barra lateral izquierda antes de guardar.")
        else:
            with st.spinner("Creando archivo de cubicación en tu Drive... Por favor espera."):
                # Empaquetamos la información para mandarla al puente de Google Sheets
                datos_envio = {
                    "edificio": nombre_edificio,
                    "elementos": st.session_state.carrito_instalacion,
                    "total": gran_total
                }
                
                try:
                    envio = requests.post(APPS_SCRIPT_URL, json=datos_envio)
                    resultado = envio.json()
                    
                    if resultado.get("status") == "success":
                        st.success(f"🎉 ¡Éxito! El archivo 'Instalacion_{nombre_edificio}' se creó en tu carpeta de Google Drive.")
                        st.markdown(f"🔗 [Haga clic aquí para abrir el documento creado]({resultado.get('url')})")
                        # Limpiamos el formulario tras guardar con éxito
                        st.session_state.carrito_instalacion = []
                    else:
                        st.error(f"El servidor respondió con un error: {resultado.get('message')}")
                except Exception as e:
                    st.error(f"Hubo un problema al enviar los datos a Google Drive: {e}")
