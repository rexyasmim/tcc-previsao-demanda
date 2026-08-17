"""
Correção da análise de WAPE por categoria.

Bug identificado: a versão anterior agrupava só por
`product_category_name`, sem filtrar por `cenario` e `modelo`
antes — misturando resultados de cenários/modelos diferentes
na mesma linha (evidência: quantidade_observacoes = 12 ou 24
em vez de 3, que é o esperado — 1 valor por mês de teste).

Uso:
    python -m python.model.wape_by_category
"""

import pandas as pd

INPUT_PATH = "docs/predictions_test_consolidado.csv"
OUTPUT_PATH = "docs/wape_por_categoria.csv"

CENARIO_OPERACIONAL = "Sem Pareto (74 categorias)"
MODELO_OPERACIONAL = "Naive (mês anterior)"  # precisa bater EXATAMENTE com o CSV


def calcular_wape_por_categoria(df, cenario, modelo):
    # Filtro explícito — este é o passo que estava faltando na versão anterior
    subset = df[(df["cenario"] == cenario) & (df["modelo"] == modelo)].copy()

    if subset.empty:
        raise ValueError(
            f"Nenhuma linha encontrada para cenario={cenario!r}, modelo={modelo!r}. "
            f"Confira os valores exatos com df['cenario'].unique() e df['modelo'].unique()."
        )

    resumo = (
        subset.groupby("product_category_name")
        .agg(
            demanda_real=("demanda_real", "sum"),
            erro_absoluto=("erro_absoluto", "sum"),
            quantidade_observacoes=("demanda_real", "count"),
        )
        .reset_index()
    )

    # Sanity check: com 3 meses de teste, TEM que ser 3 por categoria
    inesperado = resumo[resumo["quantidade_observacoes"] != 3]
    if not inesperado.empty:
        print("ATENÇÃO: categorias com quantidade_observacoes != 3 (investigar):")
        print(inesperado)

    # Categorias com demanda real total = 0 no período de teste: WAPE é
    # matematicamente indefinido (divisão por zero). Filtrar, não mostrar 'inf'.
    sem_demanda = resumo[resumo["demanda_real"] == 0]
    if not sem_demanda.empty:
        print(f"\n{len(sem_demanda)} categorias com demanda_real=0 no teste "
              f"(WAPE indefinido, removidas do relatório):")
        print(sem_demanda["product_category_name"].tolist())

    resumo = resumo[resumo["demanda_real"] > 0].copy()
    resumo["WAPE"] = (resumo["erro_absoluto"] / resumo["demanda_real"]) * 100
    resumo = resumo.sort_values("WAPE", ascending=False)

    return resumo


def main():
    df = pd.read_csv(INPUT_PATH, parse_dates=["date"])

    print("Cenários disponíveis:", df["cenario"].unique())
    print("Modelos disponíveis:", df["modelo"].unique())

    resumo = calcular_wape_por_categoria(df, CENARIO_OPERACIONAL, MODELO_OPERACIONAL)

    print(f"\nWAPE por categoria — {CENARIO_OPERACIONAL} / {MODELO_OPERACIONAL}")
    print(f"Total de categorias no relatório: {len(resumo)}")
    print(resumo.to_string(index=False))

    resumo.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSalvo em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
