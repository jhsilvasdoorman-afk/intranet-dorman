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
    ["✨ Instalación Nueva", "🔍 Buscar/Consultar Edificios"]
)

# --- FUNCIÓN COMPROBADA PARA TRAER DATOS ---
@st.cache_data(ttl=5)  
def cargar_datos_desde_google():
    try:
        respuesta = requests.get(APPS_SCRIPT_URL, timeout=10)
        if respuesta.status_code == 200:
            js = respuesta.json()
            # Si el script viejo devolvió una lista directa en vez de un diccionario modular
            if isinstance(js, list):
                return {"precios": js, "instalaciones": []}
            return js
    except Exception as e:
        pass
    return {"precios": [], "instalaciones": []}

# Cargar datos de forma segura sin romper la app por KeyError
datos_completos = cargar_datos_desde_google()
catalogo_precios = datos_completos.get("precios", [])
historial_edificios = datos_completos.get("instalaciones", [])

# Convertir a tablas limpias
df_precios = pd.DataFrame(catalogo_precios) if catalogo_precios else pd.DataFrame(columns=["material", "precio", "unidad"])
df_historial = pd.DataFrame(historial_edificios) if historial_edificios else pd.DataFrame(columns=["fecha", "edificio", "material", "cantidad", "subtotal"])

# Normalizar columnas por si vienen del script viejo o nuevo
if not df_precios.empty and "Equipo / Material" in df_precios.columns:
    df_precios = df_precios.rename(columns={"Equipo / Material": "material", "Precio": "precio", "Unidad": "unidad"})

# =========================================================================
# MÓDULO 1: INSTALACIÓN NUEVA
# =========================================================================
if modulo == "✨ Instalación Nueva":
    st.header("🧰 Módulo: Registro de Instalación Nueva")
    
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
            # Manejo seguro si las llaves se llaman diferente
            col_nombre = "material" if "material" in df_precios.columns else df_precios.columns[0]
            lista_materiales = df_precios[col_nombre].unique()
            material_sel = st.selectbox("Seleccione el ítem del catálogo:", lista_materiales)
        with col_cant:
            cantidad_sel = st.number_input("Cantidad:", min_value=1, value=1, step=1)
        with col_btn:
            st.write("")
            st.write("")
            btn_agregar = st.button("🚀 Añadir Fila")

        if "carrito" not in st.session_state:
            st.session_state.carrito = []

        if btn_agregar:
            col_precio = "precio" if "precio" in df_precios.columns else df_precios.columns[1]
            fila_item = df_precios[df_precios[col_nombre] == material_sel].iloc[0]
            precio_uni = float(fila_item[col_precio])
            st.session_state.carrito.append({
                "fecha": str(fecha_instalacion),
                "edificio": nombre_edificio,
                "material": material_sel,
                "cantidad": cantidad_sel,
                "subtotal": precio_uni * cantidad_sel
            })
            st.toast(f"Añadido: {material_sel}")

        if st.session_state.carrito:
            st.markdown("### 📋 Resumen de Elementos a Instalar")
            df_actual = pd.DataFrame(st.session_state.carrito)
            
            df_vista = df_actual.copy()
            df_vista["subtotal"] = df_vista["subtotal"].apply(lambda x: f"${x:,.0f}")
            st.table(df_vista[["material", "cantidad", "subtotal"]])
            
            total_obra = df_actual["subtotal"].sum()
            st.metric("💰 INVERSIÓN TOTAL ESTIMADA", f"${total_obra:,.0f}")
            
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
                                "elementos": st.session_state.carrito
                            }
                            try:
                                envio = requests.post(APPS_SCRIPT_URL, json=payload)
                                res = envio.json()
                                if res.get("status") == "success":
                                    st.success(f"🎉 ¡Éxito! Edificio '{nombre_edificio}' registrado correctamente.")
                                    st.session_state.carrito = []
                                else:
                                    st.error(f"Error: {res.get('message')}")
                            except Exception as e:
                                st.error(f"Error de envío: {e}")
    else:
        st.warning("⚠️ El catálogo de precios no se pudo leer o está vacío. Revisa que tu Google Sheets tenga datos.")

# =========================================================================
# MÓDULO 2: BUSCAR / CONSULTAR EDIFICIOS
# =========================================================================
elif modulo == "🔍 Buscar/Consultar Edificios":
    st.header("🔍 Módulo: Consulta de Edificios e Infraestructura")
    
    if not df_historial.empty and "edificio" in df_historial.columns:
        edificios_existentes = df_historial["edificio"].unique()
        edificio_buscado = st.selectbox("🎯 Selecciona el Edificio que deseas revisar:", edificios_existentes)
        
        if edificio_buscado:
            st.markdown(f"### 🏢 Historial de Equipamiento: **{edificio_buscado}**")
            df_filtrado = df_historial[df_historial["edificio"] == edificio_buscado]
            
            df_filtrado_vista = df_filtrado.copy()
            df_filtrado_vista["subtotal"] = df_filtrado_vista["subtotal"].apply(lambda x: float(x))
            df_filtrado_vista["subtotal_format"] = df_filtrado_vista["subtotal"].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(
                df_filtrado_vista[["fecha", "material", "cantidad", "subtotal_format"]].rename(
                    columns={"fecha": "📅 Fecha", "material": "🔧 Componente", "cantidad": "📦 Cant.", "subtotal_format": "💰 Subtotal"}
                ),
                use_container_width=True
            )
            
            costo_acumulado = df_filtrado_vista["subtotal"].sum()
            st.metric(label="Valor Total de Infraestructura Instalada", value=f"${costo_acumulado:,.0f}")
    else:
        st.info("ℹ️ No hay registros históricos en la pestaña 'Instalaciones' de tu Google Sheets todavía.")
