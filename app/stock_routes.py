
from flask import Blueprint, render_template
from sqlalchemy import case, func

from app import db
from app.models import Produto, MovimentacaoEstoque

stock = Blueprint("stock", __name__, url_prefix="/estoque")


@stock.route("/")
def listar():
    entradas = func.coalesce(
        func.sum(
            case(
                (MovimentacaoEstoque.tipo == "entrada",
                 MovimentacaoEstoque.quantidade),
                else_=0,
            )
        ),
        0,
    )

    saidas = func.coalesce(
        func.sum(
            case(
                (MovimentacaoEstoque.tipo == "saida",
                 MovimentacaoEstoque.quantidade),
                else_=0,
            )
        ),
        0,
    )

    saldo = entradas - saidas

    produtos = (
        db.session.query(
            Produto,
            entradas.label("entradas"),
            saidas.label("saidas"),
            saldo.label("saldo"),
        )
        .outerjoin(
            MovimentacaoEstoque,
            MovimentacaoEstoque.produto_id == Produto.id,
        )
        .group_by(Produto.id)
        .order_by(Produto.nome.asc())
        .all()
    )

    return render_template("estoque/listar.html", produtos=produtos)
