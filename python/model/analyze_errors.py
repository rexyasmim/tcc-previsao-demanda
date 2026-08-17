"""
Análise de erro dos modelos, usando o CSV consolidado gerado por
consolidate_and_plot.py (docs/predictions_test_consolidado.csv).

Cobre:
1. Direção do erro (super/subestimação) por modelo/cenário
2. Categorias que mais erram
3. Erro por mês (para investigar tendência)
4. Comportamento nas categorias de maior demanda
5. Impacto das linhas com demanda real = 0
6. Comportamento específico da categoria 'outras' (cenário Com Pareto)

Convenção de sinal: erro = demanda_real - demanda_prevista
    erro > 0  -> modelo SUBESTIMOU (previu menos que o real)
    erro < 0  -> modelo SUPERESTIMOU (previu mais que o real)
"""

from pathlib import Path

import pandas as pd

INPUT_PATH = Path("docs") / "predictions_test_consolidado.csv"

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
pd.set_option("display.width", 120)


def load_data():
    df = pd.read_csv(INPUT_PATH, parse_dates=["date"])

    df["cenario"] = "Sem Pareto (74 categorias)"
    df["modelo"] = "Naive Lag-1"

    return df


def secao(titulo):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


def analise_direcao_erro(df):
    secao("1. DIREÇÃO DO ERRO (viés médio) — por cenário/modelo")
    print("erro médio > 0 => modelo SUBESTIMA | erro médio < 0 => modelo SUPERESTIMA\n")

    resumo = (
        df.groupby(["cenario", "modelo"])
        .agg(
            erro_medio=("erro", "mean"),
            erro_absoluto_medio=("erro_absoluto", "mean"),
        )
        .reset_index()
        .sort_values(["cenario", "erro_absoluto_medio"])
    )
    print(resumo.to_string(index=False))
    return resumo


def analise_categorias_mais_erram(df, top_n=5):
    secao(f"2. TOP {top_n} CATEGORIAS QUE MAIS ERRAM — por cenário/modelo")

    resumo = (
        df.groupby(["cenario", "modelo", "product_category_name"])
        ["erro_absoluto"].mean()
        .reset_index()
    )

    for cenario in resumo["cenario"].unique():
        print(f"\n--- {cenario} ---")
        for modelo in resumo[resumo["cenario"] == cenario]["modelo"].unique():
            subset = resumo[
                (resumo["cenario"] == cenario) & (resumo["modelo"] == modelo)
            ].sort_values("erro_absoluto", ascending=False).head(top_n)
            print(f"\n{modelo}:")
            print(subset[["product_category_name", "erro_absoluto"]].to_string(index=False))


def analise_erro_por_mes(df):
    secao("3. ERRO POR MÊS (verificar se piora/melhora ao longo do teste)")

    resumo = (
        df.groupby(["cenario", "modelo", "date"])
        .agg(erro_medio=("erro", "mean"), erro_absoluto_medio=("erro_absoluto", "mean"))
        .reset_index()
    )
    print(resumo.to_string(index=False))


def analise_categorias_maior_demanda(df, top_n=5):
    secao(f"4. ERRO NAS {top_n} CATEGORIAS DE MAIOR DEMANDA (cenário Sem Pareto)")

    subset_cenario = df[df["cenario"] == "Sem Pareto (74 categorias)"]
    top_categorias = (
        subset_cenario.groupby("product_category_name")["demanda_real"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )

    resumo = (
        subset_cenario[subset_cenario["product_category_name"].isin(top_categorias)]
        .groupby(["modelo", "product_category_name"])
        .agg(erro_medio=("erro", "mean"), erro_absoluto_medio=("erro_absoluto", "mean"))
        .reset_index()
    )
    print(resumo.to_string(index=False))


def analise_impacto_zeros(df):
    secao("5. IMPACTO DAS LINHAS COM DEMANDA REAL = 0")

    df = df.copy()
    df["is_zero"] = df["demanda_real"] == 0

    resumo = (
        df.groupby(["cenario", "modelo", "is_zero"])
        ["erro_absoluto"].mean()
        .reset_index()
        .pivot_table(
            index=["cenario", "modelo"], columns="is_zero", values="erro_absoluto"
        )
        .rename(columns={False: "erro_abs_medio_demanda>0", True: "erro_abs_medio_demanda=0"})
    )
    print(resumo.to_string())

    n_zeros = df.groupby("cenario")["is_zero"].sum()
    print(f"\nQuantidade de linhas com demanda=0 no teste, por cenário:\n{n_zeros}")


def analise_categoria_outras(df):
    secao("6. COMPORTAMENTO DA CATEGORIA 'outras' (cenário Com Pareto)")

    subset = df[
        (df["cenario"] == "Com Pareto (categorias + 'outras')")
        & (df["product_category_name"] == "outras")
    ]

    if subset.empty:
        print("Categoria 'outras' não encontrada — confira se o Pareto foi aplicado.")
        return

    print(subset[["date", "modelo", "demanda_real", "demanda_prevista", "erro", "erro_absoluto"]]
          .to_string(index=False))


def main():
    df = load_data()

    analise_direcao_erro(df)
    analise_categorias_mais_erram(df)
    analise_erro_por_mes(df)
    analise_categorias_maior_demanda(df)
    analise_impacto_zeros(df)
    analise_categoria_outras(df)


if __name__ == "__main__":
    main()
