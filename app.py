import streamlit as st
import pandas as pd
import os
import base64
import time
from io import BytesIO
from PIL import Image

# 1. CONFIGURACIÓN MOBILE-FIRST
st.set_page_config(page_title="Meli Auditoría Pro", layout="centered", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .main-header {
        background-color: #fff159; padding: 15px; border-radius: 0 0 15px 15px;
        text-align: center; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%; height: 50px; background-color: #3483fa; color: white;
        border-radius: 10px; font-weight: bold; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADOS ---
if 'historial' not in st.session_state: st.session_state.historial = []
if 'celebracion' not in st.session_state: st.session_state.celebracion = {"activo": False, "previo": 0, "nuevo": 0}
if 'sku_idx' not in st.session_state: st.session_state.sku_idx = None
if 'evidencias' not in st.session_state: st.session_state.evidencias = [] # Lista de diccionarios con fotos

def registrar_y_celebrar(codigo, desc, piezas, ov, total_ov):
    prev_auditado = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov)
    st.session_state.historial.append({"codigo": str(codigo), "descripcion": desc, "piezas": piezas, "ov": ov, "fecha": time.strftime("%H:%M")})
    nuevo_auditado = prev_auditado + piezas
    st.session_state.celebracion = {"activo": True, "previo": (prev_auditado/total_ov)*100, "nuevo": (nuevo_auditado/total_ov)*100}
    st.session_state.sku_idx = None

# --- 3. CARGA DE DATOS ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

# --- 4. INTERFAZ ---
# BARRA DE NAVEGACIÓN (MENÚ)
menu = st.sidebar.radio("Menú Principal", ["📋 Auditoría", "🖼️ Galería de Evidencia"])

df_ov = cargar_datos()

if df_ov is not None:
    col_ov, col_codigo = 'ov', 'codigo'
    cols_desc = [c for c in df_ov.columns if 'desc' in c]
    col_desc = cols_desc[0] if cols_desc else df_ov.columns[1]
    cols_cant = [c for c in df_ov.columns if 'cant' in c]
    col_cant_nombre = cols_cant[0] if cols_cant else df_ov.columns[2]

    # --- SECCIÓN A: AUDITORÍA ---
    if menu == "📋 Auditoría":
        st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)
        ov_sel = st.selectbox("Selecciona la OV:", ["-- Selecciona --"] + df_ov[col_ov].unique().tolist())

        if ov_sel != "-- Selecciona --":
            total_ov = df_ov[df_ov[col_ov] == ov_sel][col_cant_nombre].sum()
            items_ov = df_ov[df_ov[col_ov] == ov_sel].reset_index(drop=True)

            if st.session_state.celebracion["activo"]:
                st.markdown("<h2 style='text-align:center;'>¡BIEN HECHO! 🍭</h2>", unsafe_allow_html=True)
                # (Aquí iría tu función dibujar_mascota_animada)
                if st.button("Siguiente Producto ➡️"):
                    st.session_state.celebracion["activo"] = False
                    st.rerun()

            elif st.session_state.sku_idx is not None:
                item = items_ov.iloc[st.session_state.sku_idx]
                st.markdown(f"### {item[col_desc]}")
                
                # CÁMARA PARA EVIDENCIA
                with st.expander("📸 Tomar Foto de Evidencia"):
                    foto_evidencia = st.camera_input("Capturar")
                    if foto_evidencia:
                        if st.button("Guardar Foto"):
                            st.session_state.evidencias.append({
                                "ov": ov_sel,
                                "sku": item[col_desc],
                                "foto": foto_evidencia,
                                "hora": time.strftime("%H:%M")
                            })
                            st.success("Foto guardada en galería.")

                # CONTADOR
                limite = int(item[col_cant_nombre])
                ya_auditado = sum(x['piezas'] for x in st.session_state.historial if str(x['codigo']) == str(item[col_codigo]) and x['ov'] == ov_sel)
                st.metric("En Sistema", f"{limite} pzs", f"Faltan {limite - ya_auditado}")
                cant = st.number_input("Cantidad física:", min_value=1, value=1)
                
                if st.button("CONFIRMAR REGISTRO ✅"):
                    registrar_y_celebrar(item[col_codigo], item[col_desc], cant, ov_sel, total_ov)
                    st.rerun()
                
                if st.button("⬅️ Volver"):
                    st.session_state.sku_idx = None
                    st.rerun()

            else:
                for idx, row in items_ov.iterrows():
                    with st.container():
                        c_txt, c_btn = st.columns([3, 1])
                        c_txt.markdown(f"**{row[col_desc]}**\n\nCode: {row[col_codigo]}")
                        c_btn.button("Ver", key=f"b_{idx}", on_click=lambda i=idx: st.session_state.update(sku_idx=i))
                        st.divider()

    # --- SECCIÓN B: GALERÍA DE EVIDENCIA ---
    elif menu == "🖼️ Galería de Evidencia":
        st.markdown('<div class="main-header"><h1>🖼️ Galería de Evidencias</h1></div>', unsafe_allow_html=True)
        ov_galeria = st.selectbox("Elegir OV para ver fotos:", df_ov[col_ov].unique().tolist())
        
        fotos_filtradas = [f for f in st.session_state.evidencias if f['ov'] == ov_galeria]
        
        if fotos_filtradas:
            st.write(f"Se encontraron {len(fotos_filtradas)} fotos para la OV {ov_galeria}")
            for f in fotos_filtradas:
                with st.container():
                    st.image(f['foto'], caption=f"SKU: {f['sku']} | Hora: {f['hora']}")
                    st.divider()
        else:
            st.info("No hay fotos registradas para esta OV todavía.")