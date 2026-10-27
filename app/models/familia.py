
from app import db


class FamiliaAtendida(db.Model):
    __tablename__ = "familias_atendidas"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<FamiliaAtendida {self.codigo}>"
