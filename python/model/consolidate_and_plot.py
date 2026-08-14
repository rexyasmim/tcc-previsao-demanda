"""
Consolida os CSVs de previsão (gerados separadamente por cenário/modelo)
num único DataFrame, e gera o gráfico Real x Previsto agregado por cenário.

Espera os arquivos em docs/, com o padrão de nome:
    previsoes_<cenario>_<modelo>.csv
    (ex: previsoes_pareto_random_forest.csv)

Cada CSV já vem com colunas: date, product_category_name, demanda_real,
demanda_prevista, erro, erro_absoluto. Os arquivos "naive" não têm as
colunas cenario/modelo — são preenchidas aqui a partir do nome do arquivo.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DOCS_DIR = Path("docs")
OUTPUT_CONSOLIDATED = DOCS_DIR / "predictions_test_consolidado.csv"

# Nome do arquivo -> (cenário, nome do modelo para exibição)
FILES = {
    "previsoes_sem_pareto_naive.csv": ("Sem Pareto (74 categorias)", "Naive (mês anterior)"),
    "previsoes_sem_pareto_linear_regression.csv": ("Sem Pareto (74 categorias)", "Linear Regression"),
    "previsoes_sem_pareto_random_forest.csv": ("Sem Pareto (74 categorias)", "Random Forest"),
    "previsoes_sem_pareto_gradient_boosting.csv": ("Sem Pareto (74 categorias)", "Gradient Boosting"),
    "previsoes_pareto_naive.csv": ("Com Pareto (categorias + 'outras')", "Naive (mês anterior)"),
    "previsoes_pareto_linear_regression.csv": ("Com Pareto (categorias + 'outras')", "Linear Regression"),
    "previsoes_pareto_random_forest.csv": ("Com Pareto (categorias + 'outras')", "Random Forest"),
    "previsoes_pareto_gradient_boosting.csv": ("Com Pareto (categorias + 'outras')", "Gradient Boosting"),
}


def load_and_consolidate():
    dfs = []
    for filename, (cenario, modelo) in FILES.items():
        path = DOCS_DIR / filename
        df = pd.read_csv(path, parse_dates=["date"])

        # Os arquivos naive não têm essas colunas — preenche a partir do nome do arquivo.
        # Os demais já têm, mas sobrescrevemos com o mesmo valor para garantir
        # consistência de rótulo entre todos os arquivos.
        df["cenario"] = cenario
        df["modelo"] = modelo

        dfs.append(df)

    consolidado = pd.concat(dfs, ignore_index=True)
    consolidado.to_csv(OUTPUT_CONSOLIDATED, index=False)
    print(f"Consolidado salvo em {OUTPUT_CONSOLIDATED} ({len(consolidado)} linhas)")
    return consolidado


def plot_scenario(df, cenario, filename_suffix):
    subset = df[df["cenario"] == cenario]

    # Demanda real: pega de qualquer um dos modelos (é a mesma), agregada por mês
    real_by_month = (
        subset[subset["modelo"] == "Naive (mês anterior)"]
        .groupby("date")["demanda_real"].sum()
    )

    plt.figure(figsize=(10, 5))
    plt.plot(
        real_by_month.index, real_by_month.values,
        marker="o", linewidth=2.5, color="black", label="Real",
    )

    for modelo in subset["modelo"].unique():
        pred_by_month = (
            subset[subset["modelo"] == modelo]
            .groupby("date")["demanda_prevista"].sum()
        )
        plt.plot(pred_by_month.index, pred_by_month.values,
                  marker="o", linestyle="--", label=modelo)

    plt.title(f"Real x Previsto — {cenario}")
    plt.xlabel("Mês (período de teste)")
    plt.ylabel("Demanda total (soma de todas as categorias)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"images/real_vs_previsto_{filename_suffix}.png")
    plt.show()


def main():
    df = load_and_consolidate()
    plot_scenario(df, "Sem Pareto (74 categorias)", "sem_pareto")
    plot_scenario(df, "Com Pareto (categorias + 'outras')", "com_pareto")


if __name__ == "__main__":
    main()
