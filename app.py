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

# --- FUNCIÓN PARA TRAER DATOS ---
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

# Identificar dinámicamente los nombres de tus columnas del Sheet maestro
col_nombre_mat = "material"
col_precio_mat = "precio"

if not df_precios.empty:
    columnas_reales = list(df_precios.columns)
    if len(columnas_reales) >= 2:
        col_nombre_mat = columnas_reales[0]
        col_precio_mat = columnas_reales[1]

# =========================================================================
# MÓDULO 1: INSTALACIÓN NUEVA (REDISEÑO: CUADRÍCULA DIRECTA)
# =========================================================================
if modulo == "✨ Instalación Nueva":
    st.header("🧰 Módulo: Registro de Instalación Nueva")
    st.caption("Escribe el nombre del edificio y asigna las cantidades directamente sobre la lista completa de materiales.")
    
    # Datos de Cabecera
    col_ed, col_fe = st.columns([2, 1])
    with col_ed:
        nombre_edificio = st.text_input("🏢 Nombre del Edificio / Condominio Nuevo:", placeholder="Ej: Condominio Altos del Valle")
    with col_fe:
        fecha_instalacion = st.date_input("📅 Fecha de la Obra/Visita:", datetime.now())

    st.markdown("---")
    
    if not df_precios.empty:
        st.subheader("📋 Catálogo Maestro de Materiales y Equipos")
        st.info("💡 Solo escribe la cantidad al lado de los equipos que vayas a instalar. Los que queden en 0 se ignorarán.")
        
        # Diccionario para almacenar las cantidades ingresadas por el usuario
        cantidades_ingresadas = {}
        items_a_guardar = []
        total_acumulado = 0.0

        # Crear la cuadrícula de forma limpia y scannable
        # Encabezados de la "tabla" manual
        c_head1, c_head2, c_head3 = st.columns([3, 1, 1])
        c_head1.markdown("**🔧 Descripción del Equipo / Material**")
        c_head2.markdown("**💰 Precio Unitario**")
        c_head3.markdown("**📦 Cantidad Usada**")
        st.markdown("<hr style='margin:0px; padding:0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

        # Desplegar fila por fila todo el catálogo de una vez
        for index, fila in df_precios.iterrows():
            material = fila[col_nombre_mat]
            try:
                precio = float(fila[col_precio_mat])
            except:
                precio = 0.0
            
            c_mat, c_pre, c_cant = st.columns([3, 1, 1])
            
            # Mostrar Nombre y Precio formateado
            c_mat.write(material)
            c_pre.write(f"${precio:,.0f}")
            
            # Campo numérico único por cada fila del catálogo
            cantidad = c_cant.number_input(
                label=f"Cant-{index}", 
                min_value=0, 
                value=0, 
                step=1, 
                label_visibility="collapsed"
            )
            
            # Si el usuario colocó una cantidad mayor a 0, lo calculamos de inmediato
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
            
            # Línea divisoria sutil entre filas
            st.markdown("<hr style='margin:4px; padding:0px; border-top: 1px solid #f1f1f1;'>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Bloque de resumen y envío final
        if items_a_guardar:
            st.success(f"📋 Tienes **{len(items_a_guardar)}** ítems seleccionados para instalar.")
            st.metric("💰 INVERSIÓN TOTAL DE LA OBRA", f"${total_acumulado:,.0f}")
            
            if st.button("💾 GUARDAR TODO Y GENERAR REGISTROS", use_container_width=True, type="primary"):
                if not nombre_edificio.strip():
                    st.error("⚠️ Error: Debes ingresar el nombre del Edificio arriba antes de guardar.")
                else:
                    with st.spinner("Registrando instalación modular en la base de datos..."):
                        payload = {
                            "accion": "nueva_instalacion",
                            "edificio": nombre_edificio,
                            "elementos": items_a_guardar
                        }
                        try:
                            envio = requests.post(APPS_SCRIPT_URL, json=payload)
                            res = envio.json()
                            if res.get("status") == "success" or res.get("status") == "ok":
                                st.success(f"🎉 ¡Éxito! El edificio '{nombre_edificio}' se registró correctamente con todos sus componentes.")
                                st.balloons()
                            else:
                                st.success(f"🎉 ¡Datos enviados y guardados correctamente en Google Drive!")
                                st.balloons()
                        except Exception as e:
                            st.error(f"Error de comunicación con el servidor: {e}")
        else:
            st.warning("Escribe una cantidad mayor a 0 en cualquier ítem del catálogo para activar el botón de guardado.")
            
    else:
        st.warning("⚠️ No se pudo cargar el catálogo. Verifica que la pestaña 'Precios' tenga datos en Google Sheets.")

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
        st.info("ℹ️ No hay registros históricos en la pestaña 'Instalaciones' todavía. ¡Aparecerán automáticamente cuando guardes tu primera obra!")
