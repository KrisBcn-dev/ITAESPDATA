# ==============================================================================
# DASHBOARD INTERACTIVO CON STREAMLIT
# ==============================================================================
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Dashboard Comercial - Vendes", layout="wide")

st.title("📊 Dashboard Executiu de Vendes i Comercial")


# ---------------------------------------------------------
# 1. CONEXIÓN A BASE DE DATOS MYSQL Y CARGA
# ---------------------------------------------------------
@st.cache_data
def load_data_from_mysql():
    # Parámetros de conexión a la BD MySQL
    DB_USER = "ruser"
    DB_PASS = "2026Ruser1."  
    DB_HOST = "127.0.0.1"  
    DB_PORT = "3306"
    DB_NAME = "sales"

    try:
        # String de conexión SQLAlchemy para MySQL utilizando pymysql
        connection_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_url)

        # Lectura directa desde las tablas de la base de datos 'sales'
        df_transactions = pd.read_sql("SELECT * FROM transactions", con=engine)
        df_companies = pd.read_sql("SELECT * FROM companies", con=engine)
        df_users = pd.read_sql("SELECT * FROM users", con=engine)
        df_products = pd.read_sql("SELECT * FROM products", con=engine)

    except Exception as e:
        st.error(
            f" Error de conexión a la base de datos MySQL '{DB_NAME}': {e}"
        )
        st.stop()

    # Filtrar transacciones válidas (declined == 0)
    df_valid = df_transactions[df_transactions["declined"] == 0].copy()
    df_valid["timestamp"] = pd.to_datetime(df_valid["timestamp"])

    # Unión relacional con Companies (por país de la empresa vendedora)
    df_merged = pd.merge(
        df_valid,
        df_companies[["company_id", "country"]].rename(
            columns={"country": "pais_empresa"}
        ),
        left_on="business_id",
        right_on="company_id",
        how="left",
    )

    # Unión relacional con Users (por país del usuario comprador)
    df_merged = pd.merge(
        df_merged,
        df_users[["id", "country"]].rename(
            columns={"country": "pais_usuario"}
        ),
        left_on="user_id",
        right_on="id",
        how="left",
    )

    # Determinación del mercado (Local vs Internacional)
    df_merged["tipo_compra"] = np.where(
        df_merged["pais_empresa"] == df_merged["pais_usuario"],
        "Local",
        "Internacional",
    )

    #Desanidado de la columna product_ids
    df_merged["product_id_list"] = (
        df_merged["product_ids"].astype(str).str.split(",")
    )
    df_exploded = df_merged.explode("product_id_list")
    df_exploded["product_id"] = pd.to_numeric(
        df_exploded["product_id_list"].str.strip(), errors="coerce"
    )

    # Unión relacional con Products
    df_full_products = pd.merge(
        df_exploded,
        df_products[["id", "product_name"]],
        left_on="product_id",
        right_on="id",
        how="left",
    )

    return df_merged, df_full_products


# Cargar datos desde MySQL
df_transactions_clean, df_products_clean = load_data_from_mysql()

# ---------------------------------------------------------
# SIDEBAR: FILTROS DINÁMICOS INTERACTIVOS
# ---------------------------------------------------------
st.sidebar.header("🔍 Filtres Comercials")

# Filtro 1: Rango de Fechas
min_date = df_transactions_clean["timestamp"].min().date()
max_date = df_transactions_clean["timestamp"].max().date()

rango_fechas = st.sidebar.date_input(
    "Selecciona el Rang de Dates",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

# Filtro 2: Tipos de Compra (Local / Internacional)
opciones_tipo = df_transactions_clean["tipo_compra"].unique().tolist()
tipo_seleccion = st.sidebar.multiselect(
    "Tipus de Venda (Mercat)", options=opciones_tipo, default=opciones_tipo
)

# Aplicación de los filtros
if len(rango_fechas) == 2:
    f_inicio, f_fin = rango_fechas
    mask_date = (df_transactions_clean["timestamp"].dt.date >= f_inicio) & (
        df_transactions_clean["timestamp"].dt.date <= f_fin
    )
    mask_date_prod = (df_products_clean["timestamp"].dt.date >= f_inicio) & (
        df_products_clean["timestamp"].dt.date <= f_fin
    )
else:
    mask_date = True
    mask_date_prod = True

mask_tipo = df_transactions_clean["tipo_compra"].isin(tipo_seleccion)
mask_tipo_prod = df_products_clean["tipo_compra"].isin(tipo_seleccion)

df_filtered = df_transactions_clean[mask_date & mask_tipo]
df_prod_filtered = df_products_clean[mask_date_prod & mask_tipo_prod]

# ---------------------------------------------------------
# INDICADORES CLAVE DE NEGOCIO (KPIs)
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
facturacion_total = df_filtered["amount"].sum()
total_transacciones = len(df_filtered)
ticket_medio = (
    df_filtered["amount"].mean() if total_transacciones > 0 else 0.0
)
pct_internacional = (
    (df_filtered["tipo_compra"] == "Internacional").mean() * 100
    if total_transacciones > 0
    else 0.0
)

col1.metric("Facturació Total", f"{facturacion_total:,.2f} €")
col2.metric("Total Transaccions", f"{total_transacciones:,}")
col3.metric("Ticket Mitjà", f"{ticket_medio:,.2f} €")
col4.metric("% Venda Internacional", f"{pct_internacional:.1f}%")

st.markdown("---")

# ---------------------------------------------------------
# VISUALIZACIONES DINÁMICAS (Dos gráficos por columna, dos columnas)
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("1. Evolució Temporal de la Facturació (€)")
    df_temp = (
        df_filtered.set_index("timestamp")
        .resample("M")["amount"]
        .sum()
        .reset_index()
    )
    fig1 = px.line(
        df_temp,
        x="timestamp",
        y="amount",
        markers=True,
        labels={"timestamp": "Data / Mes", "amount": "Facturació (€)"},
        color_discrete_sequence=["#1f77b4"],
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("3. Top 10 Productes més Venuts (€)")
    df_top_prod = (
        df_prod_filtered.groupby("product_name")["amount"]
        .sum()
        .nlargest(10)
        .reset_index()
    )
    fig3 = px.bar(
        df_top_prod,
        x="amount",
        y="product_name",
        orientation="h",
        labels={"amount": "Ingressos (€)", "product_name": "Producte"},
        color="amount",
        color_continuous_scale="Blues",
    )
    fig3.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

with col_right:
    st.subheader("2. Proporció del Mercat (Local vs Internacional)")
    fig2 = px.pie(
        df_filtered,
        names="tipo_compra",
        values="amount",
        color="tipo_compra",
        color_discrete_map={"Local": "#2ecc71", "Internacional": "#e74c3c"},
        hole=0.4,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("4. Distribució de la Demanda per País")
    df_pais = (
        df_filtered.groupby("pais_usuario")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    fig4 = px.bar(
        df_pais,
        x="pais_usuario",
        y="amount",
        labels={
            "pais_usuario": "País de l'Usuari",
            "amount": "Ingressos (€)",
        },
        color_discrete_sequence=["#27ae60"],
    )
    st.plotly_chart(fig4, use_container_width=True)