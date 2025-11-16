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
st.title("🦟 Casos de Dengue vs Condições Climáticas")
st.subheader("Município de Marília/SP")


# Função para carregar dados
@st.cache_data
def carregar_dados():
    try:
        # Carregar dados de dengue
        arquivos_dengue = glob.glob("DENGBR*_MARILIA.csv")
        df_dengue_list = []
        for arquivo in arquivos_dengue:
            df = pd.read_csv(arquivo, sep=";")
            df_dengue_list.append(df)
        df_dengue = pd.concat(df_dengue_list, ignore_index=True)

        # Carregar dados climáticos
        arquivos_inmet = glob.glob("INMET_*_FILTRADO.csv")
        df_inmet_list = []
        for arquivo in arquivos_inmet:
            df = pd.read_csv(arquivo, sep=";")
            df_inmet_list.append(df)
        df_inmet = pd.concat(df_inmet_list, ignore_index=True)

        return df_dengue, df_inmet
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()


# Carregar dados
with st.spinner("Carregando dados..."):
    df_dengue, df_inmet = carregar_dados()

# Verificar se os dados foram carregados corretamente
if df_dengue.empty or df_inmet.empty:
    st.error(
        "Não foi possível carregar os dados. Verifique se os arquivos existem na pasta 'processed'."
    )
    st.stop()

# Sidebar com filtros
st.sidebar.header("Filtros")
variavel_climatica = st.sidebar.selectbox(
    "Variável Climática:", options=["Temperatura", "Precipitação", "Umidade"]
)

# Processamento dos dados com tratamento de erros
try:
    # Converter datas
    df_dengue["DT_NOTIFIC"] = pd.to_datetime(df_dengue["DT_NOTIFIC"], errors="coerce")
    df_inmet["data"] = pd.to_datetime(df_inmet["data"], errors="coerce")

    # Remover linhas com datas inválidas
    df_dengue = df_dengue.dropna(subset=["DT_NOTIFIC"])
    df_inmet = df_inmet.dropna(subset=["data"])

    # Criar coluna de ano-mês para agrupamento
    df_dengue["ano_mes"] = df_dengue["DT_NOTIFIC"].dt.to_period("M")
    df_inmet["ano_mes"] = df_inmet["data"].dt.to_period("M")

    # Agrupar casos por mês
    df_dengue_mensal = df_dengue.groupby("ano_mes").size().reset_index(name="casos")
    df_dengue_mensal["data"] = df_dengue_mensal["ano_mes"].dt.to_timestamp()

    # Agrupar dados climáticos por mês
    df_inmet_mensal = (
        df_inmet.groupby("ano_mes")
        .agg(
            {
                "precipitacao_total": "sum",
                "temperatura_c": "mean",
                "umidade_relativa_percent": "mean",
            }
        )
        .reset_index()
    )
    df_inmet_mensal["data"] = df_inmet_mensal["ano_mes"].dt.to_timestamp()

    # Juntar dados
    df_analise = pd.merge(
        df_dengue_mensal[["data", "casos"]],
        df_inmet_mensal[
            ["data", "precipitacao_total", "temperatura_c", "umidade_relativa_percent"]
        ],
        on="data",
        how="inner",
    )

    # Remover qualquer linha com NaT restante
    df_analise = df_analise.dropna()

except Exception as e:
    st.error(f"Erro no processamento dos dados: {e}")
    st.stop()

# Verificar se temos dados válidos
if df_analise.empty:
    st.error("Não há dados válidos para análise após o processamento.")
    st.stop()

# Métricas principais
st.header("Visão Geral")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Casos", f"{len(df_dengue):,}")

# Formatação segura das datas
if not df_analise.empty:
    data_min = df_analise["data"].min()
    data_max = df_analise["data"].max()
    periodo_texto = (
        f"{data_min.year}-{data_max.year}"
        if pd.notna(data_min) and pd.notna(data_max)
        else "N/A"
    )
else:
    periodo_texto = "N/A"

col2.metric("Período Analisado", periodo_texto)
col3.metric("Média Mensal de Casos", f"{df_analise['casos'].mean():.1f}")
col4.metric("Máximo Mensal", f"{df_analise['casos'].max():.0f}")

# Gráfico 1: Série Temporal
st.header("Série Temporal - Casos vs Clima")

# Selecionar variável climática para o gráfico
var_map = {
    "Temperatura": ("temperatura_c", "°C", "red"),
    "Precipitação": ("precipitacao_total", "mm", "blue"),
    "Umidade": ("umidade_relativa_percent", "%", "green"),
}

