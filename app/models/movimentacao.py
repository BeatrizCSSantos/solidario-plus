
from app import db


class MovimentacaoEstoque(db.Model):
    __tablename__ = "movimentacoes_estoque"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=False
    )
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Numeric(10, 2), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)
    doacao_id = db.Column(
        db.Integer,
        db.ForeignKey("doacoes.id"),
        nullable=True
    )
    familia_id = db.Column(
        db.Integer,
        db.ForeignKey("familias_atendidas.id"),
        nullable=True
    )
    observacao = db.Column(db.String(250), nullable=True)

    produto = db.relationship("Produto", backref="movimentacoes")
    doacao = db.relationship("Doacao", backref="movimentacoes")
    familia = db.relationship(
        "FamiliaAtendida",
        backref="movimentacoes"
    )
