from sqlalchemy import create_engine, Column, String, Integer, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
import enum, uuid, json

# Criando conexão com o banco de dados
engine = create_engine('mysql+pymysql://root:root@localhost:3306/entrega_serverless_db', echo=True, pool_pre_ping=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class StatusPedidoEnum(enum.Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    ENVIADO = "ENVIADO"
    CANCELADO = "CANCELADO"

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    total = Column(Float, nullable=False)
    status = Column(Enum(StatusPedidoEnum), nullable=False)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    data_atualizacao = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    itens = relationship("Item", back_populates="pedido", cascade="all, delete-orphan")
class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False)
    produto = Column(String(255), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco = Column(Float, nullable=False)
    
    pedido = relationship("Pedido", back_populates="itens")

# Criar as tabelas no banco de dados (DDL auto create)
Base.metadata.create_all(engine)

# Dados fictícios fornecidos no JSON
json_data = """
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "cliente": "João Silva",
    "email": "joao@email.com",
    "itens": [
        { "produto": "Café Expresso", "quantidade": 2, "preco": 5.00 },
        { "produto": "Pão de Queijo", "quantidade": 1, "preco": 3.50 }
    ],
    "total": 13.50,
    "status": "PENDENTE",
    "data_criacao": "2025-02-23T12:00:00Z",
    "data_atualizacao": "2025-02-23T12:00:00Z"
}
"""

# Converter JSON para dicionário
data = json.loads(json_data)

# Verificar se o pedido já existe no banco
existing_pedido = session.query(Pedido).filter_by(id=data["id"]).first()

if not existing_pedido:
    # Criando um novo pedido
    novo_pedido = Pedido(
        id=data["id"],
        cliente=data["cliente"],
        email=data["email"],
        total=data["total"],
        status=StatusPedidoEnum[data["status"]],
        data_criacao=datetime.fromisoformat(data["data_criacao"].replace("Z", "+00:00")),
        data_atualizacao=datetime.fromisoformat(data["data_atualizacao"].replace("Z", "+00:00"))
    )

    # Criando os itens do pedido
    for item in data["itens"]:
        novo_item = Item(
            produto=item["produto"],
            quantidade=item["quantidade"],
            preco=item["preco"],
            pedido=novo_pedido  # Relacionamento automático
        )
        session.add(novo_item)

    # Adiciona o pedido ao banco de dados
    session.add(novo_pedido)
    session.commit()
    print("Pedido e itens inseridos com sucesso!")

else:
    print("Pedido já existe no banco de dados.")

data = session.query(Pedido).all()
print(data)
print(data[0])


session.close()