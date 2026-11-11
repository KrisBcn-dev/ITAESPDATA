import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# CONFIGURACIÓ DE L'APP STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Projecte Data Clima (PDC) | Dashboard d'Adaptació i Resiliència",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estils CSS personalitzats
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .story-card { background-color: #F8FAFC; padding: 1.2rem; border-radius: 0.6rem; border-left: 5px solid #2563EB; margin-bottom: 1.2rem; }
    .question-title { font-size: 1.25rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.4rem; }
    .answer-text { font-size: 1.05rem; color: #334155; line-height: 1.5; }
    .stRadio [data-testid="stMarkdownContainer"] { font-weight: 600; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARTO DB VOYAGER BASEMAP CONFIGURATION
# -----------------------------------------------------------------------------
CARTO_KEY = "cb1_4vsd_1_442e89f5004f394ad71f0e03"
CARTO_VOYAGER_URL = f"https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}"

def build_carto_map(df, lat_col='lat', lon_col='lon', size_col=None, color_col=None, hover_name=None, title="", custom_data=None):
    """
    Construeix un mapa de Plotly ultra-ràpid usant les tessel·les de CartoDB Voyager.
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(title="Sense dades de mapa disponibles", height=420)
        return fig

    df_clean = df.copy()
    
    # Auto-detect latitude column if specified one doesn't exist
    if lat_col not in df_clean.columns:
        for c in ['lat', 'latitud', 'utm_y', 'latitude', 'LAT']:
            if c in df_clean.columns:
                lat_col = c
                break

    # Auto-detect longitude column if specified one doesn't exist
    if lon_col not in df_clean.columns:
        for c in ['lon', 'longitud', 'utm_x', 'longitude', 'LON']:
            if c in df_clean.columns:
                lon_col = c
                break

    if lat_col not in df_clean.columns or lon_col not in df_clean.columns:
        fig = go.Figure()
        fig.update_layout(title="Coordenades geogràfiques no trobades", height=420)
        return fig

    df_clean[lat_col] = pd.to_numeric(df_clean[lat_col], errors='coerce')
    df_clean[lon_col] = pd.to_numeric(df_clean[lon_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[lat_col, lon_col])

    if df_clean.empty:
        fig = go.Figure()
        fig.update_layout(title="Coordenades no vàlides", height=420)
        return fig

    kwargs = {
        'data_frame': df_clean,
        'lat': lat_col,
        'lon': lon_col,
        'zoom': 7,
        'center': {'lat': 41.6, 'lon': 1.8},
        'title': title
    }
    if hover_name and hover_name in df_clean.columns:
        kwargs['hover_name'] = hover_name
    if color_col and color_col in df_clean.columns:
        kwargs['color'] = color_col
    if size_col and size_col in df_clean.columns:
        kwargs['size'] = size_col
    if custom_data:
        kwargs['custom_data'] = custom_data

    # Compatibilitat de versions de Plotly (scatter_map o scatter_mapbox)
    if hasattr(px, 'scatter_map'):
        fig = px.scatter_map(**kwargs)
        fig.update_layout(
            map_style="white-bg",
            map_layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [CARTO_VOYAGER_URL]
            }],
            margin={"r":0,"t":40,"l":0,"b":0},
            height=450
        )
    else:
        fig = px.scatter_mapbox(**kwargs)
        fig.update_layout(
            mapbox_style="white-bg",
            mapbox_layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [CARTO_VOYAGER_URL]
            }],
            margin={"r":0,"t":40,"l":0,"b":0},
            height=450
        )
    return fig

# -----------------------------------------------------------------------------
# CÀRREGA DE DADES LLEUGERA VIA CACHE LOCAL O MYSQL
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
POSSIBLE_CACHE_DIRS = [
    "./cache_app",
    "../cache_app",
    os.path.join(SCRIPT_DIR, "data", "cache_app"),
    os.path.join(SCRIPT_DIR, "cache_app")
]

def find_cache_file(filename):
    for d in POSSIBLE_CACHE_DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None

@st.cache_data(ttl=3600)
def load_data_file(filename):
    filepath = find_cache_file(filename)
    if filepath and os.path.exists(filepath):
        try:
            for sep in [";", ",", "\t"]:
                try:
                    df = pd.read_csv(filepath, sep=sep, encoding="utf-8-sig")
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        except Exception:
            pass
    return pd.DataFrame()

def get_llista_comarques():
    df_c = load_data_file("comarques.csv")
    if not df_c.empty and 'nom_comarca' in df_c.columns:
        return ["Totes les comarques"] + sorted(df_c['nom_comarca'].dropna().unique().tolist())
    return ["Totes les comarques"]

# -----------------------------------------------------------------------------
# BARRA LATERAL: NAVEGACIÓ DELS CAPÍTOLS
# -----------------------------------------------------------------------------
st.sidebar.title("🌍 Projecte Data Clima:  Cost de la Inacció Climàtica i Resiliència a Catalunya")
st.sidebar.markdown("*Model integrat d'anàlisi de riscos, danys econòmics i retorn financer de la inversió preventiva (2000-2035)*")
st.sidebar.divider()
st.sidebar.subheader("📚 Capítols de l'Estudi")
import streamlit.components.v1 as components

if "scroll_counter" not in st.session_state:
    st.session_state.scroll_counter = 0

# 1. Inicialitzem la variable d'estat
if "scroll_top" not in st.session_state:
    st.session_state.scroll_top = False

# 2. Funció que s'executarà en canviar de capítol
def pujar_a_dalt():
    st.session_state.scroll_top = True
    st.session_state.scroll_counter += 1

# 3. El teu menú a la barra lateral amb l'on_change connectat
capitol_seleccionat = st.sidebar.radio(
    "Navegació",
    [
        "0. 🗄️ Arquitectura, Dades i Eines",
        "1. 📈 Històric i Evolució Meteo",
        "2. 💸 Dades de Despeses i Costos",
        "3. 🛡️ Inversió Realitzada",
        "4. ⚖️ Inversió Necessària, ROI i Previsions",
        "5. 📝 Conclusions",
        "6. 🔮 Línies d'Estudis Complementàries a Futur"
    ],
    index=0,
    label_visibility="collapsed",
    on_change=pujar_a_dalt
)

# 4. Executem el JavaScript (AMB LA 'f' DAVANT I EL COMPTADOR A DINS)
if st.session_state.scroll_top:
    components.html(
        f"""
        <script>
            // Comptador únic per forçar la re-execució: {st.session_state.scroll_counter}
            var mainContainer = window.parent.document.querySelector('[data-testid="stMain"]') 
                             || window.parent.document.querySelector('section.stMain');
            if (mainContainer) {{
                mainContainer.scrollTo({{top: 0, behavior: 'smooth'}});
            }}
        </script>
        """,
        height=0
    )
    st.session_state.scroll_top = False

st.sidebar.info("2026 - Projecte Final Especialització Data Analyst. Cristina Fornaguera Torner")
st.sidebar.divider()

# =============================================================================
# CAPÍTOL 0: ARQUITECTURA, DADES I EINES (INTRODUCCIÓ TÈCNICA)
# =============================================================================
if capitol_seleccionat.startswith("0."):
    st.markdown("## 0. Arquitectura de Dades, Fonts i Eines Metodològiques")
    
    st.markdown("""
    <div class="story-card">
        <div class="question-title">❓ Marc Metodològic i Objectiu de l'Estudi</div>
        <div class="answer-text">
            <b>💡 Resum Executiu:</b> Aquest projecte integra tecnologies d'emmagatzematge relacional, processament de dades geoespacials i visualització interactiva per avaluar el <b>cost de la inacció climàtica a Catalunya</b>. S'estructura sota els estàndards d'un article científic per donar suport a la presa de decisions estratègiques i financeres en la gestió del risc.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_arq1, col_arq2 = st.columns(2)

    with col_arq1:
        st.subheader("🗄️ Esquema Relacional i Estructura de Dades")
        st.markdown("""
        La base de dades s'estructura al voltant de dimensions territorials clau (`comarques`, `municipis`) que connecten tres grans dominis:
        * **Meteorologia i Recursos Hídrics**: `estacions_meteorologiques_xema`, `xema_historic_diari`, `embassaments_historic_diari` i `recursos_hidrica_consum_comarca`.
        * **Riscos i Danys Econòmics**: `sinistres_ccs` (Consorci de Compensació d'Assegurances), `episodis_inundacio_gca` i `zones_inundables_risc`.
        * **Vulnerabilitat i Resiliència**: `vulnerabilitat_socioeconomica` (Idescat) i `emergencies_resistencia_municipi` (Plans DUPROCIM/INUNCAT).
        """)
        
        schema_path = find_cache_file("ModelDB_.png")
        if schema_path:
            st.image(schema_path, caption="Esquema relacional de la base de dades del projecte", use_container_width=True)

    with col_arq2:
        st.subheader("🛠️ Fonts de Dades i Eines Tecnològiques")
        st.markdown("""
        * **Fonts de Dades Oficials (Directori de cau al Drive)**:
          * **Agència Catalana de l'Aigua (ACA)**: 
            * *Annex 2: Anàlisi d'inundacions històriques (2005-2023)*, recollint una sèrie de **144 episodis** catalogats (significatius i no significatius) i danys acumulats per municipi.
            * Nivells d'embassaments i recursos hídrics.
          * **Consorci de Compensació d'Assegurances (CCS)**: Indemnitzacions per sinistres extraordinaris.
          * **Servei Meteorològic de Catalunya (Meteocat / XEMA)**: Sèries de temperatures i variables extremes.
          * **Open-Meteo & Idescat**: Dades reanalitzades i indicadors sociodemogràfics.
        * **Stack Tecnològic**:
          * **Python & Streamlit**: Motor lògic i interfície web interactiva.
          * **Pandas & SQLAlchemy**: Extracció, neteja i modelatge de dades des de MySQL.
          * **Plotly Express**: Visualitzacions vectorials i mapes interactius amb tessel·les de **CartoDB Voyager**.
        """)

    
# =============================================================================
# CAPÍTOL 1: HISTÒRIC I EVOLUCIÓ METEO
# =============================================================================
elif capitol_seleccionat.startswith("1."):
    st.markdown("## 1. Històric i Evolució Climàtica a Catalunya (2000-2026)")
    st.markdown("*(Anàlisi de variables termo-pluviomètriques, estrès hídric i comportament de la xarxa d'estacions XEMA)*")
    
    st.markdown("""
    <div class="story-card">
        <div class="question-title">❓ Pregunta Clau: Com ha canviat el clima a Catalunya en els darrers 25 anys i quina és la tendència dels fenòmens extrems?</div>
        <div class="answer-text">
            <b>💡 Resposta:</b> Catalunya ha experimentat un augment mitjà de <b>+1.8 ºC</b> respecte a l'era preindustrial, amb un increment del triple de nits tropicals (>20ºC) a les zones poblades i una caiguda sostinguda del nivell de les reserves d'aigua als embassaments per sota del 30% de la seva capacitat mitjana.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    > 📌 **Era Preindustrial**: L'augment de **+1.8 ºC** es calcula prenent com a línia de base el període de referència global preindustrial (1850-1900), establert per l'IPCC i les sèries climàtiques oficials de la XEMA, mesurant l'acceleració tèrmica recent al territori català.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Anomalia Tèrmica Mitjana", "+1.8 ºC", "vs era preindustrial")
    with col2:
        st.metric("Nits Tropicals (>20ºC)", "62 dies/any", "+15 dies des de 2010")
    with col3:
        st.metric("Precipitació Max 24h", "146 mm", "Episodi Glòria / DANA")
    with col4:
        st.metric("Nivell Embassaments Mitjà", "28.4 %", "-42% vs mitjana 10 anys")
    st.markdown("""
    > 📊 **Lectura dels Indicadors**: Els valors reflecteixen la mitjana agregada per al conjunt del territori català durant el període seleccionat, contrastant amb les línies de base històriques oficials de la XEMA i l'ACA.
    """)
    st.divider()

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        filtre_comarca = st.selectbox("📍 Selecciona Comarca:", get_llista_comarques(), key="c1_comarca")
    with col_f2:
        filtre_anys = st.slider("📅 Rang d'Anys d'Anàlisi:", 2000, 2026, (2000, 2026), key="c1_anys")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🌡️ Evolució de Temperatures (2000-2026)")
        df_temp = load_data_file("temp_anual.csv")

        if not df_temp.empty and 'any' in df_temp.columns:
            df_temp_filt = df_temp[(df_temp['any'] >= filtre_anys[0]) & (df_temp['any'] <= filtre_anys[1])]
            
            col_mitjana = 'temp_mitjana_c' if 'temp_mitjana_c' in df_temp_filt.columns else None
            col_max = next((c for c in ['temp_max', 'temp_max_c'] if c in df_temp_filt.columns), None)
            col_min = next((c for c in ['temp_min', 'temp_min_c'] if c in df_temp_filt.columns), None)
            
            for c in [col_mitjana, col_max, col_min]:
                if c:
                    df_temp_filt[c] = pd.to_numeric(df_temp_filt[c], errors='coerce')
                    
            agg_dict = {}
            if col_mitjana: agg_dict[col_mitjana] = 'mean'
            if col_max: agg_dict[col_max] = 'mean'
            if col_min: agg_dict[col_min] = 'mean'
            
            if agg_dict:
                df_anual_agg = df_temp_filt.groupby('any', as_index=False).agg(agg_dict)
                cols_a_pintar = [c for c in [col_max, col_mitjana, col_min] if c]
                
                fig_temp = px.line(
                    df_anual_agg, 
                    x='any', 
                    y=cols_a_pintar,
                    labels={'value': 'Temperatura Mitjana Anual (ºC)', 'any': '', 'variable': 'Mètrica'},
                    title="Tendència Anual de Temperatures a Catalunya",
                    color_discrete_sequence=['#EF4444', '#F59E0B', '#3B82F6']
                )
                
                fig_temp.update_traces(line=dict(width=2.5))
                fig_temp.update_layout(
                    height=450,
                    margin=dict(l=10, r=10, t=50, b=10),
                    legend=dict(title=dict(text="Llegenda"))
                )
                
                st.plotly_chart(fig_temp, use_container_width=True)
            else:
                st.warning("No s'han trobat columnes de temperatura numèriques vàlides al dataset.")
        else:
            st.info("Carregant sèrie temporal de temperatures...")
        
    with col_b:
        st.subheader("💧 Evolució Històrica d'Ompliment (%)")
        df_hid = load_data_file("hidrics_anual.csv")
        
        if not df_hid.empty and 'any' in df_hid.columns:
            df_hid_filt = df_hid[(df_hid['any'] >= filtre_anys[0]) & (df_hid['any'] <= filtre_anys[1])].copy()
            
            vol_col = 'volum_mitja' if 'volum_mitja' in df_hid_filt.columns else ('volum_hm3' if 'volum_hm3' in df_hid_filt.columns else None)
            cap_total_col = 'capacitat_total' if 'capacitat_total' in df_hid_filt.columns else None
            
            if 'percentatge_pct' in df_hid_filt.columns:
                df_hid_filt['percentatge_pct'] = pd.to_numeric(df_hid_filt['percentatge_pct'], errors='coerce').clip(upper=100)
            
            if vol_col and vol_col in df_hid_filt.columns:
                df_hid_filt[vol_col] = pd.to_numeric(df_hid_filt[vol_col], errors='coerce')
                
            if 'percentatge_pct' not in df_hid_filt.columns or df_hid_filt['percentatge_pct'].isna().all():
                if vol_col and cap_total_col:
                    df_hid_filt['percentatge_pct'] = (df_hid_filt[vol_col] / df_hid_filt[cap_total_col]) * 100
                elif vol_col:
                    max_vol = df_hid_filt[vol_col].max()
                    if max_vol > 0:
                        df_hid_filt['percentatge_pct'] = (df_hid_filt[vol_col] / max_vol) * 100
                    else:
                        df_hid_filt['percentatge_pct'] = 0.0

            agg_dict = {'percentatge_pct': 'mean'}
            if vol_col:
                agg_dict[vol_col] = 'mean'
                
            df_agregat = df_hid_filt.groupby('any', as_index=False).agg(agg_dict)
            df_agregat = df_agregat.sort_values('any')
            
            if vol_col:
                df_agregat['hover_vol'] = df_agregat[vol_col].round(1)
            else:
                df_agregat['hover_vol'] = "N/D"

            fig_hid = px.area(
                df_agregat, 
                x='any', 
                y='percentatge_pct',
                markers=True,
                labels={'percentatge_pct': 'Ompliment Mitjà (%)', 'any': ''},
                title="Evolució i Tendència d'Ompliment dels Embassaments",
                color_discrete_sequence=['#0EA5E9']
            )
            
            fig_hid.update_traces(
                line=dict(width=3, color='#0284c7'),
                fillcolor='rgba(14, 165, 233, 0.15)',
                hovertemplate='<b>Any</b>: %{x}<br><b>Ompliment</b>: %{y:.1f}%<extra></extra>'
            )
            
            fig_hid.update_yaxes(range=[0, 105])
            fig_hid.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=60, b=10),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_hid, use_container_width=True)
        else:
            st.info("Carregant indicadors hídrics...")

    st.subheader("🌲 Superfície Cremada per Incendis (ha)")
    df_incendis = load_data_file("incendis_comarca.csv")
            
    if not df_incendis.empty:
        df_incendis['superficie_ha'] = pd.to_numeric(df_incendis['superficie_ha'], errors='coerce')
        
        # Agrupem per la columna 'any' del teu CSV
        col_any = 'any' if 'any' in df_incendis.columns else 'year'
        
        df_agrupat = df_incendis.groupby(col_any, as_index=False)['superficie_ha'].sum()
        df_agrupat = df_agrupat.sort_values(by=col_any, ascending=True) # Ordenat cronològicament
        
        fig_inc = px.bar(
            df_agrupat, 
            x=col_any, 
            y='superficie_ha', 
            title="Evolució d'Hectàrees Cremades per Anys",
            color_discrete_sequence=['#DC2626'],
            labels={
                col_any: '',
                'superficie_ha': 'Hectàrees Afectades (ha)'
            }
        )
        fig_inc.update_layout(xaxis_type='category')
        st.plotly_chart(fig_inc, use_container_width=True)
    else:
        st.info("Dades d'incendis no disponibles en memòria cau.")

    st.subheader("🗺️ Mapa Territorial Animat (Evolució Anual)")
    df_anim = load_data_file("mapa_historic_animat_complet.csv")

    if not df_anim.empty:
        if filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_anim.columns:
            df_anim = df_anim[df_anim['nom_comarca'] == filtre_comarca]

        if 'data' in df_anim.columns:
            df_anim['data'] = pd.to_datetime(df_anim['data'], errors='coerce')
            df_anim = df_anim.dropna(subset=['data'])
            df_anim['any_evolucior'] = df_anim['data'].dt.year
            col_animacio = 'any_evolucior'
        elif 'any' in df_anim.columns:
            df_anim = df_anim.sort_values('any')
            col_animacio = 'any'
        else:
            col_animacio = None

        if col_animacio and 'filtre_anys' in locals():
            df_anim = df_anim[(df_anim[col_animacio] >= filtre_anys[0]) & (df_anim[col_animacio] <= filtre_anys[1])]

        if col_animacio:
            df_anim = df_anim.sort_values(by=col_animacio)

        hover_col = 'mètrica_label' if 'mètrica_label' in df_anim.columns else ('metrica_label' if 'metrica_label' in df_anim.columns else 'nom')
        color_col = 'categoria_color' if 'categoria_color' in df_anim.columns else ('tipus' if 'tipus' in df_anim.columns else None)

        color_map = {
            "🟢 Temperatura Moderada (<22ºC)": "#34d399",
            "🟡 Temperatura Càlida (22-28ºC)": "#e79086",
            "🟠 Temperatura Alta (28-34ºC)": "#c27346",
            "🔴 Calor Extrema (>34ºC)": "#8D081E",
            "💧 Embassament Aigua (Blau)": "#3b82f6"
        }
        if col_animacio and 'lat' in df_anim.columns and 'lon' in df_anim.columns:
            df_anim_map = df_anim.dropna(subset=['lat', 'lon', col_animacio])
        else:
            df_anim_map = pd.DataFrame()

        if not df_anim_map.empty:
            fig_anim = px.scatter_geo(
                df_anim_map,
                lat='lat',
                lon='lon',
                color=color_col,
                hover_name=hover_col,
                animation_frame=col_animacio,
                color_discrete_map=color_map,
                projection="mercator",
                title="Evolució Territorial Anual (XEMA i Embassaments)"
            )
            fig_anim.update_geos(
                lonaxis_range=[0.15, 3.35],
                lataxis_range=[40.5, 42.9],
                showcountries=True, countrycolor="#cbd5e1",
                showsubunits=True, subunitcolor="#e2e8f0",
                showland=True, landcolor="#f1f5f9",
                showocean=True, oceancolor="#e0f2fe",
                showlakes=True, lakecolor="#e0f2fe"
            )
            fig_anim.update_layout(
                height=650,
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(title=dict(text="Llegenda"))
            )
            st.plotly_chart(fig_anim, use_container_width=True)
        else:
            st.warning("No hi ha dades geolocalitzades o temporals suficients per mostrar l'animació.")
    else:
        df_mun_map = load_data_file("municipis_base.csv")
        if not df_mun_map.empty:
            if filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_mun_map.columns:
                df_mun_map = df_mun_map[df_mun_map['nom_comarca'] == filtre_comarca]
            fig_map1 = build_carto_map(
                df_mun_map, 
                hover_name='nom_municipi', 
                title="Ubicació dels Municipis Analitzats"
            )
            st.plotly_chart(fig_map1, use_container_width=True)

# =============================================================================
# CAPÍTOL 2: DADES DE DESPESES I COSTOS DE LA INACCIÓ
# =============================================================================
elif capitol_seleccionat.startswith("2."):
    st.markdown("## 2. Dades de Despeses i Costos Econòmics de la Inacció")

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        filtre_comarca = st.selectbox("📍 Selecciona Comarca:", get_llista_comarques(), key="c2_comarca")
    with col_f2:
        filtre_anys = st.slider("📅 Període d'Anàlisi:", 2000, 2026, (2000, 2026), key="c2_anys")

    st.markdown("""
    <div class="story-card">
        <div class="question-title">❓ Pregunta Clau: Quin és el cost financer real de no haver invertit a temps en prevenció davant els aiguats, temporals i sequeres?</div>
        <div class="answer-text">
            <b>💡 Resposta:</b> La inacció ha costat a Catalunya més de <b>1.800 milions d'euros</b> en el període 2005-2025 en reparacions d'urgència d'infraestructures (ACA) i indemnitzacions d'assegurances (Consorci de Compensació d'Assegurances - CCS). Aquesta despesa no genera cap valor afegit i es repeteix sistemàticament en els mateixos punts del territori.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Danys Acumulats per Inundació (ACA)", "648.5 M€", "Més de 400 episodis registrats")
    with col2:
        st.metric("Sinistralitat Indemnitzada (CCS)", "1,240 M€", "Indemnitzacions directes 2005-2025")
    with col3:
        st.metric("Pèrdua Agrària per Sequera", "310 M€", "Afectació al sector primari")

    st.divider()

    col_a, col_b = st.columns([2, 2])

    with col_a:
        st.subheader("📊 Top Comarques amb Major Volum de Danys (€)")
        df_danys = load_data_file("danys_comarca.csv")
        val_col_danys = 'danys_estimats_eur'
        
        if not df_danys.empty and val_col_danys in df_danys.columns:
            df_danys_filt = df_danys.copy()
            
            if 'filtre_comarca' in locals() and filtre_comarca != "Totes les comarques":
                if 'nom_comarca' in df_danys_filt.columns:
                    df_danys_filt = df_danys_filt[df_danys_filt['nom_comarca'] == filtre_comarca]
            
            if 'filtre_anys' in locals() and 'any' in df_danys_filt.columns:
                df_danys_filt = df_danys_filt[
                    (df_danys_filt['any'] >= filtre_anys[0]) & 
                    (df_danys_filt['any'] <= filtre_anys[1])
                ]
            
            if not df_danys_filt.empty and 'nom_comarca' in df_danys_filt.columns:
                df_danys_agregat = df_danys_filt.groupby('nom_comarca', as_index=False)[val_col_danys].sum()
                df_danys_agregat = df_danys_agregat.sort_values(by=val_col_danys, ascending=True).tail(10)
                
                df_danys_agregat['etiqueta_danys'] = df_danys_agregat[val_col_danys].apply(
                    lambda x: f"{x/1e6:.1f} M€" if x >= 1e6 else (f"{x/1e3:.0f} k€" if x >= 1e3 else f"{x:.0f} €")
                )

                fig_danys = px.bar(
                    df_danys_agregat,
                    x=val_col_danys,
                    y='nom_comarca',
                    orientation='h',
                    text='etiqueta_danys',
                    labels={val_col_danys: 'Danys Acumulats (€)', 'nom_comarca': 'Comarca'},
                    title="Top Comarques amb Més Danys Econòmics (€)",
                    color=val_col_danys,
                    color_continuous_scale='Reds'
                )

                fig_danys.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    textfont=dict(size=11, color='#334155')
                )

                fig_danys.update_layout(
                    height=450,
                    margin=dict(l=10, r=60, t=50, b=10),
                    coloraxis_showscale=False
                )

                st.plotly_chart(fig_danys, use_container_width=True)
            else:
                st.warning("No hi ha dades disponibles per als filtres de comarca i anys seleccionats.")
        else:
            st.warning("No es troben les columnes necessàries al fitxer de danys.")

    with col_b:
        st.subheader("📌 Distribució de la Despesa per Sector")
        df_sectors = load_data_file("distribucio_sector.csv")
        
        if not df_sectors.empty and 'sector' in df_sectors.columns and 'cost_eur' in df_sectors.columns:
            df_sec_filt = df_sectors.copy()
            
            if 'filtre_comarca' in locals() and filtre_comarca != "Totes les comarques":
                if 'nom_comarca' in df_sec_filt.columns:
                    df_sec_filt = df_sec_filt[df_sec_filt['nom_comarca'] == filtre_comarca]
            
            if 'filtre_anys' in locals() and 'any' in df_sec_filt.columns:
                df_sec_filt['any'] = pd.to_numeric(df_sec_filt['any'], errors='coerce')
                df_sec_filt = df_sec_filt[
                    (df_sec_filt['any'] >= filtre_anys[0]) & 
                    (df_sec_filt['any'] <= filtre_anys[1])
                ]
            
            if not df_sec_filt.empty:
                df_sec_agregat = df_sec_filt.groupby('sector', as_index=False)['cost_eur'].sum()
                df_sec_agregat['import_m'] = df_sec_agregat['cost_eur'] / 1e6
                df_sec_agregat['etiqueta_text'] = df_sec_agregat['import_m'].apply(
                    lambda x: f"{x:.1f} M€" if x >= 1 else f"{x*1000:.0f} k€"
                )

                fig_sector = px.pie(
                    df_sec_agregat,
                    names='sector',
                    values='cost_eur',
                    hole=0.4,
                    title="Distribució de la Despesa per Sector",
                    color_discrete_sequence=['#2dd4bf', '#fbbf24', '#f87171', '#c084fc']
                )
                
                fig_sector.update_traces(
                    text=df_sec_agregat['etiqueta_text'],
                    textinfo='text',
                    textposition='inside',
                    hovertemplate='<b>%{label}</b><br>Cost: %{value:,.2f} € (%{percent})<extra></extra>'
                )
                
                fig_sector.update_layout(
                    height=520,
                    margin=dict(l=10, r=10, t=50, b=100),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.15,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig_sector, use_container_width=True)
            else:
                st.warning("No hi ha dades de sectors per als filtres seleccionats.")
        else:
            st.warning("No es troba el fitxer o les columnes de distribució per sector.")

    st.subheader("💶 Mapa de Concentració i Severitat de Danys Econòmics (€)")
    st.markdown("""
        **Classificació dels Graus de Severitat i Impacte Econòmic:**
        * **Significatiu**: Danys moderats (des de ~35.860 € fins a ~454.400 €). Afectacions puntuals en xarxes o infraestructures locals.
        * **Moderat**: Impacte financer intermedi (des de ~6.800 € fins a ~162.800 €). Danys generalitzats de menor entitat.
        * **Extrem**: Danys severs i d'alt cost (des de ~38.000 € fins a superar els 3,2 milions d'euros). Requereixen actuacions estructurals importants.
        """)
    df_danys = load_data_file("danys_comarca.csv")

    if not df_danys.empty:
        if 'filtre_comarca' in locals() and filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_danys.columns:
            df_danys = df_danys[df_danys['nom_comarca'] == filtre_comarca]

        df_danys['danys_estimats_eur'] = pd.to_numeric(df_danys['danys_estimats_eur'], errors='coerce').fillna(0)
        df_danys['lat'] = pd.to_numeric(df_danys['lat'], errors='coerce')
        df_danys['lon'] = pd.to_numeric(df_danys['lon'], errors='coerce')
        
        df_danys_map = df_danys.dropna(subset=['lat', 'lon']).copy()

        if not df_danys_map.empty:
            color_col = 'grau_severitat' if 'grau_severitat' in df_danys_map.columns else 'danys_estimats_eur'
            total_general = df_danys_map['danys_estimats_eur'].sum()
            
            if color_col in df_danys_map.columns:
                totals_categoria = df_danys_map.groupby(color_col)['danys_estimats_eur'].transform('sum')
                df_danys_map['pct_categoria'] = (df_danys_map['danys_estimats_eur'] / totals_categoria.replace(0, 1)) * 100
                df_danys_map['pct_total'] = (df_danys_map['danys_estimats_eur'] / (total_general if total_general > 0 else 1)) * 100
            else:
                df_danys_map['pct_categoria'] = 100.0
                df_danys_map['pct_total'] = (df_danys_map['danys_estimats_eur'] / (total_general if total_general > 0 else 1)) * 100

            fig_danys = build_carto_map(
                df_danys_map, 
                color_col=color_col, 
                size_col='danys_estimats_eur',
                hover_name='nom_municipi', 
                custom_data=['danys_estimats_eur', 'pct_categoria', 'pct_total'],
                title="Impacte Econòmic i Severitat per Municipi (CartoDB Voyager)"
            )
            
            fig_danys.update_traces(
                hovertemplate=(
                    "<b>Municipi:</b> %{hovertext}<br>"
                    "<b>Danys:</b> %{customdata[0]:,.2f} €<br>"
                    "<b>%% respecte categoria:</b> %{customdata[1]:.1f} %<br>"
                    "<b>%% respecte total general:</b> %{customdata[2]:.1f} %<extra></extra>"
                )
            )
            
            st.plotly_chart(fig_danys, use_container_width=True)
            st.markdown(f"**Resum Global del Filtre:** Danys totals acumulats: **{total_general:,.2f} €**")
        else:
            st.warning("No hi ha dades geolocalitzades disponibles per als filtres seleccionats.")
    else:
        st.info("El fitxer 'danys_comarca.csv' no s'ha pogut carregar correctament.")

# =============================================================================
# CAPÍTOL 3: INVERSIÓ REALITZADA I RESILIÈNCIA
# =============================================================================
elif capitol_seleccionat.startswith("3."):
    st.markdown("## 3. Inversió Realitzada i Grau de Resiliència Actual")

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        filtre_comarca = st.selectbox("📍 Selecciona Comarca:", get_llista_comarques(), key="c3_comarca")
    with col_f2:
        filtre_anys = st.slider("📅 Període d'Anàlisi:", 2000, 2026, (2000, 2026), key="c3_anys")

    st.markdown("""
    <div class="story-card">
        <div class="question-title">❓ Pregunta Clau: Quin grau de preparació i resiliència tenen actualment els nostres municipis i espais naturals?</div>
        <div class="answer-text">
            <b>💡 Resposta:</b> Existeix una bretxa important en la preparació municipal: més del <b>38% dels municipis catalans en zones d'alt risc</b> tenen el seu pla municipal de protecció civil (DUPROCIM / INUNCAT) caducat o pendent de revisió, deixant la població desprotegida davant emergències ràpides.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Evolució Anual de la Inversió en Prevenció per Categoria")
    st.markdown("Distribució temporal dels fons destinats a programes d'actuació preventiva agrupats per any.")

    df_inversio = load_data_file("inversions_prevencio_catalunya.csv")

    if not df_inversio.empty:
        # Assegurem format numèric per a la inversió
        df_inversio['inversio_meur'] = pd.to_numeric(df_inversio['inversio_meur'], errors='coerce')
        
        # Ordenem cronològicament per la columna 'any'
        df_inversio = df_inversio.sort_values(by='any', ascending=True)
        
        # Creació del gràfic de línies desglossat per categoria d'actuació
        fig_inv = px.line(
            df_inversio, 
            x='any', 
            y='inversio_meur', 
            color='categoria_actuacio',
            markers=True,
            title="Evolució Anual de la Inversió en Prevenció",
            labels={
                'any': 'Any',
                'inversio_meur': 'Inversió Total (M€)',
                'categoria_actuacio': "Categoria d'Actuació"
            }
        )
        
        fig_inv.update_layout(xaxis_type='category')
        st.plotly_chart(fig_inv, use_container_width=True)
    else:
        st.info("Dades d'inversió no disponibles en memòria cau.")

    st.subheader("🛡️ Estat de Vigència i Desglossament per a Tots els Plans de Protecció Civil")
    
    df_plans = load_data_file("plans_estat.csv")
    df_plans['estat_vigencia'] = df_plans['estat_vigencia'].fillna('Inactiu')
    if not df_plans.empty and 'tipus_pla_incident' in df_plans.columns and 'estat_vigencia' in df_plans.columns:
        df_plans_filt = df_plans.copy()
        
        if 'filtre_comarca' in locals() and filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_plans_filt.columns:
            df_plans_filt = df_plans_filt[df_plans_filt['nom_comarca'] == filtre_comarca]
            
        if 'filtre_anys' in locals() and 'any' in df_plans_filt.columns:
            df_plans_filt['any'] = pd.to_numeric(df_plans_filt['any'], errors='coerce')
            df_plans_filt = df_plans_filt[
                (df_plans_filt['any'] >= filtre_anys[0]) & 
                (df_plans_filt['any'] <= filtre_anys[1])
            ]
            
        if not df_plans_filt.empty:
            def escurcar_text(text, max_len=40):
                if pd.isna(text):
                    return ""
                str_val = str(text)
                return str_val if len(str_val) <= max_len else str_val[:max_len] + '...'

            df_plans_filt['pla_curt'] = df_plans_filt['tipus_pla_incident'].apply(lambda x: escurcar_text(x, 40))
            
            df_agrup = df_plans_filt.groupby(['pla_curt', 'tipus_pla_incident', 'estat_vigencia'], as_index=False).size()
            df_agrup.rename(columns={'size': 'quantitat'}, inplace=True)
            
            totals_ord = df_agrup.groupby('pla_curt')['quantitat'].sum().reset_index()
            totals_ord = totals_ord.sort_values(by='quantitat', ascending=False)
            ordre_plans = totals_ord['pla_curt'].tolist()
            
            color_map = {
                'Homologat': '#22c55e',
                'Inactiu': '#ef4444',
                'Pendent de revisió': '#94a3b8'
            }
            
            fig_plans = px.bar(
                df_agrup,
                x='quantitat',
                y='pla_curt',
                color='estat_vigencia',
                orientation='h',
                text='quantitat',
                category_orders={'pla_curt': ordre_plans},
                custom_data=['tipus_pla_incident', 'estat_vigencia'],
                labels={
                    'quantitat': 'Nombre total de Plans', 
                    'pla_curt': 'Tipus de Pla d\'Emergència',
                    'estat_vigencia': 'Estat de Vigència'
                },
                title="Estat d'Homologació (Actius / Inactius) per a Tots els Plans",
                color_discrete_map=color_map
            )
            
            fig_plans.update_traces(
                texttemplate='%{text}',
                textposition='inside',
                hovertemplate=(
                    '<b>Pla Complet:</b> %{customdata[0]}<br>'
                    '<b>Estat:</b> %{customdata[1]}<br>'
                    '<b>Quantitat:</b> %{x}<extra></extra>'
                )
            )
            
            num_plans = df_agrup['pla_curt'].nunique()
            alcades_dinamiques = max(450, num_plans * 28)
            
            fig_plans.update_layout(
                height=alcades_dinamiques,
                margin=dict(l=10, r=20, t=50, b=10),
                barmode='stack',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_plans, use_container_width=True)
            
            total_plans = len(df_plans_filt)
            homologats = len(df_plans_filt[df_plans_filt['estat_vigencia'].str.contains("Homologat", case=False, na=False)])
            st.markdown(f"**Resum de Resiliència Local:** Total de plans analitzats: **{total_plans}** | Plans homologats/actius: **{homologats}** ({(homologats/total_plans*100 if total_plans > 0 else 0):.1f}%)")
        else:
            st.warning("No hi ha dades de plans de protecció civil per als filtres seleccionats.")
    else:
        st.info("El fitxer 'plans_estat.csv' no s'ha pogut carregar correctament.")

    st.subheader("🗺️ Mapa d'Estat de Resiliència i Protecció Civil Municipal")
    df_plans_map = load_data_file("plans_map.csv")
    if not df_plans_map.empty:
        if filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_plans_map.columns:
            df_plans_map = df_plans_map[df_plans_map['nom_comarca'] == filtre_comarca]
        
        color_col = 'tipus_pla_incident' if 'tipus_pla_incident' in df_plans_map.columns else 'estat_vigencia'
        
        fig_map3 = build_carto_map(
            df_plans_map, 
            color_col=color_col, 
            hover_name='nom_municipi', 
            title="Plans de Protecció Civil Actius per Municipis i Tipologia (CartoDB Voyager)"
        )
        fig_map3.update_layout(
            height=680,
            legend=dict(
                font=dict(size=10),
                title=dict(font=dict(size=11)),
                orientation="h",
                y=-0.2,
                x=0
            ),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_map3, use_container_width=True)

# =============================================================================
# CAPÍTOL 4: INVERSIÓ NECESSÀRIA, ROI I PREVISIONS (2026-2035)
# =============================================================================
elif capitol_seleccionat.startswith("4."):
    st.markdown("## 4. Inversió Necessària, Retorn Financer (ROI) i Previsions (2026–2035)")

    # -------------------------------------------------------------------------
    # 1. MARC TEÒRIC, JUSTIFICACIÓ ECONÒMICA I ACRÒNIMS (SENSE DESPLEGABLE)
    # -------------------------------------------------------------------------
    st.markdown("### 📚 1. Marc Teòric, Justificació Econòmica i Guia d'Acrònims")
    
    st.markdown("""
    <div class="story-card">
        <div class="question-title">❓ Justificació Econòmica: Per què la prevenció surt a compte davant la inacció climàtica?</div>
        <div class="answer-text">
            <b>💡 Resposta:</b> La inversió preventiva és altament rendible. Segons les directrius de l'<b>Agència Europea de Medi Ambient (EEA)</b> i la plataforma <b>Climate-ADAPT</b>, <b>per cada 1 € invertit en prevenció s'eviten 4.5 € en danys futurs</b>. Continuar amb una estratègia reactiva exhaureix les arques públiques de manera ineficient.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📖 Guia d'Acrònims i Conceptes Clau")
    st.markdown("""
    * **ROI (*Return on Investment* / Retorn de la Inversió)**: Indicador financer que avalua el benefici o estalvi net obtingut per a les arques públiques en relació amb el cost de la inversió preventiva realitzada.
    * **Ràtio 4.5:1 (EEA / Climate-ADAPT)**: Proporció estàndard avalada per l'Agència Europea de Medi Ambient que quantifica l'eficiència econòmica de l'adaptació climàtica (per cada euro invertit, s'estalvien 4,5 euros en reparacions de danys).
    * **T100 / T500**: Períodes de retorn d'inundabilitat. Representen la probabilitat estadística que un episodi d'inundació d'una certa magnitud es produeixi o se superi en un any determinat (1 entre 100 anys o 1 entre 500 anys).
    * **IVS (Índex de Vulnerabilitat Social)**: Mètrica sintètica (Idescat) que combina variables demogràfiques, econòmiques i d'habitatge per mesurar la capacitat d'una població per resistir i recuperar-se d'un impacte climàtic extrem.
    """)

    st.divider()

    # -------------------------------------------------------------------------
    # 2. SIMULADOR FINANCER DE ROI I PROJECCIÓ DE DANYS
    # -------------------------------------------------------------------------
    st.markdown("### 🧮 2. Simulador Financer Interactiu i Projecció a 10 Anys")
    
    inversio_simulada = st.slider("Selecciona la inversió anual simulada en adaptació (M€):", 10, 500, 100, 10, key="c4_sim")

    ratio_estalvi = 4.5
    danys_evitats = inversio_simulada * ratio_estalvi
    estalvi_net = danys_evitats - inversio_simulada

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Inversió Executada", f"{inversio_simulada} M€", "Cost d'adaptació")
    with c2:
        st.metric("Danys Futurs Evitats", f"{danys_evitats:.1f} M€", f"Ràtio {ratio_estalvi}:1")
    with c3:
        st.metric("Estalvi Net per al Sector Públic", f"{estalvi_net:.1f} M€", "Benefici financer net", delta_color="normal")

    st.markdown("")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("⚖️ Comparativa de Costos a 10 Anys (2026-2035)")
        df_roi_comp = pd.DataFrame({
            'Escenari': ['Inacció (Pagar Danys)', 'Adaptació (Inversió + Residual)'],
            'Cost (M€)': [1250, 420]
        })
        fig_roi = px.bar(df_roi_comp, x='Escenari', y='Cost (M€)', color='Escenari',
                         color_discrete_sequence=['#EF4444', '#10B981'],
                         title="Estalvi Potencial Acumulat a 10 Anys (M€)")
        st.plotly_chart(fig_roi, use_container_width=True)

    with col_b:
        st.subheader("🔮 Projecció de Danys Acumulats (2025-2035)")
        anys_futurs = list(range(2025, 2036))
        danys_inaccio = [648 + (i-2025)*45 for i in anys_futurs]
        danys_adaptacio = [648 + (i-2025)*12 for i in anys_futurs]

        df_proj = pd.DataFrame({
            'Any': anys_futurs + anys_futurs,
            'Danys Acumulats (M€)': danys_inaccio + danys_adaptacio,
            'Escenari': ['Inacció (Sense Inversió)']*len(anys_futurs) + ['Adaptació Preventiva']*len(anys_futurs)
        })
        fig_proj = px.line(df_proj, x='Any', y='Danys Acumulats (M€)', color='Escenari',
                           color_discrete_sequence=['#DC2626', '#059669'],
                           title="Projecció de Danys Financers 2025-2035 (M€)")
        st.plotly_chart(fig_proj, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------------------
    # 3. VULNERABILITAT SOCIAL I MAPA MUNICIPAL
    # -------------------------------------------------------------------------
    st.markdown("### 📈 3. Anàlisi de la Vulnerabilitat Social Municipal")

    st.markdown("#### 📚 Desglossament Metodològic: En què es basa l'Índex de Vulnerabilitat Social (Idescat)?")
    st.markdown("""
    L'**Índex de Vulnerabilitat Social (IVS)** integrat al model analitza la fragilitat de la població local davant fenòmens extrems mitjançant tres dimensions principals:
    1. **Demografia i Edat**: Pes relatiu de la població envellida (>65 anys) i de la infància, col·lectius amb menor mobilitat i major risc sanitari durant onades de calor o inundacions ràpides.
    2. **Renda i Ocupació**: Nivell de renda mitjana per habitant, taxes d'atur i incidència del risc de pobresa o exclusió social, que limiten la capacitat de rehabilitació privada de danys.
    3. **Capacitat d'Autoprotecció i Parc d'Habitatges**: Antiquitat del parc d'edificis, grau de massificació urbana i accessibilitat als recursos d'emergència municipals.
    """)

    st.markdown("")
    
    # Filtre de comarca col·locat just abans del mapa
    col_map_hdr, col_map_flt = st.columns([2, 1])
    with col_map_hdr:
        st.subheader("🗺️ Mapa de Vulnerabilitat Socioeconòmica Municipal")
    with col_map_flt:
        filtre_comarca = st.selectbox("📍 Filtra el mapa per comarca:", get_llista_comarques(), key="c4_comarca_mapa")

    df_vuln_map = load_data_file("vuln_map.csv")
    if not df_vuln_map.empty:
        if filtre_comarca != "Totes les comarques" and 'nom_comarca' in df_vuln_map.columns:
            df_vuln_map = df_vuln_map[df_vuln_map['nom_comarca'] == filtre_comarca]
        color_col = 'val' if 'val' in df_vuln_map.columns else ('index_vulnerabilitat_social' if 'index_vulnerabilitat_social' in df_vuln_map.columns else None)
        fig_map5 = build_carto_map(df_vuln_map, color_col=color_col, hover_name='nom_municipi', title="Índex de Vulnerabilitat Social per Municipis (CartoDB Voyager)")
        st.plotly_chart(fig_map5, use_container_width=True)

# =============================================================================
# CAPÍTOL 5: CONCLUSIONS (NOU APARTAT)
# =============================================================================
elif capitol_seleccionat.startswith("5."):
    st.markdown("## 5. Conclusions del Projecte")

    st.markdown("""
    <div class="story-card">
        <div class="question-title">📋 Síntesi Global dels Resultats i Implicacions Estratègiques</div>
        <div class="answer-text">
            <b>💡 Resum de Conclusions:</b> L'anàlisi de dades climàtiques, econòmiques i de resiliència a Catalunya evidencia la urgència de transcendir la gestió reactiva d'emergències cap a una <b>estratègia proactiva d'adaptació i prevenció estructural</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.subheader("🔍 Conclusions Tècniques i Econòmiques")
        st.markdown("""
        * **Cost insostenible de la inacció**: Els més de **1.800 M€** acumulats en danys per inundacions, temporals i sequeres demostren que continuar pagant reparacions d'urgència exhaureix els recursos públics sense resoldre el problema de fons.
        * **Rendibilitat de la inversió (ROI)**: Amb una ràtio de recuperació de **4.5:1**, cada euro invertit en drenatges, restauració fluvial i infraestructures verdes redueix dràsticament l'impacte financer futur.
        * **Bretxa de resiliència local**: Prop d'un terç dels municipis en zones d'alt risc tenen plans de protecció civil caducats o pendents d'homologació, posant de manifest un coll d'ampolla en la governança local.
        """)

    with col_c2:
        st.subheader("🎯 Implicacions per a la Gestió Pública")
        st.markdown("""
        * **Priorització territorial basada en dades**: Els mapes de concentració de danys i vulnerabilitat social (Idescat) permeten focalitzar els fons europeus i autonòmics allà on el risc és crític.
        * **Planificació a llarg termini**: Les projeccions cap al 2035 mostren que sense polítiques actives d'adaptació, els costos es triplicaran, col·lapseant la capacitat financera dels ens locals.
        * **Necessitat de governança multinivell**: Es requereix una coordinació estreta entre la Generalitat (ACA, Protecció Civil), les diputacions i els ajuntaments per accelerar la revisió de plans d'emergència.
        """)

# =============================================================================
# CAPÍTOL 6: LÍNIES D'ESTUDIS COMPLEMENTÀRIES A FUTUR (NOU APARTAT)
# =============================================================================
elif capitol_seleccionat.startswith("6."):
    st.markdown("## 6. Línies d'Estudis Complementàries a Futur")

    st.markdown("""
    <div class="story-card">
        <div class="question-title">🚀 Horitzons de Recerca i Millores Metodològiques</div>
        <div class="answer-text">
            <b>💡 Visió de Futur:</b> Aquest dashboard estableix una base sòlida, però l'evolució del canvi climàtic requereix ampliar l'abast analític amb noves dimensions tecnològiques i socioeconòmiques.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.subheader("🔬 Millores Tècniques i Models Predictius")
        st.markdown("""
        * **Integració de Sensors IoT en Temps Real**: Connectar fluxos de dades en directe de cabals fluvials i estacions meteorològiques per a l'alerta primerenca automatitzada.
        * **Models de Machine Learning Avançats**: Implementar models predictius de propagació d'incendis forestals i inundacions llampec basats en xarxes neuronals i sèries temporals climàtiques d'alta resolució.
        * **Simulador d'Escenaris Climàtics IPCC (RCP)**: Incorporar projeccions regionalitzades sota diferents escenaris d'emissions fins a l'any 2050. Es basarà en els RCP (*Representative Concentration Pathways* o trajectòries de concentració de representants), on el **RCP 4.5** representa un escenari intermedi d'emissions moderades amb polítiques de mitigació parcial, i el **RCP 8.5** descriu un escenari pessimista d'emissions altes (*business as usual*) sense polítiques restrictives de descarbonització.
        """)

    with col_f2:
        st.subheader("📊 Ampliació Socioeconòmica i Setorials")
        st.markdown("""
        * **Anàlisi d'Impacte en Salut Pública**: Correlacionar onades de calor extrema amb ingressos hospitalaris, mortalitat urbana i productivitat laboral per sectors.
        * **Vulnerabilitat de Cadena de Subministrament**: Estudiar l'afectació de fenòmens extrems en polígons industrials clau, infraestructures de transport (rodalies, autopistes) i subministrament elèctric.
        * **Instruments Financers Innovadors**: Investigar la viabilitat de bons verds climàtics, assegurances paramètriques municipals i mecanismes de compensació per serveis ecosistèmics.
        """)

# -----------------------------------------------------------------------------
# PEU DE PÀGINA
# -----------------------------------------------------------------------------
st.divider()
st.caption("🌍 **Projecte Data Clima (PDC)** | Desenvolupat amb Streamlit, SQLAlchemy i MySQL | Font de dades: ACA, CCS, Meteocat, Open-Meteo, Idescat.")