var_nome, var_unidade, var_cor = var_map[variavel_climatica]

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(
    go.Scatter(
        x=df_analise["data"],
        y=df_analise["casos"],
        name="Casos de Dengue",
        line=dict(color="orange"),
    ),
    secondary_y=False,
)
fig1.add_trace(
    go.Scatter(
        x=df_analise["data"],
        y=df_analise[var_nome],
        name=f"{variavel_climatica} ({var_unidade})",
        line=dict(color=var_cor),
    ),
    secondary_y=True,
)
fig1.update_layout(title=f"Casos de Dengue vs {variavel_climatica} ao Longo do Tempo")
fig1.update_xaxes(title_text="Data")
fig1.update_yaxes(title_text="Casos de Dengue", secondary_y=False)
fig1.update_yaxes(title_text=f"{variavel_climatica} ({var_unidade})", secondary_y=True)

st.plotly_chart(fig1, use_container_width=True)

# Breve explicação da Série Temporal
st.write(
    "Série temporal: mostra a evolução mensal dos casos de dengue (linha laranja) "
    "em comparação com a variável climática selecionada (linha secundária). "
    "Observe picos e possíveis defasagens entre clima e ocorrência de casos."
)

# Gráfico 3: Análise Sazonal
st.header("Análise Sazonal")

df_analise["mes"] = df_analise["data"].dt.month
df_analise["ano"] = df_analise["data"].dt.year

# Casos médios por mês
casos_por_mes = df_analise.groupby("mes")["casos"].mean().reset_index()

fig3 = px.bar(
    casos_por_mes,
    x="mes",
    y="casos",
    title="Média de Casos de Dengue por Mês",
    labels={"mes": "Mês", "casos": "Casos Médios"},
)
fig3.update_xaxes(
    tickvals=list(range(1, 13)),
    ticktext=[
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ],
)
st.plotly_chart(fig3, use_container_width=True)

# Breve explicação da Análise Sazonal
st.write(
    "Análise sazonal: barra com a média de casos por mês. "
    "Ajuda a identificar meses com maior tendência de ocorrência de dengue."
)

# Gráfico 4: Comparação entre Anos
st.header("Comparação entre Anos")

if len(df_analise["ano"].unique()) > 1:
    fig4 = px.box(df_analise, x="ano", y="casos", title="Distribuição de Casos por Ano")
    st.plotly_chart(fig4, use_container_width=True)

    # Breve explicação da Comparação entre Anos
    st.write(
        "Comparação entre anos: boxplots que mostram a distribuição mensal de casos para cada ano, "
        "destacando mediana, variabilidade e outliers."
    )


# Gráfico 5: Scatter Plot
st.header("Dispersão - Casos vs Variáveis Climáticas")

fig7 = px.scatter(
    df_analise,
    x=var_nome,
    y="casos",
    title=f"Relação entre {variavel_climatica} e Casos de Dengue",
    labels={
        var_nome: f"{variavel_climatica} ({var_unidade})",
        "casos": "Casos de Dengue",
    },
)
st.plotly_chart(fig7, use_container_width=True)

# Breve explicação do Scatter Plot
st.write(
    "Dispersão: relação entre a variável climática selecionada e o número de casos. "
    "Use para avaliar correlação visual e procurar padrões (pontos dispersos, tendência)."
)

# Informações técnicas
with st.expander("Informações Técnicas"):
    st.write(
        f"""
    **Fonte dos Dados:**
    - Dengue: Sistemas DENGBR (Ministério da Saúde)
    - Clima: INMET (Estação Marília/SP)
    
    **Período:** {df_analise['data'].min().strftime('%d/%m/%Y')} a {df_analise['data'].max().strftime('%d/%m/%Y')}
    **Total de Registros:** {len(df_dengue):,} casos de dengue
    **Município:** Marília/SP (Código IBGE: 352900)
    
    **Variáveis Climáticas:**
    - Temperatura: Média diária (°C)
    - Precipitação: Acumulado diário (mm)
    - Umidade: Média diária (%)
    """
    )

# Tabela com dados resumidos
with st.expander("Dados Resumidos"):
    st.dataframe(df_analise.sort_values("data", ascending=False).head(10))

# Rodapé
st.markdown("---")
st.markdown("**Projeto Integrador UNIVESP - 2025**")
st.markdown("Angela Luisa da Silva Lopes")
st.markdown("Lodiane Gabriely Queiroz da Conceição")
st.markdown("Nicolas Francisco de Melo")

# %%
