import streamlit as st
import pandas as pd
import os
import base64
import time
from io import BytesIO

# 1. CONFIGURACIÓN MOBILE-FIRST
st.set_page_config(page_title="Meli Auditoría Pro", layout="centered", page_icon="⚽")

# Estilos optimizados para celular
st.markdown("""
    <style>
    .stApp { background-color: #f5f5f5; }
    .main-header {
        background-color: #fff159; padding: 15px; border-radius: 0 0 15px 15px;
        text-align: center; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .main-header h1 { font-size: 20px !important; margin:0; }
    .stButton>button {
        width: 100%; height: 50px; background-color: #3483fa; color: white;
        border-radius: 10px; font-weight: bold; border: none;
    }
    .empty-state { text-align: center; padding: 40px; color: #666; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES TÉCNICAS (IMÁGENES Y ASSET MANAGEMENT) ---
def buscar_foto(codigo):
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
    <div style="position: relative; width: 160px; height: 240px; margin: 0 auto; background: transparent;">
        <img src="data:image/png;base64,{img_v}" style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 1;">
        <img src="data:image/png;base64,{img_l}" id="m-color" 
             style="position: absolute; width: 100%; height: 100%; object-fit: contain; z-index: 2; 
                    clip-path: inset({clip_inicio}% 0 0 0); transition: clip-path 2s ease-out; background: transparent;">
    </div>
    <script>setTimeout(function() {{ document.getElementById('m-color').style.clipPath = 'inset({clip_fin}% 0 0 0)'; }}, 100);</script>
    '''
    return html

# --- 3. INICIALIZACIÓN DE ESTADOS ---
if 'historial' not in st.session_state: st.session_state.historial = []
if 'celebracion' not in st.session_state: st.session_state.celebracion = {"activo": False, "previo": 0, "nuevo": 0}
if 'sku_idx' not in st.session_state: st.session_state.sku_idx = None
if 'evidencias' not in st.session_state: st.session_state.evidencias = []

def registrar_y_celebrar(codigo, desc, piezas, ov, total_ov):
    prev_auditado = sum(x['piezas'] for x in st.session_state.historial if x['ov'] == ov)
    st.session_state.historial.append({
        "codigo": str(codigo), "descripcion": desc, "piezas": piezas, "ov": ov, "fecha": time.strftime("%H:%M")
    })
    nuevo_auditado = prev_auditado + piezas
    st.session_state.celebracion = {
        "activo": True, "previo": (prev_auditado/total_ov)*100, "nuevo": (nuevo_auditado/total_ov)*100
    }
    st.session_state.sku_idx = None

# --- 4. CARGA DE DATOS (GOOGLE DRIVE) ---
URL_OV = "https://docs.google.com/spreadsheets/d/1lFs6ngMzwSfy0TgrXVgHTJCTsWc4INmOuGLmiQFrrrE/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_OV)
        df.columns = df.columns.str.strip().str.lower()
        df['codigo'] = df['codigo'].astype(str).str.strip()
        return df
    except: return None

# --- 5. INTERFAZ PRINCIPAL ---
menu = st.sidebar.radio("Menú Principal", ["📋 Auditoría", "🖼️ Galería de Evidencia"])
df_ov = cargar_datos()

if df_ov is not None:
    # Identificación de columnas
    col_ov, col_codigo = 'ov', 'codigo'
    cols_desc = [c for c in df_ov.columns if 'desc' in c]
    col_desc = cols_desc[0] if cols_desc else df_ov.columns[1]
    cols_cant = [c for c in df_ov.columns if 'cant' in c]
    col_cant_nombre = cols_cant[0] if cols_cant else df_ov.columns[2]

    # --- SECCIÓN A: AUDITORÍA ---
    if menu == "📋 Auditoría":
        st.markdown('<div class="main-header"><h1>⚽ Auditoría Mundial | Mars</h1></div>', unsafe_allow_html=True)
        ov_sel = st.selectbox("Elegir OV:", ["-- Selecciona --"] + df_ov[col_ov].unique().tolist())

        if ov_sel != "-- Selecciona --":
            total_ov = df_ov[df_ov[col_ov] == ov_sel][col_cant_nombre].sum()
            todos_productos = df_ov[df_ov[col_ov] == ov_sel].reset_index(drop=True)
            
            # Filtrar productos que no se han completado
            pendientes = []
            for idx, row in todos_productos.iterrows():
                auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == row[col_codigo] and x['ov'] == ov_sel)
                if auditado < int(row[col_cant_nombre]):
                    pendientes.append(row)
            df_pendientes = pd.DataFrame(pendientes)

            # A.1. CELEBRACIÓN (Llenado del M&M)
            if st.session_state.celebracion["activo"]:
                st.markdown("<h2 style='text-align:center; color:#3483fa;'>¡REGISTRO ÉXITOSO! 🍬</h2>", unsafe_allow_html=True)
                st.components.v1.html(dibujar_mascota_animada(st.session_state.celebracion["previo"], st.session_state.celebracion["nuevo"]), height=300)
                if st.button("Continuar con la lista ➡️"):
                    st.session_state.celebracion["activo"] = False
                    st.rerun()

            # A.2. PANTALLA DE CONTEO Y CÁMARA LIBRE
            elif st.session_state.sku_idx is not None:
                item = todos_productos.iloc[st.session_state.sku_idx]
                st.markdown(f"### {item[col_codigo]} / {item[col_desc]}")
                
                # Imagen de referencia (Buscador automático)
                ruta_foto = buscar_foto(item[col_codigo])
                if ruta_foto: st.image(ruta_foto, width=150)
                
                # CÁMARA MULTITOMA
                st.markdown("#### 📸 Evidencias")
                foto_capturada = st.camera_input("Capturar", key=f"cam_{item[col_codigo]}")
                if foto_capturada:
                    if st.button("📥 Guardar esta evidencia"):
                        st.session_state.evidencias.append({
                            "ov": ov_sel, "sku": item[col_desc], "codigo": item[col_codigo],
                            "foto": foto_capturada, "hora": time.strftime("%H:%M")
                        })
                        st.toast("Foto guardada")

                # Vista previa de ráfaga
                fotos_temp = [f for f in st.session_state.evidencias if f['codigo'] == item[col_codigo] and f['ov'] == ov_sel]
                if fotos_temp:
                    cols = st.columns(4)
                    for i, f in enumerate(fotos_temp):
                        cols[i % 4].image(f['foto'], width=70)

                # REGISTRO
                limite = int(item[col_cant_nombre])
                ya_auditado = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == item[col_codigo] and x['ov'] == ov_sel)
                st.metric("Sistema", f"{limite} pzs", f"Auditado: {ya_auditado}")
                cant = st.number_input("Cantidad física:", min_value=1, max_value=limite-ya_auditado, value=limite-ya_auditado)
                
                if st.button("CONFIRMAR ✅"):
                    registrar_y_celebrar(item[col_codigo], item[col_desc], cant, ov_sel, total_ov)
                    st.rerun()
                if st.button("⬅️ Volver"):
                    st.session_state.sku_idx = None
                    st.rerun()

            # A.3. LISTA DE PENDIENTES
            else:
                if df_pendientes.empty:
                    st.markdown('<div class="empty-state"><h3>✅ ¡OV Completada!</h3><p>Todo el material ha sido auditado.</p></div>', unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown(f"### Pendientes ({len(df_pendientes)})")
                    for idx, row in df_pendientes.iterrows():
                        idx_orig = todos_productos[todos_productos[col_codigo] == row[col_codigo]].index[0]
                        ruta_mini = buscar_foto(row[col_codigo])
                        with st.container():
                            c_img, c_info, c_btn = st.columns([1, 2.5, 1])
                            with c_img:
                                if ruta_mini: st.image(ruta_mini, width=60)
                                else: st.write("🖼️")
                            with c_info:
                                st.markdown(f"**{row[col_codigo]} / {row[col_desc]}**")
                                auditado_p = sum(x['piezas'] for x in st.session_state.historial if x['codigo'] == row[col_codigo] and x['ov'] == ov_sel)
                                st.caption(f"Avance: {auditado_p} de {row[col_cant_nombre]}")
                            with c_btn:
                                st.button("Ver", key=f"btn_{row[col_codigo]}", on_click=lambda i=idx_orig: st.session_state.update(sku_idx=i))
                            st.divider()

    # --- SECCIÓN B: GALERÍA DE EVIDENCIA (BUSCADOR) ---
    elif menu == "🖼️ Galería de Evidencia":
        st.markdown('<div class="main-header"><h1>🖼️ Galería por OV</h1></div>', unsafe_allow_html=True)
        ov_g = st.selectbox("🔍 Filtrar por OV:", ["-- Todas --"] + df_ov[col_ov].unique().tolist())
        
        filtro = [f for f in st.session_state.evidencias if f['ov'] == ov_g] if ov_g != "-- Todas --" else st.session_state.evidencias
        
        if not filtro:
            st.info("No hay evidencias guardadas para esta selección.")
        else:
            sku_filter = st.text_input("Buscar por SKU o Código:").lower()
            for f in filtro:
                if sku_filter in f['sku'].lower() or sku_filter in str(f['codigo']).lower():
                    with st.container():
                        st.markdown(f"**OV: {f['ov']} | {f['sku']}**")
                        st.image(f['foto'], use_container_width=True)
                        st.caption(f"Hora: {f['hora']}")
                        st.divider()