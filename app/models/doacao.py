
from app import db


class Doacao(db.Model):
    __tablename__ = "doacoes"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=False
    )
    quantidade = db.Column(db.Numeric(10, 2), nullable=False)
    data_doacao = db.Column(db.Date, nullable=False)
    observacao = db.Column(db.String(250), nullable=True)

    produto = db.relationship("Produto", backref="doacoes")
