# %%
import pandas as pd
import json
import os


# %%
def criar_pasta_processed():
    """Cria a pasta processed se não existir"""
    pasta_processed = "../data/processed"
    if not os.path.exists(pasta_processed):
        os.makedirs(pasta_processed)
        print(f"Pasta criada: {pasta_processed}")
    return pasta_processed


# %%
def processar_dengue_chunks(caminho_entrada, caminho_saida, codigo_municipio="352900"):
    """Processa arquivos de dengue muito grandes usando chunks"""

    print(f"Processando {caminho_entrada} em chunks...")

    # Primeiro, descobrir qual é a coluna do município
    with pd.read_csv(
        caminho_entrada, encoding="utf-8", sep=",", chunksize=1000, low_memory=False
    ) as reader:
        primeiro_chunk = next(reader)

    # Identificar coluna do município
    coluna_municipio = None
    for col in primeiro_chunk.columns:
        if any(termo in col.lower() for termo in ["id_municip"]):
            coluna_municipio = col
            break

    if not coluna_municipio:
        print(f"  - AVISO: Coluna de município não encontrada em {caminho_entrada}")
        return

    print(f"  - Usando coluna: {coluna_municipio}")

    # Colunas a manter
    colunas_dengue = [
        "DT_NOTIFIC",  # Data da notificação
        "NU_ANO",  # Ano da notificação
        "ID_MUNICIP",  # Código do município
        "SG_UF",  # UF
        "CS_SEXO",  # Sexo
        "CS_RACA",  # Raça
    ]

    # Verificar quais colunas existem no arquivo
    colunas_existentes = [
        col for col in colunas_dengue if col in primeiro_chunk.columns
    ]
    print(f"  - Colunas a manter: {colunas_existentes}")

    # Processar em chunks e salvar apenas registros de Marília
    chunks = []
    total_registros = 0

    for chunk in pd.read_csv(
        caminho_entrada, encoding="utf-8", sep=",", chunksize=10000, low_memory=False
    ):
        chunk_filtrado = chunk[chunk[coluna_municipio].astype(str) == codigo_municipio]

        # Manter apenas as colunas selecionadas
        chunk_filtrado = chunk_filtrado[colunas_existentes]

        if len(chunk_filtrado) > 0:
            chunks.append(chunk_filtrado)
            total_registros += len(chunk_filtrado)

    if chunks:
        df_final = pd.concat(chunks, ignore_index=True)
        df_final.to_csv(caminho_saida, sep=";", index=False, encoding="utf-8")
        print(f"  - Total de registros para Marília: {total_registros}")
        print(f"  - Salvo em: {caminho_saida}")

        # Mostrar preview dos dados
        print(f"  - Preview das primeiras linhas:")
        print(df_final.head(3))
    else:
        print(f"  - Nenhum registro encontrado para Marília")


# %%
def processar_inmet():
    """Processa arquivos INMET mantendo apenas colunas essenciais"""

    # Mapeamento: nome simples -> padrão no arquivo
    padroes_originais = {
        "PRECIPITACAO_TOTAL_HORARIO_MM": ["PRECIPITAÇÃO TOTAL", "PRECIPITACAO"],
        "TEMPERATURA_AR_BULBO_SECO_C": ["TEMPERATURA DO AR", "BULBO SECO"],
        "UMIDADE_RELATIVA_AR_PORCENTO": ["UMIDADE RELATIVA", "HORARIA (%)"],
    }

    arquivos_inmet = ["../data/raw/INMET_2024.csv", "../data/raw/INMET_2025.csv"]
    pasta_processed = criar_pasta_processed()

    for arquivo in arquivos_inmet:
        print(f"Processando {arquivo}...")

        try:
            df = pd.read_csv(arquivo, sep=";", encoding="utf-8")

            print(f"  - Colunas disponíveis:")
            for col in df.columns:
                print(f"    '{col}'")

            # Encontrar colunas correspondentes
            colunas_para_manter = ["Data"]  # Sempre começa com Data

            for col_simples, padroes in padroes_originais.items():
                coluna_encontrada = None
                for col_real in df.columns:
                    if all(padrao.upper() in col_real.upper() for padrao in padroes):
                        coluna_encontrada = col_real
                        break

                if coluna_encontrada:
                    colunas_para_manter.append(coluna_encontrada)
                    print(f" {col_simples} -> {coluna_encontrada}")
                else:
                    print(f" Não encontrada: {col_simples}")

            # Manter apenas as colunas encontradas
            df_filtrado = df[colunas_para_manter]

            # Renomear para nomes simples
            mapeamento_renomear = {}
            for col in df_filtrado.columns:
                if col == "Data":
                    mapeamento_renomear[col] = "DATA"
                else:
                    for col_simples, padroes in padroes_originais.items():
                        if all(padrao.upper() in col.upper() for padrao in padroes):
                            mapeamento_renomear[col] = col_simples
                            break

            df_filtrado = df_filtrado.rename(columns=mapeamento_renomear)

            # Criar novo arquivo
            nome_arquivo = os.path.basename(arquivo)
            novo_arquivo = os.path.join(
                pasta_processed, nome_arquivo.replace(".csv", "_FILTRADO.csv")
            )
            df_filtrado.to_csv(novo_arquivo, sep=";", index=False, encoding="utf-8")

            print(f"  - Colunas finais: {list(df_filtrado.columns)}")
            print(f"  - Registros: {len(df_filtrado)}")
            print(f"  - Arquivo: {novo_arquivo}")
            print(f"  - Preview:")
            print(df_filtrado.head(2))
            print("\n")

        except Exception as e:
            print(f"Erro: {e}")


# %%
def processar_todos_arquivos():
    # Carregar configuração
    with open("../config/ingestion.json", "r") as open_json:
        ingestions = json.load(open_json)

    # Criar pasta processed
    pasta_processed = criar_pasta_processed()

    for item in ingestions:
        table = item["table"]
        path = item["path"]

        print(f"\nProcessando {table}...")

        try:
            if "DENGBR" in table:
                # Usar processamento em chunks para dengue
                # Criar novo caminho na pasta processed
                nome_arquivo = os.path.basename(path)  # Pega apenas o nome do arquivo
                novo_path = os.path.join(
                    pasta_processed, nome_arquivo.replace(".csv", "_MARILIA.csv")
                )
                processar_dengue_chunks(path, novo_path)

            elif "INMET" in table:
                # Já processamos INMET separadamente
                continue

        except Exception as e:
            print(f"ERRO em {table}: {e}")

    # Processar INMET separadamente
    print("\n" + "=" * 50)
    print("PROCESSANDO DADOS CLIMÁTICOS (INMET)")
    print("=" * 50)
    processar_inmet()


# Executar
processar_todos_arquivos()

print("\n" + "=" * 50)
print("PROCESSAMENTO CONCLUÍDO!")
print("=" * 50)
print("\nArquivos gerados na pasta ../data/processed/:")
print("- DENGBR24_MARILIA.csv")
print("- DENGBR25_MARILIA.csv")
print("- INMET_2024_FILTRADO.csv")
print("- INMET_2025_FILTRADO.csv")

# %%
