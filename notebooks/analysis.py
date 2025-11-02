# %%
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os

# %%
# Configuração da página
st.set_page_config(
    page_title="Análise Dengue vs Clima - Marília/SP", page_icon="🦟", layout="wide"
)

# Título principal
st.title("🦟 Análise: Casos de Dengue vs Condições Climáticas")
st.subheader("Município de Marília/SP - Período 2020-2024")


# %%
@st.cache_data
def carregar_dados():
    # Carregar dados de dengue
    arquivos_dengue = glob.glob("../data/processed/DENGBR*_MARILIA.csv")
    df_dengue_list = []
    for arquivo in arquivos_dengue:
        df = pd.read_csv(arquivo, sep=";")
        df_dengue_list.append(df)
    df_dengue = pd.concat(df_dengue_list, ignore_index=True)

    # Carregar dados climáticos
    arquivos_inmet = glob.glob("../data/processed/INMET_*_FILTRADO.csv")
    df_inmet_list = []
    for arquivo in arquivos_inmet:
        df = pd.read_csv(arquivo, sep=";")
        df_inmet_list.append(df)
    df_inmet = pd.concat(df_inmet_list, ignore_index=True)

    return df_dengue, df_inmet


# Carregar dados
with st.spinner("Carregando dados..."):
    df_dengue, df_inmet = carregar_dados()

# %%
# Sidebar com filtros
st.sidebar.header("Filtros")
ano_selecionado = st.sidebar.selectbox(
    "Selecione o Ano:", options=["Todos"] + sorted(df_dengue["NU_ANO"].unique())
)

variavel_climatica = st.sidebar.selectbox(
    "Variável Climática:", options=["Temperatura", "Precipitação", "Umidade"]
)

# %%
# Processamento dos dados
# Converter datas
df_dengue["DT_NOTIFIC"] = pd.to_datetime(
    df_dengue["DT_NOTIFIC"], format="%d/%m/%Y", errors="coerce"
)
df_inmet["data"] = pd.to_datetime(df_inmet["data"], format="%Y/%m/%d", errors="coerce")

# Agrupar dados por mês
df_dengue_mensal = (
    df_dengue.groupby(pd.Grouper(key="DT_NOTIFIC", freq="M"))
    .size()
    .reset_index(name="casos")
)
df_inmet_mensal = (
    df_inmet.groupby(pd.Grouper(key="data", freq="M"))
    .agg(
        {
            "precipitacao_total": "sum",
            "temperatura_c": "mean",
            "umidade_relativa_percent": "mean",
        }
    )
    .reset_index()
)

# Juntar dados
df_analise = pd.merge(
    df_dengue_mensal.rename(columns={"DT_NOTIFIC": "data"}),
    df_inmet_mensal,
    on="data",
    how="inner",
)
