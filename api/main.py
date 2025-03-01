from sqlalchemy import create_engine, Column, String, Integer, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
import enum, uuid, json

# Criando conexão com o banco de dados
engine = create_engine('mysql+pymysql://root:root@localhost:3306/entrega_serverless_db', echo=True, pool_pre_ping=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# ENTIDADES

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

# REPOSITORIES  

def listAll():
    """ Retorna todos os pedidos no formato JSON """
    pedidos = session.query(Pedido).all()
    return json.dumps([pedido.to_dict() for pedido in pedidos], indent=4, ensure_ascii=False)

def findById(pedido_id):
    """ Busca um pedido pelo ID e retorna no formato JSON """
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    if pedido:
        return json.dumps(pedido.to_dict(), indent=4, ensure_ascii=False)
    return json.dumps({"message": "Pedido não encontrado"}, indent=4)

def save(pedido_data):
    """ Salva um novo pedido no banco de dados """
    pedido = Pedido(
        id=pedido_data.get("id", str(uuid.uuid4())),
        cliente=pedido_data["cliente"],
        email=pedido_data["email"],
        total=pedido_data["total"],
        status=StatusPedidoEnum[pedido_data["status"]],
        data_criacao=datetime.fromisoformat(pedido_data["data_criacao"]),
        data_atualizacao=datetime.fromisoformat(pedido_data["data_atualizacao"])
    )
    
    for item_data in pedido_data["itens"]:
        item = Item(
            produto=item_data["produto"],
            quantidade=item_data["quantidade"],
            preco=item_data["preco"]
        )
        pedido.itens.append(item)

    session.add(pedido)
    session.commit()
    return json.dumps({"message": "Pedido salvo com sucesso!"}, indent=4)

def update(pedido_id, update_data):
    """ Atualiza um pedido pelo ID """
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        return json.dumps({"message": "Pedido não encontrado"}, indent=4)

    if "cliente" in update_data:
        pedido.cliente = update_data["cliente"]
    if "email" in update_data:
        pedido.email = update_data["email"]
    if "total" in update_data:
        pedido.total = update_data["total"]
    if "status" in update_data:
        pedido.status = StatusPedidoEnum[update_data["status"]]

    pedido.data_atualizacao = datetime.now(timezone.utc)

    session.commit()
    return json.dumps({"message": "Pedido atualizado com sucesso!"}, indent=4)

def delete(pedido_id):
    """ Deleta um pedido pelo ID """
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        return json.dumps({"message": "Pedido não encontrado"}, indent=4)

    session.delete(pedido)
    session.commit()
    return json.dumps({"message": "Pedido deletado com sucesso!"}, indent=4)

# Exemplo de chamada
if __name__ == "__main__":
    print(listAll())  # Lista todos os pedidos

    novo_pedido = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "cliente": "João Silva",
        "email": "joao@email.com",
        "total": 13.50,
        "status": "PENDENTE",
        "data_criacao": "2025-02-23T12:00:00+00:00",
        "data_atualizacao": "2025-02-23T12:00:00+00:00",
        "itens": [
            {"produto": "Café Expresso", "quantidade": 2, "preco": 5.00},
            {"produto": "Pão de Queijo", "quantidade": 1, "preco": 3.50}
        ]
    }

    print(save(novo_pedido))  # Salva um novo pedido
    print(findById("123e4567-e89b-12d3-a456-426614174000"))  # Busca pelo ID
    print(update("123e4567-e89b-12d3-a456-426614174000", {"status": "ENVIADO"}))  # Atualiza
    print(delete("123e4567-e89b-12d3-a456-426614174000"))  # Deleta

# Fechar a sessão
session.close()