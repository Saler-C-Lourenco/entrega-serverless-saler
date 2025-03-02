from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Integer, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
from datetime import datetime, timezone
import enum, uuid


# Configuração do Flask
app = Flask(__name__)

# Criando conexão com o banco de dados
engine = create_engine('mysql+pymysql://root:root@localhost:3306/entrega_serverless_db', echo=True, pool_pre_ping=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

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
        return {
            "id": self.id,
            "produto": self.produto,
            "quantidade": self.quantidade,
            "preco": self.preco
        }

# Criar tabelas
Base.metadata.create_all(engine)

# ROTAS FLASK (API REST)

@app.route('/pedidos', methods=['GET'])
def listAll():
    """ Retorna todos os pedidos """
    session = Session()
    pedidos = session.query(Pedido).options(joinedload(Pedido.itens)).all()
    session.close()
    return jsonify([pedido.to_dict() for pedido in pedidos])

@app.route('/pedidos/<string:pedido_id>', methods=['GET'])
def findById(pedido_id):
    """ Busca um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).options(joinedload(Pedido.itens)).first()
    session.close()
    if pedido:
        return jsonify(pedido.to_dict())
    return jsonify({"message": "Pedido não encontrado"}), 404

@app.route('/pedidos', methods=['POST'])
def save():
    """ Salva um novo pedido """
    session = Session()
    pedido_data = request.json
    
    try:
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
        session.close()
        return jsonify({"message": "Pedido salvo com sucesso!"}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"message": "Erro ao salvar pedido", "error": str(e)}), 500
@app.route('/pedidos/<string:pedido_id>', methods=['PATCH'])
def update_status(pedido_id):
    """ Atualiza apenas o status de um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    
    if not pedido:
        session.close()
        return jsonify({"message": "Pedido não encontrado"}), 404

    update_data = request.json
    if "status" not in update_data:
        session.close()
        return jsonify({"message": "Campo 'status' é obrigatório"}), 400

    try:
        pedido.status = StatusPedidoEnum[update_data["status"]]
    except KeyError:
        session.close()
        return jsonify({"message": "Status inválido"}), 400

    pedido.data_atualizacao = datetime.now(timezone.utc)

    session.commit()

    # Captura o status antes de fechar a sessão para evitar erro de DetachedInstance
    status_atualizado = pedido.status.name

    session.close()

    return jsonify({"message": "Pedido atualizado com sucesso", "status": status_atualizado}), 200

@app.route('/pedidos/<string:pedido_id>', methods=['DELETE'])
def delete(pedido_id):
    """ Deleta um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        session.close()
        return jsonify({"message": "Pedido não encontrado"}), 404

    session.delete(pedido)
    session.commit()
    session.close()
    return jsonify({"message": "Pedido deletado com sucesso!"})

# Iniciar o servidor
if __name__ == '__main__':
    app.run(debug=True)
