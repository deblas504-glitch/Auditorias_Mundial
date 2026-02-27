import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO

# 1. CONFIGURACIÓN MOBILE-FIRST
st.set_page_config(page_title="Meli Auditoría Mobile", layout="centered", page_icon="⚽")

# Estilos CSS (Look & Feel Mercado Libre)
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
    .stTextInput>div>div>input { height: 50px; font-size: 18px; border-radius: 10px; }
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
    <div style="text-align:center; font-weight:bold; color:#3483fa;">{porcentaje:.1f}% Validado</div>
    '''

# --- 3. LOGICA DE DATOS ---
if 'historial' not in st.session_state:
    st.session_state.historial = []

def registrar_y_limpiar(codigo, desc, piezas, ov):
    st.session_state.historial.append({"codigo": codigo, "descripcion": desc, "piezas": piezas, "ov": ov})
    st.session_state.scanner_input = "" # Reset
    st.toast(f"✅ Registrado: {desc}")

# URL de tu Drive (asegúrate de que sea público)
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

# --- 4. INTERFAZ ---
st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)

df_ov = cargar_datos()

if df_ov is not None:
    # Selector de OV (Punto 2 de tu solicitud)
    lista_ovs = df_ov['ov'].unique().tolist()
    ov_seleccionada = st.selectbox("📋 Selecciona la OV a validar:", ["-- Selecciona --"] + lista_ovs)

    if ov_seleccionada != "-- Selecciona --":
        codigo_input = st.text_input("👇 Escanea o escribe código:", key="scanner_input").strip()

        if codigo_input:
            # Filtramos por código y por la OV elegida
            res = df_ov[(df_ov['codigo'].astype(str) == codigo_input) & (df_ov['ov'] == ov_seleccionada)]

            if not res.empty:
                item = res.iloc[0]
                st.markdown(f"### {item.get('descripción', 'Sin descripción')}")
                
                # Imagen del producto (Punto 3 de tu solicitud)
                # Intenta buscar .jpg, .png o .jpeg
                foto_path = f"{codigo_input}.jpg"
                if os.path.exists(foto_path):
                    st.image(foto_path, use_container_width=True)
                else:
                    st.warning(f"📸 Foto {foto_path} no encontrada en la carpeta.")

                # Cantidad
                col_cant_nombre = [c for c in df_ov.columns if 'cant' in c][0]
                limite = int(item[col_cant_nombre])
                ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == codigo_input and x['ov'] == ov_seleccionada)
                
                st.metric("Esperado", f"{limite} pzs", f"Llevas {ya_auditado}")
                cant_ahora = st.number_input("Piezas encontradas:", min_value=1, value=1)

                if (ya_auditado + cant_ahora) > limite:
                    st.error("🚨 CANTIDAD EXCEDIDA")
                else:
                    st.button("CONFIRMAR ✅", on_click=registrar_y_limpiar, 
                              args=(codigo_input, item.get('descripción', ''), cant_ahora, ov_seleccionada))

        # Barra de progreso M&M
        st.divider()
        total_ov = df_ov[df_ov['ov'] == ov_seleccionada][col_cant_nombre].sum()
        total_hist = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov_seleccionada)
        avance = (total_hist / total_ov) * 100 if total_ov > 0 else 0
        st.markdown(dibujar_mascota(avance), unsafe_allow_html=True)