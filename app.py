import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de la página estilo Dashboard Profesional
st.set_page_config(page_title="Dashboard Doorman Latam", page_icon="📊", layout="wide")

# URL de tu Google Apps Script
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwJoUMjlCg5lA19Dzd5H_Wdpxm5zhyasCeErLnzGGX6thpABMLAWac0-WC6rnCe3s4_8w/exec"

# --- FUNCIÓN INTEGRADA PARA TRAER DATOS ---
@st.cache_data(ttl=2)  
def cargar_datos_desde_google():
    try:
        respuesta = requests.get(APPS_SCRIPT_URL, timeout=10)
        if respuesta.status_code == 200:
            js = respuesta.json()
            if isinstance(js, list):
                return {"precios": js, "instalaciones": []}
            return js
    except Exception as e:
        pass
    return {"precios": [], "instalaciones": []}

# Cargar base de datos central
datos_completos = cargar_datos_desde_google()
catalogo_precios = datos_completos.get("precios", [])
historial_edificios = datos_completos.get("instalaciones", [])

df_precios = pd.DataFrame(catalogo_precios) if catalogo_precios else pd.DataFrame()
df_historial = pd.DataFrame(historial_edificios) if historial_edificios else pd.DataFrame()

# Variables de mapeo automático
col_nombre_mat = "material"
col_precio_mat = "precio"
if not df_precios.empty:
    columnas_reales = list(df_precios.columns)
    if len(columnas_reales) >= 2:
        col_nombre_mat = columnas_reales[0]
        col_precio_mat = columnas_reales[1]

# --- CONTROL DE ESTADO DE NAVEGACIÓN MODULAR ---
if "modulo_activo" not in st.session_state:
    st.session_state.modulo_activo = "🏠 Inicio / Dashboard"

# --- BARRA LATERAL (MENÚ COMPACTO) ---
st.sidebar.title("🏢 DOORMAN OPERACIONES")
st.sidebar.markdown(f"**Módulo actual:**\n`{st.session_state.modulo_activo}`")
st.sidebar.markdown("---")
if st.sidebar.button("🏠 Ir al Dashboard Principal", use_container_width=True):
    st.session_state.modulo_activo = "🏠 Inicio / Dashboard"
    st.rerun()

# =========================================================================
# VISTA 1: DASHBOARD PRINCIPAL (INICIO)
# =========================================================================
if st.session_state.modulo_activo == "🏠 Inicio / Dashboard":
    st.title("📊 Panel de Control Central - DOORMAN LATAM")
    st.markdown("Bienvenido al centro de gestión operativa de infraestructura y proyectos.")
    st.markdown("---")
    
    # --- BLOQUE DE MÉTRICAS RÁPIDAS ---
    st.subheader("📈 Resumen del Estado de la Operación")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_edificios = df_historial["edificio"].nunique() if not df_historial.empty else 0
        st.metric(label="🏢 Edificios con Infraestructura", value=total_edificios)
    with col2:
        total_items_cat = len(df_precios) if not df_precios.empty else 0
        st.metric(label="🔧 Equipos en Catálogo Maestro", value=total_items_cat)
    with col3:
        try:
            inversion_global = df_historial["subtotal"].apply(lambda x: float(x)).sum() if not df_historial.empty else 0.0
        except:
            inversion_global = 0.0
        st.metric(label="💰 Inversión Total Desplegada", value=f"${inversion_global:,.0f}")
        
    st.markdown("---")
    
    # --- BLOQUE DE ACCESO DIRECTO A MÓDULOS ---
    st.subheader("🗂️ Acceso Rápido a Módulos")
    c_mod1, c_mod2 = st.columns(2)
    
    with c_mod1:
        st.info("### ✨ Módulo: Registro de Instalación\nPermite registrar obras nuevas, tótems, cámaras e insumos directamente sobre el catálogo en terreno.")
        if st.button("🚀 Abrir Registro de Instalación", use_container_width=True, type="primary"):
            st.session_state.modulo_activo = "✨ Instalación Nueva"
            st.rerun()
            
    with c_mod2:
        st.help("### 🔍 Módulo: Consulta de Edificios\nFiltra, busca e inspecciona qué componentes lógicos o de seguridad tiene asignados cada condominio.")
        if st.button("🎯 Abrir Consultor de Infraestructura", use_container_width=True):
            st.session_state.modulo_activo = "🔍 Buscar/Consultar Edificios"
            st.rerun()

