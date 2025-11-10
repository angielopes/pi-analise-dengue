import pandas as pd
import glob
import os


def analise_numerica():
    """Análise numérica dos dados de dengue vs clima"""

    print("ANÁLISE NUMÉRICA - DENGUE vs CONDIÇÕES CLIMÁTICAS")
    print("Município de Marília/SP")

    # Carregar dados
    try:
        # Dados de dengue
        arquivos_dengue = glob.glob("../data/processed/DENGBR*_MARILIA.csv")
        df_dengue_list = []
        for arquivo in arquivos_dengue:
            df = pd.read_csv(arquivo, sep=";")
            df_dengue_list.append(df)
        df_dengue = pd.concat(df_dengue_list, ignore_index=True)

        # Dados climáticos
        arquivos_inmet = glob.glob("../data/processed/INMET_*_FILTRADO.csv")
        df_inmet_list = []
        for arquivo in arquivos_inmet:
            df = pd.read_csv(arquivo, sep=";")
            df_inmet_list.append(df)
        df_inmet = pd.concat(df_inmet_list, ignore_index=True)

    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return

    # Processamento dos dados
    df_dengue["DT_NOTIFIC"] = pd.to_datetime(df_dengue["DT_NOTIFIC"], errors="coerce")
    df_inmet["data"] = pd.to_datetime(df_inmet["data"], errors="coerce")

    df_dengue = df_dengue.dropna(subset=["DT_NOTIFIC"])
    df_inmet = df_inmet.dropna(subset=["data"])

    # Agrupar por mês
    df_dengue["ano_mes"] = df_dengue["DT_NOTIFIC"].dt.to_period("M")
    df_inmet["ano_mes"] = df_inmet["data"].dt.to_period("M")

    df_dengue_mensal = df_dengue.groupby("ano_mes").size().reset_index(name="casos")
    df_dengue_mensal["data"] = df_dengue_mensal["ano_mes"].dt.to_timestamp()

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

    df_analise = pd.merge(
        df_dengue_mensal[["data", "casos"]],
        df_inmet_mensal[
            ["data", "precipitacao_total", "temperatura_c", "umidade_relativa_percent"]
        ],
        on="data",
        how="inner",
    )

    # ANÁLISE NUMÉRICA
    print("\n1. ESTATÍSTICAS GERAIS")
    print("-" * 50)
    print(f"Total de casos de dengue: {len(df_dengue):,}")
    print(
        f"Período analisado: {df_analise['data'].min().strftime('%d/%m/%Y')} a {df_analise['data'].max().strftime('%d/%m/%Y')}"
    )
    print(f"Média mensal de casos: {df_analise['casos'].mean():.1f}")
    print(f"Desvio padrão mensal: {df_analise['casos'].std():.1f}")
    print(f"Máximo mensal: {df_analise['casos'].max():.0f}")
    print(f"Mínimo mensal: {df_analise['casos'].min():.0f}")

    print("\n2. ESTATÍSTICAS CLIMÁTICAS")
    print("-" * 50)
    print(f"Temperatura média: {df_analise['temperatura_c'].mean():.1f}°C")
    print(f"Temperatura máxima média: {df_analise['temperatura_c'].max():.1f}°C")
    print(f"Temperatura mínima média: {df_analise['temperatura_c'].min():.1f}°C")
    print(
        f"Precipitação total acumulada: {df_analise['precipitacao_total'].sum():.1f} mm"
    )
    print(
        f"Precipitação média mensal: {df_analise['precipitacao_total'].mean():.1f} mm"
    )
    print(
        f"Umidade relativa média: {df_analise['umidade_relativa_percent'].mean():.1f}%"
    )

    print("\n3. CORRELAÇÕES")
    print("-" * 50)
    correlacoes = df_analise[
        ["casos", "temperatura_c", "precipitacao_total", "umidade_relativa_percent"]
    ].corr()
    print("Matriz de correlação:")
    print(f"Casos x Temperatura: {correlacoes.loc['casos', 'temperatura_c']:.3f}")
    print(f"Casos x Precipitação: {correlacoes.loc['casos', 'precipitacao_total']:.3f}")
    print(
        f"Casos x Umidade: {correlacoes.loc['casos', 'umidade_relativa_percent']:.3f}"
    )
    print(
        f"Temperatura x Precipitação: {correlacoes.loc['temperatura_c', 'precipitacao_total']:.3f}"
    )

    print("\n4. ANÁLISE SAZONAL")
    print("-" * 50)
    df_analise["mes"] = df_analise["data"].dt.month
    casos_por_mes = (
        df_analise.groupby("mes")
        .agg({"casos": "mean", "temperatura_c": "mean", "precipitacao_total": "mean"})
        .round(1)
    )

    meses = [
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
    ]

    for i, mes in enumerate(meses, 1):
        if i in casos_por_mes.index:
            dados_mes = casos_por_mes.loc[i]
            print(
                f"{mes}: {dados_mes['casos']:.1f} casos | {dados_mes['temperatura_c']:.1f}°C | {dados_mes['precipitacao_total']:.1f}mm"
            )

    print("\n5. ANÁLISE POR ANO")
    print("-" * 50)
    df_analise["ano"] = df_analise["data"].dt.year
    casos_por_ano = (
        df_analise.groupby("ano")
        .agg({"casos": "sum", "temperatura_c": "mean", "precipitacao_total": "sum"})
        .round(1)
    )

    for ano, dados in casos_por_ano.iterrows():
        print(
            f"{ano}: {dados['casos']:.0f} casos | {dados['temperatura_c']:.1f}°C | {dados['precipitacao_total']:.1f}mm"
        )

    print("\n7. MESES COM MAIOR INCIDÊNCIA")
    print("-" * 50)
    top_meses = df_analise.nlargest(5, "casos")[
        ["data", "casos", "temperatura_c", "precipitacao_total"]
    ]
    for _, mes in top_meses.iterrows():
        print(
            f"{mes['data'].strftime('%b/%Y')}: {mes['casos']:.0f} casos | {mes['temperatura_c']:.1f}°C | {mes['precipitacao_total']:.1f}mm"
        )

    print("\n" + "=" * 70)
    print("RESUMO DAS PRINCIPAIS CONCLUSÕES:")
    print("=" * 70)

    # Análise das correlações
    corr_temp = correlacoes.loc["casos", "temperatura_c"]
    corr_precip = correlacoes.loc["casos", "precipitacao_total"]
    corr_umid = correlacoes.loc["casos", "umidade_relativa_percent"]

    print(
        f"• Correlação temperatura-casos: {corr_temp:.3f} ({'positiva' if corr_temp > 0 else 'negativa'})"
    )
    print(
        f"• Correlação precipitação-casos: {corr_precip:.3f} ({'positiva' if corr_precip > 0 else 'negativa'})"
    )
    print(
        f"• Correlação umidade-casos: {corr_umid:.3f} ({'positiva' if corr_umid > 0 else 'negativa'})"
    )

    # Mês com maior incidência
    mes_max = df_analise.loc[df_analise["casos"].idxmax()]
    print(
        f"• Mês de maior incidência: {mes_max['data'].strftime('%B/%Y')} ({mes_max['casos']:.0f} casos)"
    )

    # Ano com maior incidência
    ano_max = casos_por_ano.loc[casos_por_ano["casos"].idxmax()]
    print(
        f"• Ano com maior número de casos: {casos_por_ano['casos'].idxmax()} ({ano_max['casos']:.0f} casos)"
    )


if __name__ == "__main__":
    analise_numerica()
