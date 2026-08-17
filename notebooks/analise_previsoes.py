import pandas as pd

ARQUIVOS = [
    "docs/previsoes_sem_pareto_linear_regression.csv",
    "docs/previsoes_sem_pareto_random_forest.csv",
    "docs/previsoes_sem_pareto_gradient_boosting.csv",
    "docs/previsoes_pareto_linear_regression.csv",
    "docs/previsoes_pareto_random_forest.csv",
    "docs/previsoes_pareto_gradient_boosting.csv",
]


def analisar_arquivo(caminho):
    df = pd.read_csv(caminho)

    print("\n" + "=" * 70)
    print(f"ARQUIVO: {caminho}")
    print("=" * 70)

    print("\nResumo:")
    print(df[[
        "demanda_real",
        "demanda_prevista",
        "erro",
        "erro_absoluto"
    ]].describe())

    print("\nErro médio:")
    print(df["erro"].mean())

    print("\nErro absoluto médio:")
    print(df["erro_absoluto"].mean())

    print("\nTop 10 maiores erros:")
    print(
        df.sort_values("erro_absoluto", ascending=False)
        [[
            "date",
            "product_category_name",
            "demanda_real",
            "demanda_prevista",
            "erro",
            "erro_absoluto"
        ]]
        .head(10)
        .to_string(index=False)
    )

    print("\nErro por categoria:")
    erro_categoria = (
        df.groupby("product_category_name")
        .agg(
            demanda_real=("demanda_real", "sum"),
            demanda_prevista=("demanda_prevista", "sum"),
            erro_medio=("erro", "mean"),
            erro_absoluto_medio=("erro_absoluto", "mean"),
        )
        .sort_values("erro_absoluto_medio", ascending=False)
    )

    print(erro_categoria.head(10).to_string())


def main():
    for arquivo in ARQUIVOS:
        analisar_arquivo(arquivo)


if __name__ == "__main__":
    main()