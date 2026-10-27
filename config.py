import os


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "chave-temporaria-apenas-para-desenvolvimento"
    )

    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://",
                "postgresql+psycopg://",
                1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///solidario.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
