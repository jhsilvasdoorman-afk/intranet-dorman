import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de la interfaz
st.set_page_config(page_title="Intranet DORMAN LATAM", page_icon="🏢", layout="wide")

# URL de tu Google Apps Script
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwJoUMjlCg5lA19Dzd5H_Wdpxm5zhyasCeErLnzGGX6thpABMLAWac0-WC6rnCe3s4_8w/exec"

st.title("🏢 Sistema de Gestión Operativa - DORMAN LATAM")
st.markdown("---")

# --- NAVEGACIÓN POR MÓDULOS ---
st.sidebar.title("🗂️ Módulos del Sistema")
modulo = st.sidebar.radio(
    "Selecciona el módulo en el que deseas trabajar:",
    ["✨ Instalación Nueva", "🔍 Buscar/Consultar Edificios", "📦 Malla de Turnos / Inventario (Próximamente)"]
)

# --- FUNCIÓN PARA TRAER DATOS DE GOOGLE ---
@st.cache_data(ttl=10)  # Se actualiza rápido para ver los cambios
def cargar_datos_desde_google():
    try:
        respuesta = requests.get(APPS_SCRIPT_URL)
        if respuesta.status_code == 200:
            return respuesta.json()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return {}

# Cargar la base de datos actual de Google
datos_completos = cargar_datos_desde_google()
catalogo_precios = datos_completos.get("precios", [])
historial_edificios = datos_completos.get("instalaciones", [])

# Convertir a Tablas de Python (DataFrames)
df_precios = pd.DataFrame(catalogo_precios) if catalogo_precios else pd.DataFrame(columns=["material", "precio", "unidad"])
df_historial = pd.DataFrame(historial_edificios) if historial_edificios else pd.DataFrame(columns=["fecha", "edificio", "material", "cantidad", "subtotal"])


# =========================================================================
# MÓDULO 1: INSTALACIÓN NUEVA
# =========================================================================
if modulo == "✨ Instalación Nueva":
    st.header("🧰 Módulo: Registro de Instalación Nueva")
    st.caption("Usa este formulario en terreno para cubicaciones y asignación de equipos a un nuevo condominio.")
    
    # Formulario Principal integrado en la pantalla
    col_ed, col_fe = st.columns([2, 1])
    with col_ed:
        nombre_edificio = st.text_input("🏢 Nombre del Edificio / Condominio Nuevo:", placeholder="Ej: Condominio Altos del Valle")
    with col_fe:
        fecha_instalacion = st.date_input("📅 Fecha de la Obra/Visita:", datetime.now())

    st.markdown("---")
    
    if not df_precios.empty:
        st.subheader("➕ Agregar Materiales y Equipos")
        col_mat, col_cant, col_btn = st.columns([2, 1, 1])
        
        with col_mat:
            lista_materiales = df_precios["material"].unique()
            material_sel = st.selectbox("Seleccione el ítem del catálogo:", lista_materiales)
        with col_cant:
            cantidad_sel = st.number_input("Cantidad:", min_value=1, value=1, step=1)
        with col_btn:
            st.write("") # Espacio estético
            st.write("")
            btn_agregar = st.button("🚀 Añadir Fila")

        # Inicializar el carrito de la sesión si no existe
        if "carrito" not in st.session_state:
            st.session_state.carrito = []

        if btn_agregar:
            # Buscar precio del ítem elegido
            fila_item = df_precios[df_precios["material"] == material_sel].iloc[0]
            precio_uni = float(fila_item["precio"])
            st.session_state.carrito.append({
                "fecha": str(fecha_instalacion),
                "edificio": nombre_edificio,
                "material": material_sel,
                "cantidad": cantidad_sel,
                "subtotal": precio_uni * cantidad_sel
            })
            st.toast(f"Añadido: {material_sel}")

        # Mostrar tabla del presupuesto actual si tiene ítems
        if st.session_state.carrito:
            st.markdown("### 📋 Resumen de Elementos a Instalar")
            df_actual = pd.DataFrame(st.session_state.carrito)
            
            # Formatear visualmente para el usuario
            df_vista = df_actual.copy()
            df_vista["subtotal"] = df_vista["subtotal"].apply(lambda x: f"${x:,.0f}")
            st.table(df_vista[["material", "cantidad", "subtotal"]])
            
            total_obra = df_actual["subtotal"].sum()
            st.metric("💰 INVERSIÓN TOTAL ESTIMADA", f"${total_obra:,.0f}")
            
            # Botones de Acción final
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Limpiar Planilla"):
                    st.session_state.carrito = []
                    st.rerun()
            with c2:
                if st.button("💾 GUARDAR INSTALACIÓN Y REGISTRAR EDIFICIO"):
                    if not nombre_edificio.strip():
                        st.error("⚠️ Debes asignar un nombre al Edificio antes de guardar.")
                    else:
                        with st.spinner("Guardando en el sistema central..."):
                            payload = {
                                "accion": "nueva_instalacion",
                                "edificio": nombre_edificio,
                                "elementos": st.session
