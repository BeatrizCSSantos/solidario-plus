import os


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "chave-temporaria-apenas-para-desenvolvimento"
    )

    SQLALCHEMY_DATABASE_URI = "sqlite:///solidario.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False