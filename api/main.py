# Importações necessárias para a API
from flask import Flask, request, jsonify  # Flask para criar a API, request para capturar dados das requisições e jsonify para formatar respostas JSON
from sqlalchemy import create_engine, Column, String, Integer, Float, Enum, ForeignKey, DateTime  # SQLAlchemy para modelagem e manipulação do banco de dados
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload  # ORM do SQLAlchemy para definir modelos e gerenciar sessões
from datetime import datetime, timezone  # Trabalhar com datas e fusos horários
import enum, uuid  # Enum para status do pedido e uuid para gerar identificadores únicos

# Importa a URI de conexão do banco de dados definida no arquivo de configuração
from config import SQLALCHEMY_DATABASE_URI  

# Configuração do Flask
app = Flask(__name__)

# Criando conexão com o banco de dados usando SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_pre_ping=True)  
# `echo=True` exibe as queries SQL no console para debug
# `pool_pre_ping=True` ajuda a evitar erros de conexão inativa

# Criando a base para os modelos do SQLAlchemy
Base = declarative_base()

# Criando uma fábrica de sessões para interação com o banco de dados
Session = sessionmaker(bind=engine)

# ENTIDADES

# Enum para representar os possíveis status de um pedido
class StatusPedidoEnum(enum.Enum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    ENVIADO = "ENVIADO"
    CANCELADO = "CANCELADO"

# Modelo da entidade Pedido
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Identificador único gerado automaticamente
    cliente = Column(String(255), nullable=False)  # Nome do cliente
    email = Column(String(255), nullable=False)  # E-mail do cliente
    total = Column(Float, nullable=False)  # Valor total do pedido
    status = Column(Enum(StatusPedidoEnum), nullable=False)  # Status do pedido, baseado no enum definido
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # Data de criação do pedido
    data_atualizacao = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)  # Data de última atualização
    
    itens = relationship("Item", back_populates="pedido", cascade="all, delete-orphan")  # Relacionamento com os itens do pedido

    # Método para converter um pedido em um dicionário (JSON)
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

# Modelo da entidade Item (produtos dentro de um pedido)
class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Identificador único do item
    pedido_id = Column(String(36), ForeignKey("pedidos.id"), nullable=False)  # Chave estrangeira referenciando um pedido
    produto = Column(String(255), nullable=False)  # Nome do produto
    quantidade = Column(Integer, nullable=False)  # Quantidade do produto
    preco = Column(Float, nullable=False)  # Preço unitário do produto
    
    pedido = relationship("Pedido", back_populates="itens")  # Relacionamento reverso com a tabela Pedido

    # Método para converter um item em um dicionário (JSON)
    def to_dict(self):
        return {
            "id": self.id,
            "produto": self.produto,
            "quantidade": self.quantidade,
            "preco": self.preco
        }

# Criar as tabelas no banco de dados com base nos modelos definidos
Base.metadata.create_all(engine)

# ROTAS FLASK (API REST)

@app.route('/')
def hello_world():
    """ Rota raiz da API, usada para verificar se está funcionando """
    return 'Hello, Cloud Functions!'

@app.route('/pedidos', methods=['GET'])
def listAll():
    """ Retorna todos os pedidos cadastrados no banco """
    session = Session()
    pedidos = session.query(Pedido).options(joinedload(Pedido.itens)).all()  # Busca todos os pedidos e seus itens relacionados
    session.close()
    return jsonify([pedido.to_dict() for pedido in pedidos])  # Retorna a lista de pedidos como JSON

@app.route('/pedidos/<string:pedido_id>', methods=['GET'])
def findById(pedido_id):
    """ Busca um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).options(joinedload(Pedido.itens)).first()  # Busca o pedido pelo ID
    session.close()
    if pedido:
        return jsonify(pedido.to_dict())  # Retorna o pedido se encontrado
    return jsonify({"message": "Pedido não encontrado"}), 404  # Retorna erro 404 se não encontrado

@app.route('/pedidos', methods=['POST'])
def save():
    """ Cria e salva um novo pedido no banco de dados """
    session = Session()
    pedido_data = request.json  # Captura os dados enviados na requisição

    try:
        # Criando um novo pedido
        pedido = Pedido(
            id=pedido_data.get("id", str(uuid.uuid4())),
            cliente=pedido_data["cliente"],
            email=pedido_data["email"],
            total=pedido_data["total"],
            status=StatusPedidoEnum[pedido_data["status"]],
            data_criacao=datetime.fromisoformat(pedido_data["data_criacao"]),
            data_atualizacao=datetime.fromisoformat(pedido_data["data_atualizacao"])
        )

        # Criando os itens associados ao pedido
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
    """ Atualiza o status de um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()  # Busca o pedido pelo ID
    
    if not pedido:
        session.close()
        return jsonify({"message": "Pedido não encontrado"}), 404

    update_data = request.json
    if "status" not in update_data:
        session.close()
        return jsonify({"message": "Campo 'status' é obrigatório"}), 400

    try:
        pedido.status = StatusPedidoEnum[update_data["status"]]  # Atualiza o status do pedido
    except KeyError:
        session.close()
        return jsonify({"message": "Status inválido"}), 400

    pedido.data_atualizacao = datetime.now(timezone.utc)  # Atualiza a data de modificação

    session.commit()
    status_atualizado = pedido.status.name  # Captura o status antes de fechar a sessão

    session.close()
    return jsonify({"message": "Pedido atualizado com sucesso", "status": status_atualizado}), 200

@app.route('/pedidos/<string:pedido_id>', methods=['DELETE'])
def delete(pedido_id):
    """ Remove um pedido pelo ID """
    session = Session()
    pedido = session.query(Pedido).filter_by(id=pedido_id).first()
    if not pedido:
        session.close()
        return jsonify({"message": "Pedido não encontrado"}), 404

    session.delete(pedido)
    session.commit()
    session.close()
    return jsonify({"message": "Pedido deletado com sucesso!"})

# Inicia o servidor Flask quando executado localmente
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

# Função de entrada para o Google Cloud Functions
def flask_function(request):
    """ Ponto de entrada para rodar a API no Cloud Functions """
    with app.request_context(request.environ):
        return app.full_dispatch_request()
