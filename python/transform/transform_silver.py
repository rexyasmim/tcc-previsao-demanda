import os

from sqlalchemy import text

from python.utils.database import engine

SQL_FILE = "database/dml/transform_silver.sql"

def read_sql_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def execute_sql(sql):
    commands = sql.split(";")

    with engine.begin() as conn:
        for command in commands:
            command = command.strip()

            if command:
                conn.execute(text(command))


def main():
    print("=" * 60)
    print("INICIANDO TRANSFORMAÇÃO DA CAMADA SILVER")
    print("=" * 60)

    try:
        print(f"\n📄 Lendo {SQL_FILE}...")

        sql = read_sql_file(SQL_FILE)

        print("⬇️ Executando transformações...")

        execute_sql(sql)

        print("✅ Camada Silver atualizada com sucesso!")

    except Exception as e:
        print(f"❌ Erro durante a transformação: {e}")

    finally:
        print("\n" + "=" * 60)
        print("PROCESSO FINALIZADO")
        print("=" * 60)


if __name__ == "__main__":
    main()                