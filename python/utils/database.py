from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

# Lê as variáveis de ambiente
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# String de conexão
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Cria a engine do SQLAlchemy
engine = create_engine(DATABASE_URL)


def test_connection():
    """
    Testa a conexão com o PostgreSQL.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Conectado ao PostgreSQL com sucesso!")
    except Exception as e:
        print("❌ Erro ao conectar ao PostgreSQL:")
        print(e)


if __name__ == "__main__":
    test_connection()