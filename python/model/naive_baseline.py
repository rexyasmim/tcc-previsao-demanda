import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error

from python.model.build_features import TEST_MONTHS, build_feature_dataset


TARGET_COLUMN = "demand"


def wape(y_true, y_pred):
    """
    Weighted Absolute Percentage Error.
    """
    return np.sum(np.abs(y_true - y_pred)) / np.sum(y_true) * 100


def temporal_train_test_split(df, test_months=TEST_MONTHS):
    """
    Separa os últimos N meses para teste.
    """
    meses_distintos = sorted(df["date"].unique())
    corte = meses_distintos[-test_months]

    train = df[df["date"] < corte].copy()
    test = df[df["date"] >= corte].copy()

    print(
        f"Treino: {train['date'].min().date()} até "
        f"{train['date'].max().date()} ({len(train)} linhas)"
    )

    print(
        f"Teste:  {test['date'].min().date()} até "
        f"{test['date'].max().date()} ({len(test)} linhas)"
    )

    return train, test


def run_baseline(apply_pareto, label):
    print("\n" + "#" * 60)
    print(f"CENÁRIO: {label}")
    print("#" * 60)

    df = build_feature_dataset(apply_pareto=apply_pareto)

    train, test = temporal_train_test_split(df)

    # Naive: previsão = demanda do mês anterior
    y_test = test[TARGET_COLUMN]
    y_pred = test["demand_lag_1"]

    # Garantia de valores não negativos
    y_pred = np.clip(y_pred, 0, None)

    mae = mean_absolute_error(y_test, y_pred)

    rmse = np.sqrt(
        mean_squared_error(y_test, y_pred)
    )

    wape_score = wape(
        y_test.values,
        y_pred.values
    )

    print("\nNaive Baseline (Lag-1)")
    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  WAPE: {wape_score:.2f}%")

    # Salvar previsões
    previsoes = test[
        ["date", "product_category_name"]
    ].copy()

    previsoes["demanda_real"] = y_test.values
    previsoes["demanda_prevista"] = y_pred.values

    previsoes["erro"] = (
        previsoes["demanda_real"]
        - previsoes["demanda_prevista"]
    )

    previsoes["erro_absoluto"] = np.abs(
        previsoes["erro"]
    )

    caminho = (
        "docs/previsoes_pareto_naive.csv"
        if apply_pareto
        else "docs/previsoes_sem_pareto_naive.csv"
    )

    previsoes.to_csv(caminho, index=False)

    print(f"\nPrevisões salvas em: {caminho}")

    return {
        "cenario": label,
        "modelo": "Naive Lag-1",
        "n_treino": len(train),
        "n_teste": len(test),
        "MAE": mae,
        "RMSE": rmse,
        "WAPE": wape_score,
    }


def main():

    todos_resultados = []

    todos_resultados.append(
        run_baseline(
            apply_pareto=False,
            label="Sem Pareto (74 categorias)"
        )
    )

    todos_resultados.append(
        run_baseline(
            apply_pareto=True,
            label="Com Pareto (categorias + 'outras')"
        )
    )

    print("\n" + "=" * 60)
    print("RESUMO COMPARATIVO — NAIVE BASELINE")
    print("=" * 60)

    df_resultados = pd.DataFrame(todos_resultados)

    print(
        df_resultados.to_string(index=False)
    )

    df_resultados.to_csv(
        "docs/resultados_naive_baseline.csv",
        index=False
    )

    print(
        "\nResultado salvo em "
        "docs/resultados_naive_baseline.csv"
    )


if __name__ == "__main__":
    main()