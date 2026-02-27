import streamlit as st
import pandas as pd
import os
import base64
import time

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Meli Auditoría Visual", layout="centered", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .main-header {
        background-color: #fff159; padding: 15px; border-radius: 0 0 15px 15px;
        text-align: center; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    /* Estilo de Tarjeta de Producto */
    .product-card {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .stButton>button {
        width: 100%; height: 50px; background-color: #3483fa; color: white;
        border-radius: 10px; font-weight: bold; border: none;
    }
    .btn-seleccionar>div>button {
        background-color: white !important; color: #3483fa !important;
        border: 1px solid #3483fa !important; height: 35px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE IMAGEN ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def dibujar_mascota_animada(porcentaje_inicio, porcentaje_fin):
    img_v = get_base64("mascota_vacia.png")
    img_l = get_base64("mascota_llena.png")
    if not img_v or not img_l: return ""
    clip_inicio, clip_fin = 100 - porcentaje_inicio, 100 - porcentaje_fin
    html = f'''
    <div style="position: relative; width: 150px; height: 220px; margin: 0 auto;">
        <img src="data:image/png;base64,{img_v}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1;">
        <img src="data:image/png;base64,{img_l}" id="m-color" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; clip-path: inset({clip_inicio}% 0 0 0); transition: clip-path 2s ease-out;">
    </div>
    <script>setTimeout(function() {{ document.getElementById('m-color').style.clipPath = 'inset({clip_fin}% 0 0 0)'; }}, 100);</script>
    '''
    return html

# --- 3. ESTADOS ---
if 'historial' not in st.session_state: st.session_state.historial = []
if 'celebracion' not in st.session_state: st.session_state.celebracion = {"activo": False, "previo": 0, "nuevo": 0}
if 'sku_seleccionado' not in st.session_state: st.session_state.sku_seleccionado = None

def seleccionar_sku(sku_data):
    st.session_state.sku_seleccionado = sku_data

def registrar_y_celebrar(codigo, desc, piezas, ov, total_ov):
    prev_auditado = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov)
    st.session_state.historial.append({"codigo": str(codigo), "descripcion": desc, "piezas": piezas, "ov": ov, "fecha": time.strftime("%Y-%m-%d %H:%M")})
    nuevo_auditado = prev_auditado + piezas
    st.session_state.celebracion = {"activo": True, "previo": (prev_auditado/total_ov)*100, "nuevo": (nuevo_auditado/total_ov)*100}
    st.session_state.sku_seleccionado = None # Regresa a la lista

# --- 4. CARGA DRIVE ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

# --- 5. INTERFAZ ---
st.markdown('<div class="main-header"><h1>⚽ Auditoría Visual | Mars</h1></div>', unsafe_allow_html=True)
df_ov = cargar_datos()

if df_ov is not None:
    col_ov, col_codigo = 'ov', 'codigo'
    cols_desc = [c for c in df_ov.columns if 'desc' in c]
    col_desc = cols_desc[0] if cols_desc else df_ov.columns[1]
    cols_cant = [c for c in df_ov.columns if 'cant' in c]
    col_cant_nombre = cols_cant[0] if cols_cant else df_ov.columns[2]

    ov_sel = st.selectbox("📋 Selecciona la OV:", ["-- Selecciona --"] + df_ov[col_ov].unique().tolist())

    if ov_sel != "-- Selecciona --":
        total_ov = df_ov[df_ov[col_ov] == ov_sel][col_cant_nombre].sum()
        
        # PANTALLA CELEBRACIÓN
        if st.session_state.celebracion["activo"]:
            st.markdown("<h2 style='text-align:center;'>¡BIEN HECHO! 🍭</h2>", unsafe_allow_html=True)
            st.components.v1.html(dibujar_mascota_animada(st.session_state.celebracion["previo"], st.session_state.celebracion["nuevo"]), height=300)
            if st.button("Siguiente Producto ➡️"):
                st.session_state.celebracion["activo"] = False
                st.rerun()

        # FORMULARIO DE CAPTURA (Si hay un SKU elegido)
        elif st.session_state.sku_seleccionado:
            item = st.session_state.sku_seleccionado
            st.markdown(f"### {item[col_desc]}")
            
            # Imagen grande
            foto = f"{item[col_codigo]}.png" if os.path.exists(f"{item[col_codigo]}.png") else f"{item[col_codigo]}.jpg"
            if os.path.exists(foto): st.image(foto, use_container_width=True)
            
            limite = int(item[col_cant_nombre])
            ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == str(item[col_codigo]) and x['ov'] == ov_sel)
            st.metric("Sistema", f"{limite} pzs", f"Faltan {limite - ya_auditado}")
            
            cant = st.number_input("Cantidad física:", min_value=1, value=1)
            if st.button("CONFIRMAR REGISTRO ✅"):
                registrar_y_celebrar(item[col_codigo], item[col_desc], cant, ov_sel, total_ov)
                st.rerun()
            if st.button("⬅️ Cancelar"):
                st.session_state.sku_seleccionado = None
                st.rerun()

        # LISTA VISUAL DE PRODUCTOS
        else:
            st.markdown("### 📦 Productos en esta OV")
            items_ov = df_ov[df_ov[col_ov] == ov_sel]
            
            for _, row in items_ov.iterrows():
                # Preparar miniatura
                foto_mini = f"{row[col_codigo]}.png" if os.path.exists(f"{row[col_codigo]}.png") else f"{row[col_codigo]}.jpg"
                
                with st.container():
                    c_img, c_txt, c_btn = st.columns([1, 2, 1])
                    with c_img:
                        if os.path.exists(foto_mini): st.image(foto_mini, width=60)
                        else: st.write("🖼️")
                    with c_txt:
                        st.markdown(f"**{row[col_desc]}**")
                        st.caption(f"Código: {row[col_codigo]}")
                    with c_btn:
                        st.button("Ver", key=f"btn_{row[col_codigo]}", on_click=seleccionar_sku, args=(row,))
                    st.divider()