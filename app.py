import streamlit as st
import pandas as pd
import os
import base64
import time
from io import BytesIO

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
    /* Estilo para la lista de productos */
    .item-container {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES TÉCNICAS (IMÁGENES) ---
def buscar_foto(codigo):
    # Busca en ambos formatos
    for ext in [".png", ".jpg", ".jpeg"]:
        ruta = f"{codigo}{ext}"
        if os.path.exists(ruta):
            return ruta
    return None

def get_base64(bin_file):
    if bin_file and os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def dibujar_mascota_animada(porcentaje_inicio, porcentaje_fin):
    img_v = get_base64("mascota_vacia.png")
    img_l = get_base64("mascota_llena.png")
    if not img_v or not img_l: return ""
    clip_inicio, clip_fin = 100 - porcentaje_inicio, 100 - porcentaje_fin
    html = f'''
    <div style="position: relative; width: 160px; height: 240px; margin: 0 auto;">
        <img src="data:image/png;base64,{img_v}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1;">
        <img src="data:image/png;base64,{img_l}" id="m-color" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; clip-path: inset({clip_inicio}% 0 0 0); transition: clip-path 2s ease-out;">
    </div>
    <script>setTimeout(function() {{ document.getElementById('m-color').style.clipPath = 'inset({clip_fin}% 0 0 0)'; }}, 100);</script>
    '''
    return html

# --- 3. ESTADOS ---
if 'historial' not in st.session_state: st.session_state.historial = []
if 'celebracion' not in st.session_state: st.session_state.celebracion = {"activo": False, "previo": 0, "nuevo": 0}
if 'sku_idx' not in st.session_state: st.session_state.sku_idx = None
if 'evidencias' not in st.session_state: st.session_state.evidencias = []

def registrar_y_celebrar(codigo, desc, piezas, ov, total_ov):
    prev_auditado = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov)
    st.session_state.historial.append({"codigo": str(codigo), "descripcion": desc, "piezas": piezas, "ov": ov, "fecha": time.strftime("%H:%M")})
    nuevo_auditado = prev_auditado + piezas
    st.session_state.celebracion = {"activo": True, "previo": (prev_auditado/total_ov)*100, "nuevo": (nuevo_auditado/total_ov)*100}
    st.session_state.sku_idx = None

# --- 4. CARGA DRIVE ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        df['codigo'] = df['codigo'].astype(str).str.strip()
        return df
    except: return None

# --- 5. INTERFAZ ---
menu = st.sidebar.radio("Navegación", ["📋 Auditoría", "🖼️ Galería"])
df_ov = cargar_datos()

if df_ov is not None:
    col_ov, col_codigo = 'ov', 'codigo'
    cols_desc = [c for c in df_ov.columns if 'desc' in c]
    col_desc = cols_desc[0] if cols_desc else df_ov.columns[1]
    cols_cant = [c for c in df_ov.columns if 'cant' in c]
    col_cant_nombre = cols_cant[0] if cols_cant else df_ov.columns[2]

    if menu == "📋 Auditoría":
        st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)
        ov_sel = st.selectbox("Elegir OV:", ["-- Selecciona --"] + df_ov[col_ov].unique().tolist())

        if ov_sel != "-- Selecciona --":
            total_ov = df_ov[df_ov[col_ov] == ov_sel][col_cant_nombre].sum()
            items_ov = df_ov[df_ov[col_ov] == ov_sel].reset_index(drop=True)

            # A. CELEBRACIÓN
            if st.session_state.celebracion["activo"]:
                st.markdown("<h2 style='text-align:center;'>¡LEVEL UP! 🍭</h2>", unsafe_allow_html=True)
                st.components.v1.html(dibujar_mascota_animada(st.session_state.celebracion["previo"], st.session_state.celebracion["nuevo"]), height=300)
                if st.button("Continuar ➡️"):
                    st.session_state.celebracion["activo"] = False
                    st.rerun()

            # B. PANTALLA DE CONTEO
            elif st.session_state.sku_idx is not None:
                item = items_ov.iloc[st.session_state.sku_idx]
                st.markdown(f"### {item[col_codigo]} / {item[col_desc]}") # Formato solicitado
                
                # Imagen del producto (Detalle)
                ruta_foto = buscar_foto(item[col_codigo])
                if ruta_foto:
                    st.image(ruta_foto, use_container_width=True)
                
                with st.expander("📸 Evidencia"):
                    cam = st.camera_input("Foto")
                    if cam and st.button("Guardar"):
                        st.session_state.evidencias.append({"ov": ov_sel, "sku": item[col_desc], "foto": cam})
                        st.success("Guardada")

                limite = int(item[col_cant_nombre])
                ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == item[col_codigo] and x['ov'] == ov_sel)
                st.metric("Esperado", f"{limite} pzs", f"Faltan {limite - ya_auditado}")
                cant = st.number_input("Cantidad física:", min_value=1, value=1)
                
                if st.button("CONFIRMAR ✅"):
                    registrar_y_celebrar(item[col_codigo], item[col_desc], cant, ov_sel, total_ov)
                    st.rerun()
                if st.button("⬅️ Atrás"):
                    st.session_state.sku_idx = None
                    st.rerun()

            # C. LISTA DE PRODUCTOS
            else:
                st.markdown("### Selecciona el producto:")
                for idx, row in items_ov.iterrows():
                    ruta_mini = buscar_foto(row[col_codigo])
                    
                    with st.container():
                        c_img, c_info, c_btn = st.columns([1, 2.5, 1])
                        with c_img:
                            if ruta_mini: st.image(ruta_mini, width=60)
                            else: st.write("🍬")
                        with c_info:
                            # Formato solicitado: Código / Descripción
                            st.markdown(f"**{row[col_codigo]} / {row[col_desc]}**")
                        with c_btn:
                            st.button("Ver", key=f"btn_{idx}", on_click=lambda i=idx: st.session_state.update(sku_idx=i))
                        st.divider()

    elif menu == "🖼️ Galería":
        st.markdown('<div class="main-header"><h1>🖼️ Galería</h1></div>', unsafe_allow_html=True)
        ov_g = st.selectbox("OV:", df_ov[col_ov].unique().tolist())
        fotos = [f for f in st.session_state.evidencias if f['ov'] == ov_g]
        for f in fotos:
            st.image(f['foto'], caption=f['sku'])