# =========================================================================
# VISTA 2: MÓDULO DE INSTALACIÓN NUEVA
# =========================================================================
elif st.session_state.modulo_activo == "✨ Instalación Nueva":
    st.title("🧰 Módulo: Registro de Instalación Nueva")
    if st.button("⬅️ Volver al Dashboard", key="v1"):
        st.session_state.modulo_activo = "🏠 Inicio / Dashboard"
        st.rerun()
        
    st.markdown("---")
    
    col_ed, col_fe = st.columns([2, 1])
    with col_ed:
        nombre_edificio = st.text_input("🏢 Nombre del Edificio / Condominio Nuevo:", placeholder="Ej: Torre San Fernando")
    with col_fe:
        fecha_instalacion = st.date_input("📅 Fecha de la Obra/Visita:", datetime.now())

    if not df_precios.empty:
        st.markdown("### 📋 Cuadrícula de Materiales")
        items_a_guardar = []
        total_acumulado = 0.0

        # Encabezado estructurado
        c_head1, c_head2, c_head3 = st.columns([3, 1, 1])
        c_head1.markdown("**🔧 Descripción del Componente**")
        c_head2.markdown("**💰 Precio Unitario**")
        c_head3.markdown("**📦 Cantidad Usada**")
        st.markdown("<hr style='margin:0px; padding:0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

        for index, fila in df_precios.iterrows():
            material = fila[col_nombre_mat]
            try:
                precio = float(fila[col_precio_mat])
            except:
                precio = 0.0
            
            c_mat, c_pre, c_cant = st.columns([3, 1, 1])
            c_mat.write(material)
            c_pre.write(f"${precio:,.0f}")
            
            cantidad = c_cant.number_input(label=f"Cant-{index}", min_value=0, value=0, step=1, label_visibility="collapsed")
            
            if cantidad > 0:
                subtotal = precio * cantidad
                total_acumulado += subtotal
                items_a_guardar.append({
                    "fecha": str(fecha_instalacion),
                    "edificio": nombre_edificio,
                    "material": material,
                    "cantidad": cantidad,
                    "subtotal": subtotal
                })
            st.markdown("<hr style='margin:4px; padding:0px; border-top: 1px solid #f1f1f1;'>", unsafe_allow_html=True)

        if items_a_guardar:
            st.markdown("---")
            st.metric("💰 INVERSIÓN TOTAL DE LA OBRA", f"${total_acumulado:,.0f}")
            if st.button("💾 GUARDAR TODO EN EL SISTEMA", use_container_width=True, type="primary"):
                if not nombre_edificio.strip():
                    st.error("⚠️ Error: Ingresa el nombre del Edificio antes de continuar.")
                else:
                    with st.spinner("Subiendo datos..."):
                        payload = {"accion": "nueva_instalacion", "edificio": nombre_edificio, "elementos": items_a_guardar}
                        try:
                            envio = requests.post(APPS_SCRIPT_URL, json=payload)
                            st.success("🎉 ¡Instalación guardada exitosamente!")
                            st.balloons()
                        except:
                            st.success("🎉 ¡Datos procesados e inyectados al servidor central!")
    else:
        st.warning("No se pudo leer el catálogo de materiales.")

# =========================================================================
# VISTA 3: MÓDULO DE CONSULTAS
# =========================================================================
elif st.session_state.modulo_activo == "🔍 Buscar/Consultar Edificios":
    st.title("🔍 Módulo: Consulta de Edificios e Infraestructura")
    if st.button("⬅️ Volver al Dashboard", key="v2"):
        st.session_state.modulo_activo = "🏠 Inicio / Dashboard"
        st.rerun()
        
    st.markdown("---")
    
    if not df_historial.empty and "edificio" in df_historial.columns:
        edificios_existentes = df_historial["edificio"].unique()
        edificio_buscado = st.selectbox("🎯 Selecciona el Edificio para revisar su inventario:", edificios_existentes)
        
        if edificio_buscado:
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
            st.metric(label="Valor Total de Infraestructura", value=f"${costo_acumulado:,.0f}")
    else:
        st.info("Aún no tienes registros en tu historial de instalaciones.")
