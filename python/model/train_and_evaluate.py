"""
Treino e avaliação comparativa de modelos de previsão de demanda.

Modelos comparados:
- Regressão Linear (baseline)
- Random Forest Regressor
- Gradient Boosting Regressor

Estratégia:
- Split temporal (não aleatório): últimos 3 meses = teste,
  restante = treino. Nunca embaralhar dados de série temporal.
- Encoding: One-Hot para product_category_name, ajustado (fit)
  somente no treino, para evitar vazamento de dado.
- Métricas: MAE, RMSE e WAPE (WAPE no lugar de MAPE, pois ~28%
  das observações têm demanda real = 0, o que quebra MAPE).
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from python.model.build_features import TEST_MONTHS, build_feature_dataset

FEATURE_COLUMNS_NUMERIC = [
    "year",
    "month_sin",
    "month_cos",
    "is_black_friday_month",
    "demand_lag_1",
    "demand_lag_2",
    "rolling_mean_3",
]
FEATURE_COLUMN_CATEGORICAL = "product_category_name"
TARGET_COLUMN = "demand"


def wape(y_true, y_pred):
    """
    Weighted Absolute Percentage Error.
    Diferente do MAPE, não quebra quando y_true = 0, pois divide a
    soma dos erros pela soma da demanda real (não linha a linha).
    """
    return np.sum(np.abs(y_true - y_pred)) / np.sum(y_true) * 100


def temporal_train_test_split(df, test_months=TEST_MONTHS):
    """Separa treino/teste pelos últimos N meses, respeitando a ordem temporal."""
    meses_distintos = sorted(df["date"].unique())
    corte = meses_distintos[-test_months]

    train = df[df["date"] < corte].copy()
    test = df[df["date"] >= corte].copy()

    print(f"Treino: {train['date'].min().date()} até {train['date'].max().date()} "
          f"({len(train)} linhas)")
    print(f"Teste:  {test['date'].min().date()} até {test['date'].max().date()} "
          f"({len(test)} linhas)")

    return train, test


def build_preprocessor():
    """One-Hot para categoria, passthrough para as numéricas."""
    return ColumnTransformer(
        transformers=[
            ("category", OneHotEncoder(handle_unknown="ignore"), [FEATURE_COLUMN_CATEGORICAL]),
            ("numeric", "passthrough", FEATURE_COLUMNS_NUMERIC),
        ]
    )


def get_models():
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
    }


def evaluate_model(name, pipeline, X_test, y_test, test_data):
    y_pred = pipeline.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)  # demanda nunca é negativa

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    wape_score = wape(y_test.values, y_pred)

    print(f"\n{name}")
    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  WAPE: {wape_score:.2f}%")

    previsoes = test_data[
        ["date", FEATURE_COLUMN_CATEGORICAL]
    ].copy()

    previsoes["demanda_real"] = y_test.values
    previsoes["demanda_prevista"] = y_pred
    previsoes["erro"] = (
        previsoes["demanda_real"] - previsoes["demanda_prevista"]
    )
    previsoes["erro_absoluto"] = np.abs(previsoes["erro"])

    return {
        "modelo": name,
        "MAE": mae,
        "RMSE": rmse,
        "WAPE": wape_score,
        "previsoes": previsoes
    }


def run_experiment(apply_pareto, label):
    print("\n" + "#" * 60)
    print(f"CENÁRIO: {label}")
    print("#" * 60)

    df = build_feature_dataset(apply_pareto=apply_pareto)
    train, test = temporal_train_test_split(df)

    feature_cols = [FEATURE_COLUMN_CATEGORICAL] + FEATURE_COLUMNS_NUMERIC
    X_train, y_train = train[feature_cols], train[TARGET_COLUMN]
    X_test, y_test = test[feature_cols], test[TARGET_COLUMN]

    preprocessor = build_preprocessor()
    resultados = []

    print("\n" + "=" * 60)
    print("TREINANDO E AVALIANDO MODELOS")
    print("=" * 60)

    for nome, modelo in get_models().items():
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("modelo", modelo),
        ])

        pipeline.fit(X_train, y_train)

        resultado = evaluate_model(
            nome,
            pipeline,
            X_test,
            y_test,
            test
        )

        previsoes = resultado.pop("previsoes")

        resultado["cenario"] = label
        resultado["n_treino"] = len(train)
        resultado["n_teste"] = len(test)

        resultados.append(resultado)

        previsoes["cenario"] = label
        previsoes["modelo"] = nome

        previsoes.to_csv(
            f"docs/previsoes_"
            f"{'pareto' if apply_pareto else 'sem_pareto'}_"
            f"{nome.lower().replace(' ', '_')}.csv",
            index=False
        )

    return resultados


def main():
    todos_resultados = []
    todos_resultados += run_experiment(apply_pareto=False, label="Sem Pareto (74 categorias)")
    todos_resultados += run_experiment(apply_pareto=True, label="Com Pareto (categorias + 'outras')")

    print("\n" + "=" * 60)
    print("RESUMO COMPARATIVO — AMBOS OS CENÁRIOS")
    print("=" * 60)
    df_resultados = pd.DataFrame(todos_resultados)[
        ["cenario", "modelo", "n_treino", "n_teste", "MAE", "RMSE", "WAPE"]
    ]
    print(df_resultados.to_string(index=False))

    df_resultados.to_csv("docs/resultados_comparativo_modelos.csv", index=False)
    print("\nResultado salvo em docs/resultados_comparativo_modelos.csv")


if __name__ == "__main__":
    main()
