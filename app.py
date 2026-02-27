import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO

# 1. CONFIGURACIÓN MOBILE-FIRST
st.set_page_config(page_title="Meli Auditoría Mobile", layout="centered", page_icon="⚽")

# CSS para optimización de Teléfono
st.markdown("""
    <style>
    /* Fondo y contenedores */
    .stApp { background-color: #f5f5f5; }
    
    /* Header compacto para móvil */
    .main-header {
        background-color: #fff159;
        padding: 15px;
        border-radius: 0 0 15px 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .main-header h1 { font-size: 20px !important; color: #333; }

    /* Botones GIGANTES para el pulgar */
    .stButton>button {
        width: 100% !important;
        height: 60px !important;
        background-color: #3483fa !important;
        color: white !important;
        border-radius: 12px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 10px;
    }
    
    /* Inputs más grandes para tocar fácil */
    .stTextInput>div>div>input {
        height: 50px !important;
        font-size: 18px !important;
        border-radius: 10px !important;
    }

    /* Ajuste de imágenes en móvil */
    .stImage > img {
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE IMAGEN ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

def dibujar_mascota_llenado(porcentaje):
    img_v = get_base64("mascota_vacia.png")
    img_l = get_base64("mascota_llena.png")
    if not img_v or not img_l: return ""
    p = min(max(porcentaje, 0), 100)
    clip_value = f"inset({100 - p}% 0 0 0)"
    html = f"""
    <div style="position: relative; width: 150px; height: 220px; margin: 0 auto;">
        <img src="data:image/png;base64,{img_v}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1;">
        <img src="data:image/png;base64,{img_l}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; clip-path: {clip_value}; transition: clip-path 1s ease-in-out;">
    </div>
    <div style="text-align:center; font-weight:bold; font-size:18px; color:#3483fa; margin-bottom:20px;">{porcentaje:.1f}% Validado</div>
    """
    return html

# --- 3. LÓGICA DE REGISTRO ---
if 'historial' not in st.session_state:
    st.session_state.historial = []

def registrar_y_limpiar(codigo, desc, piezas, ov):
    st.session_state.historial.append({
        "codigo": codigo, "descripcion": desc, "piezas": piezas, "ov": ov
    })
    st.session_state.scanner_input = "" # Auto-reset del buscador
    st.toast(f"✅ Registrado: {desc}")

# --- 4. CARGA DE DRIVE ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        df['codigo'] = df['codigo'].astype(str).str.strip()
        return df
    except: return None

# --- 5. INTERFAZ MÓVIL ---
st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)

df_ov = cargar_datos()

if df_ov is not None:
    # Columnas dinámicas
    col_codigo = 'codigo'
    col_ov = 'ov'
    col_desc = [c for c in df_ov.columns if 'desc' in c][0]
    col_cant = [c for c in df_ov.columns if 'cant' in c][0]

    # BUSCADOR (Lo primero que ves)
    codigo_input = st.text_input("👇 Escanea o escribe el código:", key="scanner_input", placeholder="Código aquí...").strip()

    if codigo_input:
        res = df_ov[df_ov[col_codigo] == codigo_input]

        if not res.empty:
            item = res.iloc[0]
            
            # Info del producto en vertical para móvil
            st.markdown(f"### {item[col_desc]}")
            
            # Foto del producto
            foto_p = f"{item[col_codigo]}.jpg"
            if os.path.exists(foto_p):
                st.image(foto_p, use_container_width=True)
            
            # Datos y Contador
            limite = int(item[col_cant])
            ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == codigo_input)
            
            c1, c2 = st.columns(2)
            c1.metric("Esperado", f"{limite} pzs")
            c2.metric("Llevas", f"{ya_auditado} pzs")
            
            cant_ahora = st.number_input("¿Cuántas piezas encontraste?", min_value=1, value=1, step=1)
            
            if (ya_auditado + cant_ahora) > limite:
                st.error("🚨 CANTIDAD EXCEDIDA")
            else:
                st.button("CONFIRMAR REGISTRO ✅", on_click=registrar_y_limpiar, 
                          args=(codigo_input, item[col_desc], cant_ahora, item[col_ov]))

    # --- AVANCE (MASCOTA) ---
    st.divider()
    if st.session_state.historial:
        ovs = pd.DataFrame(st.session_state.historial)[col_ov].unique()
        total_e = df_ov[df_ov[col_ov].isin(ovs)][col_cant].sum()
        total_a = sum(x['piezas'] for x in st.session_state.historial)
        avance = (total_a / total_e) * 100 if total_e > 0 else 0
        
        st.markdown(dibujar_mascota_llenado(avance), unsafe_allow_html=True)
        
        # Botones de reporte abajo
        with st.expander("📊 Ver Resumen y Exportar"):
            df_res = pd.DataFrame(st.session_state.historial).groupby([col_codigo, 'descripcion', col_ov])['piezas'].sum().reset_index()
            st.dataframe(df_res, use_container_width=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_res.to_excel(writer, index=False)
            st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Auditoria_Mars.xlsx")
            
            if st.button("🗑️ REINICIAR TODO"):
                st.session_state.historial = []
                st.rerun()
    else:
        st.info("Escanea un material para comenzar la auditoría.")

else:
    st.error("Error de conexión con Drive.")