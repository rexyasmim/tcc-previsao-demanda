"""
Feature engineering para o modelo global de previsão de demanda
(uma linha = categoria x mês).

Decisões incorporadas (ver EDA, Sprint 7, e discussão de contexto):
- Remove meses de ramp-up da plataforma (< 2017-01), que têm
  demanda artificialmente baixa e não refletem sazonalidade real.
- Mês é codificado como seno/cosseno (variável cíclica), não como
  inteiro puro, para não sugerir que dezembro e janeiro são
  "distantes" um do outro.
- Lags e média móvel são calculados POR CATEGORIA (cada série
  segue seu próprio histórico).
- Linhas com NaN geradas pelos lags (início de cada série) são
  removidas — nunca preenchidas artificialmente.
"""

import numpy as np
import pandas as pd

from python.utils.database import engine

RAMP_UP_CUTOFF = "2017-01-01"
TEST_MONTHS = 3  # fonte única de verdade — train_and_evaluate.py importa daqui
PARETO_THRESHOLD = 0.90


def load_gold():
    df = pd.read_sql("SELECT * FROM gold.monthly_category_sales", engine)
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str) + "-01"
    )
    return df


def remove_ramp_up(df):
    """Remove o período inicial de baixo volume artificial da plataforma."""
    antes = len(df)
    df = df[df["date"] >= RAMP_UP_CUTOFF].copy()
    print(f"Ramp-up removido: {antes - len(df)} linhas descartadas "
          f"(mantidas: {len(df)})")
    return df


def compute_pareto_mapping(df, test_months=TEST_MONTHS, threshold=PARETO_THRESHOLD):
    """
    Calcula o mapeamento categoria original -> categoria final (Pareto/ABC).

    IMPORTANTE: o volume usado para decidir quais categorias são "grandes"
    considera SOMENTE o período de treino (exclui os últimos `test_months`
    meses). Calcular isso com o dataset inteiro (incluindo teste) seria
    vazamento de dado — a estrutura das features não pode "espiar" o
    período que será usado para avaliação.

    Regra: mantém a categoria com seu nome original se o volume acumulado
    ANTES dela (ordenando da maior para a menor) ainda não tiver passado
    de `threshold`. Caso contrário, agrupa em 'outras'.
    """
    meses_distintos = sorted(df["date"].unique())
    corte = meses_distintos[-test_months]
    treino = df[df["date"] < corte]

    volume = (
        treino.groupby("product_category_name")["demand"]
        .sum()
        .sort_values(ascending=False)
    )
    cum_pct = volume.cumsum() / volume.sum()
    cum_pct_antes = cum_pct.shift(1).fillna(0)

    mapping = {
        categoria: (categoria if antes < threshold else "outras")
        for categoria, antes in cum_pct_antes.items()
    }

    n_mantidas = sum(1 for v in mapping.values() if v != "outras")
    print(f"Pareto (calculado só no treino, corte {threshold:.0%}): "
          f"{n_mantidas} categorias mantidas + 'outras'")

    return mapping


def apply_pareto_grouping(df, mapping):
    """
    Aplica o mapeamento de categoria final e reagrega a demanda
    (soma as categorias que viraram 'outras' para o mesmo mês).
    """
    df = df.copy()
    df["product_category_name"] = df["product_category_name"].map(mapping)

    df = (
        df.groupby(["year", "month", "date", "product_category_name"], as_index=False)
        ["demand"].sum()
    )
    return df


def add_cyclical_month(df):
    """Codifica o mês como variável cíclica (seno/cosseno)."""
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def add_black_friday_flag(df):
    """Flag manual: novembro é mês de Black Friday no Brasil."""
    df["is_black_friday_month"] = (df["month"] == 11).astype(int)
    return df


def add_lag_and_rolling_features(df):
    """
    Cria features de lag e média móvel, calculadas independentemente
    por categoria (cada série usa apenas seu próprio histórico).
    """
    df = df.sort_values(["product_category_name", "date"]).copy()

    grouped = df.groupby("product_category_name")["demand"]

    df["demand_lag_1"] = grouped.shift(1)
    df["demand_lag_2"] = grouped.shift(2)

    # IMPORTANTE: usar .transform(), não encadear .shift().rolling() direto
    # na Series retornada pelo groupby. Encadear dessa forma quebra o
    # alinhamento de índice (bug real encontrado em 2024-XX-XX durante
    # o Sprint 7 — ver discussão no histórico do projeto). .transform()
    # garante que o cálculo respeita os limites de cada categoria E
    # retorna a Series já alinhada corretamente ao índice original.
    df["rolling_mean_3"] = grouped.transform(
        lambda s: s.shift(1).rolling(window=3).mean()
    )

    return df


def build_feature_dataset(apply_pareto=True):
    df = load_gold()
    df = remove_ramp_up(df)

    if apply_pareto:
        mapping = compute_pareto_mapping(df)
        df = apply_pareto_grouping(df, mapping)

    df = add_cyclical_month(df)
    df = add_black_friday_flag(df)
    df = add_lag_and_rolling_features(df)

    antes = len(df)
    df = df.dropna(subset=["demand_lag_1", "demand_lag_2", "rolling_mean_3"])
    print(f"Linhas removidas por NaN de lag (início de cada série): "
          f"{antes - len(df)} (mantidas: {len(df)})")

    return df


if __name__ == "__main__":
    df_features = build_feature_dataset()
    print(df_features.head(10))
    print(f"\nColunas finais: {list(df_features.columns)}")
