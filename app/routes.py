
from flask import Blueprint, render_template

from app.models import (
    Produto,
    Doacao,
    FamiliaAtendida,
    MovimentacaoEstoque,
)

main = Blueprint("main", __name__)


@main.route("/")
def index():
    total_produtos = Produto.query.filter_by(ativo=True).count()

    total_doacoes = Doacao.query.count()

    total_distribuicoes = MovimentacaoEstoque.query.filter_by(
        tipo="saida"
    ).count()

    total_familias = FamiliaAtendida.query.filter_by(
        ativo=True
    ).count()

    return render_template(
        "index.html",
        total_produtos=total_produtos,
        total_doacoes=total_doacoes,
        total_distribuicoes=total_distribuicoes,
        total_familias=total_familias,
    )
