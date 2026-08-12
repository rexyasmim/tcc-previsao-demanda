import pandas as pd
from python.utils.database import engine
import matplotlib.pyplot as plt


df = pd.read_sql(
    "SELECT * FROM gold.monthly_category_sales",
    engine
)

print(df.head())
print(df.info())
print(df.describe())




df["date"] = pd.to_datetime(
    df["year"].astype(str) + "-" +
    df["month"].astype(str) + "-01"
)


monthly_demand = (
    df.groupby("date")["demand"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(12, 5))

plt.plot(
    monthly_demand["date"],
    monthly_demand["demand"]
)

plt.title("Demanda mensal total")
plt.xlabel("Mês")
plt.ylabel("Demanda")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()





nov_2017 = df[
    (df["year"] == 2017) &
    (df["month"] == 11)
]

print(
    nov_2017
    .sort_values("demand", ascending=False)
    [["product_category_name", "demand"]]
    .head(10)
)



'''Distribuição da demanda'''

plt.figure(figsize=(10, 5))

plt.hist(df["demand"], bins=50)

plt.title("Distribuição da demanda")
plt.xlabel("Demanda")
plt.ylabel("Frequência")

plt.tight_layout()
plt.show()



plt.figure(figsize=(10, 4))

plt.boxplot(df["demand"], vert=False)

plt.title("Distribuição da demanda")
plt.xlabel("Demanda")

plt.tight_layout()
plt.show()

'''Top categorias'''
category_demand = (
    df.groupby("product_category_name")["demand"]
    .sum()
    .sort_values(ascending=False)
)

print(category_demand.head(10))



top10 = category_demand.head(10)

plt.figure(figsize=(10, 6))

top10.sort_values().plot(kind="barh")

plt.title("Top 10 categorias por demanda")
plt.xlabel("Demanda")
plt.ylabel("Categoria")

plt.tight_layout()
plt.show()


'''ETAPA 5 — Demanda zero'''
total_rows = len(df)

zero_demand = (df["demand"] == 0).sum()

zero_percentage = zero_demand / total_rows * 100

print(f"Total de observações: {total_rows}")
print(f"Observações com demanda zero: {zero_demand}")
print(f"Percentual com demanda zero: {zero_percentage:.2f}%")


'''ETAPA 6 — Sazonalidade'''
monthly_seasonality = (
    df.groupby("month")["demand"]
    .mean()
)

print(monthly_seasonality)



'''Análise por categoria ao longo do tempo'''

top5 = category_demand.head(5).index

top5_df = df[
    df["product_category_name"].isin(top5)
]

pivot_top5 = top5_df.pivot(
    index="date",
    columns="product_category_name",
    values="demand"
)


plt.figure(figsize=(12, 6))

for category in pivot_top5.columns:
    plt.plot(
        pivot_top5.index,
        pivot_top5[category],
        label=category
    )

plt.title("Demanda das principais categorias ao longo do tempo")
plt.xlabel("Mês")
plt.ylabel("Demanda")

plt.legend()
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()