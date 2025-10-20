# %%
import pandas as pd
import os


# %%
def processar_dengue():
    os.makedirs("../data/processed", exist_ok=True)

    for ano in [20, 21, 22, 23, 24]:
        arquivo_entrada = f"../data/raw/DENGBR{ano}.csv"
        arquivo_saida = f"../data/processed/DENGBR{ano}_MARILIA.csv"

        colunas_necessarias = [
            "ID_MUNICIP",
            "DT_NOTIFIC",
            "NU_ANO",
            "SG_UF",
            "CS_SEXO",
            "CS_RACA",
        ]
        chunks = []

        for chunk in pd.read_csv(
            arquivo_entrada,
            usecols=colunas_necessarias,
            low_memory=False,
            chunksize=50000,
        ):
            chunk_filtrado = chunk[chunk["ID_MUNICIP"] == 352900]
            if len(chunk_filtrado) > 0:
                chunks.append(chunk_filtrado)

        if chunks:
            df_final = pd.concat(chunks, ignore_index=True)
            df_final.to_csv(arquivo_saida, sep=";", index=False)
            print(f"Dengue {ano}: {len(df_final)} registros")


# %%
def processar_inmet():
    os.makedirs("../data/processed", exist_ok=True)

    for ano in [2020, 2021, 2022, 2023, 2024]:
        arquivo_entrada = f"../data/raw/INMET_{ano}.csv"
        arquivo_saida = f"../data/processed/INMET_{ano}_FILTRADO.csv"

        df = pd.read_csv(arquivo_entrada, sep=";", encoding="latin-1")

        colunas_manter = ["Data"]
        mapeamento_nomes = {"Data": "data"}

        for coluna in df.columns:
            if "TEMPERATURA DO AR - BULBO SECO" in coluna:
                colunas_manter.append(coluna)
                mapeamento_nomes[coluna] = "temperatura_c"
            elif "PRECIPITACAO TOTAL" in coluna:
                colunas_manter.append(coluna)
                mapeamento_nomes[coluna] = "precipitacao_total"
            elif "UMIDADE RELATIVA DO AR, HORARIA" in coluna:
                colunas_manter.append(coluna)
                mapeamento_nomes[coluna] = "umidade_relativa_percent"

            df_final = df[colunas_manter]
            df_final = df_final.rename(columns=mapeamento_nomes)

        # Corrigir valores decimais que começam com vírgula
        for coluna in [
            "precipitacao_total",
            "temperatura_c",
            "umidade_relativa_percent",
        ]:
            if coluna in df_final.columns:
                df_final[coluna] = (
                    df_final[coluna].astype(str).str.replace(",", ".", regex=False)
                )
                df_final[coluna] = df_final[coluna].str.replace(
                    r"^\.", "0.", regex=True
                )
                df_final[coluna] = df_final[coluna].str.replace(r"^;", "0;", regex=True)
                # Converter para numérico
                df_final[coluna] = pd.to_numeric(df_final[coluna], errors="coerce")

        df_final.to_csv(arquivo_saida, sep=";", index=False, encoding="utf-8")
        print(f"INMET {ano}: {len(df_final)} registros")


# %%
# Executar
# processar_dengue()
processar_inmet()

# %%
