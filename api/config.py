DB_USER = "root"  # Define o nome de usuário do banco de dados MySQL.
DB_PASSWORD = "root"  # Define a senha do banco de dados MySQL.
DB_NAME = "entrega_serverless_db"  # Nome do banco de dados utilizado pela aplicação.
INSTANCE_CONNECTION_NAME = "green-alchemy-452419-i5:southamerica-east1:root"  
# Identificador da instância do Cloud SQL na GCP, usado para conexões seguras via Unix socket.

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@35.198.52.88:3306/{DB_NAME}"
)
# Define a URI de conexão com o banco de dados MySQL, utilizando o driver 'pymysql'.
# Substitui as credenciais e informações do banco na string de conexão.

SQLALCHEMY_TRACK_MODIFICATIONS = False  
# Desativa o recurso de rastreamento de modificações do SQLAlchemy para melhorar a performance.
