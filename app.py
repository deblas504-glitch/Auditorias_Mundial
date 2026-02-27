import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO

# 1. CONFIGURACIÓN MOBILE-FIRST
st.set_page_config(page_title="Meli Auditoría Mobile", layout="centered", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .main-header {
        background-color: #fff159; padding: 15px; border-radius: 0 0 15px 15px;
        text-align: center; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%; height: 60px; background-color: #3483fa; color: white;
        border-radius: 12px; font-size: 18px; font-weight: bold; border: none;
    }
    /* Estilo para el mensaje tipo Candy Crush */
    .level-up {
        text-align: center; color: #FFD700; font-size: 24px; font-weight: bold;
        text-shadow: 2px 2px #000; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES TÉCNICAS ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def dibujar_mascota(porcentaje):
    img_v = get_base64("mascota_vacia.png")
    img_l = get_base64("mascota_llena.png")
    if not img_v or not img_l: return ""
    p = min(max(porcentaje, 0), 100)
    clip_value = f"inset({100 - p}% 0 0 0)"
    return f'''
    <div style="position: relative; width: 150px; height: 220px; margin: 0 auto;">
        <img src="data:image/png;base64,{img_v}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1;">
        <img src="data:image/png;base64,{img_l}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; clip-path: {clip_value}; transition: clip-path 1s ease-in-out;">
    </div>
    <div style="text-align:center; font-weight:bold; color:#3483fa; font-size:20px;">{porcentaje:.1f}% del total</div>
    '''

# --- 3. LÓGICA DE DATOS ---
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'mostrar_celebracion' not in st.session_state:
    st.session_state.mostrar_celebracion = False

def registrar_y_celebrar(codigo, desc, piezas, ov):
    st.session_state.historial.append({"codigo": str(codigo), "descripcion": desc, "piezas": piezas, "ov": ov})
    st.session_state.scanner_input = "" 
    st.session_state.mostrar_celebracion = True # Activamos el muñequito
    st.toast(f"✅ ¡Excelente! {desc} registrado")

# --- 4. CARGA DE DRIVE ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

# --- 5. INTERFAZ ---
st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)

df_ov = cargar_datos()

if df_ov is not None:
    col_ov = 'ov'
    col_codigo = 'codigo'
    cols_desc = [c for c in df_ov.columns if 'desc' in c]
    col_desc = cols_desc[0] if cols_desc else df_ov.columns[1]
    cols_cant = [c for c in df_ov.columns if 'cant' in c]
    col_cant_nombre = cols_cant[0] if cols_cant else df_ov.columns[2]

    lista_ovs = df_ov[col_ov].unique().tolist()
    ov_sel = st.selectbox("📋 Selecciona la OV:", ["-- Selecciona --"] + lista_ovs)

    if ov_sel != "-- Selecciona --":
        # SI acabamos de registrar algo, mostramos la "Celebración"
        if st.session_state.mostrar_celebracion:
            st.markdown('<div class="level-up">¡PRODUCTO VALIDADO! 🍬</div>', unsafe_allow_html=True)
            
            # Cálculo de avance de la OV
            total_ov = df_ov[df_ov[col_ov] == ov_sel][col_cant_nombre].sum()
            total_hist = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov_sel)
            avance = (total_hist / total_ov) * 100 if total_ov > 0 else 0
            
            st.markdown(dibujar_mascota(avance), unsafe_allow_html=True)
            
            if st.button("Siguiente Producto ➡️"):
                st.session_state.mostrar_celebracion = False
                st.rerun()
        
        else:
            # INTERFAZ DE BUSQUEDA NORMAL
            codigo_input = st.text_input("👇 Escanea el código:", key="scanner_input").strip()

            if codigo_input:
                res = df_ov[(df_ov[col_codigo].astype(str) == str(codigo_input)) & (df_ov[col_ov] == ov_sel)]

                if not res.empty:
                    item = res.iloc[0]
                    st.markdown(f"### {item[col_desc]}")
                    
                    # Fotos (.png o .jpg)
                    f_png, f_jpg = f"{codigo_input}.png", f"{codigo_input}.jpg"
                    if os.path.exists(f_png): st.image(f_png, use_container_width=True)
                    elif os.path.exists(f_jpg): st.image(f_jpg, use_container_width=True)

                    limite = int(item[col_cant_nombre])
                    ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == str(codigo_input) and x['ov'] == ov_sel)
                    
                    st.metric("En sistema", f"{limite} pzs", f"Ya auditado: {ya_auditado}")
                    cant_ahora = st.number_input("Cantidad física:", min_value=1, value=1)

                    if (ya_auditado + cant_ahora) > limite:
                        st.error("🚨 CANTIDAD EXCEDIDA")
                    else:
                        st.button("CONFIRMAR ✅", on_click=registrar_y_celebrar, 
                                  args=(codigo_input, item[col_desc], cant_ahora, ov_sel))