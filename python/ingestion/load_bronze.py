import os

import pandas as pd

from sqlalchemy import text

from python.utils.database import engine

DATA_PATH = "data/raw"

FILES = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_products_dataset.csv": "products",
    "product_category_name_translation.csv": "product_category_name_translation"
}

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df


def load_dataframe(df, table_name):
    df.to_sql(name=table_name,
              schema="bronze",
              con=engine,
              if_exists="append",
              index=False,
              method="multi",
              chunksize=1000
    )


def main():
    print("=" * 60)
    print("INICIANDO CARGA DA CAMADA BRONZE")
    print("=" * 60)

    for file_name, table_name in FILES.items():

        try:
            file_path = os.path.join(DATA_PATH, file_name)

            print(f"\n📄 Lendo {file_name}...")

            df = read_csv(file_path)

            print(f"✅ {len(df):,} registros encontrados.")

            print(f"⬇️ Inserindo em bronze.{table_name}...")

            load_dataframe(df, table_name)

            print("✅ Carga concluída.")

        except Exception as e:
            print(f"❌ Erro ao carregar {file_name}:")
            print(e)

    print("\n" + "=" * 60)
    print("🎉 CAMADA BRONZE CARREGADA!")
    print("=" * 60)


if __name__ == "__main__":
    main()