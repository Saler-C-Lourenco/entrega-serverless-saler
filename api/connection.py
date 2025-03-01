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

    def to_dict(self):
        """ Converte um objeto Pedido para dicionário JSON """
        return {
            "id": self.id,
            "cliente": self.cliente,
            "email": self.email,
            "total": self.total,
            "status": self.status.value,
            "data_criacao": self.data_criacao.isoformat(),
            "data_atualizacao": self.data_atualizacao.isoformat(),
            "itens": [item.to_dict() for item in self.itens]
        }

class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False)
    produto = Column(String(255), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco = Column(Float, nullable=False)
    
    pedido = relationship("Pedido", back_populates="itens")

    def to_dict(self):
        """ Converte um objeto Item para dicionário JSON """
        return {
            "id": self.id,
            "produto": self.produto,
            "quantidade": self.quantidade,
            "preco": self.preco
        }

# Criar as tabelas no banco de dados (DDL auto create)
Base.metadata.create_all(engine)

def listAll():
    """ Retorna todos os pedidos no formato JSON """
    pedidos = session.query(Pedido).all()
    pedidos_json = json.dumps([pedido.to_dict() for pedido in pedidos], indent=4, ensure_ascii=False)
    return pedidos_json

# Executar listAll e exibir o resultado
print(listAll())

# Fechar a sessão
session.close()
