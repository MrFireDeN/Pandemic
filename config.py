import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # заменить в prod
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pandemic.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False