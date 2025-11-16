# Projeto Integrador UNIVESP - Análise de Casos de Dengue em Marília - SP

## Introdução

Este projeto tem como objetivo analisar a relação entre o número de casos de dengue e as condições climáticas no município de Marília, São Paulo, durante o período de 2020 a 2024. A análise busca identificar possíveis correlações entre variáveis climáticas (temperatura, precipitação e umidade) e a incidência de dengue, utilizando dados públicos.

## Fontes de Dados

- **Casos de Dengue:** Os dados sobre os casos de dengue foram obtidos do Sistema de Informação de Agravos de Notificação (SINAN), disponibilizados publicamente.
- **Dados Meteorológicos:** As informações climáticas foram coletadas do Instituto Nacional de Meteorologia (INMET).

## Estrutura do Projeto

- **`data/`**: Contém os dados brutos (`raw`) e processados (`processed`) utilizados na análise.
- **`notebooks/`**: Contém os scripts Python para processamento de dados (`data_tratament.py`) e a aplicação web de visualização (`app.py`).
- **`config/`**: (A ser utilizado para configurações do projeto).
- **`docs/`**: (A ser utilizado para documentação adicional).

## Instalação

Para executar este projeto, você precisará ter Python 3.12 instalado. Clone o repositório e instale as dependências:

```bash
git clone <https://github.com/angielopes/pi-analise-dengue>
cd <pi-analise-dengue>
pip install -r requirements.txt
```

## Uso

1. **Processamento de Dados:**

Para processar os dados brutos, execute o script `data_tratament.py`:

```bash
python notebooks/data_tratament.py
```

2. **Visualização dos Dados:**

Para iniciar a aplicação web e visualizar os gráficos e análises, utilize o Streamlit:

```bash
streamlit run notebooks/app.py
```
