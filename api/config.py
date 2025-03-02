import os

DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "entrega_serverless_db"
INSTANCE_CONNECTION_NAME = "green-alchemy-452419-i5:southamerica-east1:root"

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@35.198.52.88:3306/{DB_NAME}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
