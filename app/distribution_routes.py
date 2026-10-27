
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Produto, FamiliaAtendida, MovimentacaoEstoque

distributions = Blueprint(
    "distributions",
    __name__,
    url_prefix="/distribuicoes",
)


def calcular_saldo(produto_id):
    entradas, saidas = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (MovimentacaoEstoque.tipo == "entrada",
                     MovimentacaoEstoque.quantidade),
                    else_=0,
                )
            ),
            0,
        ),
        func.coalesce(
            func.sum(
                case(
                    (MovimentacaoEstoque.tipo == "saida",
                     MovimentacaoEstoque.quantidade),
                    else_=0,
                )
            ),
            0,
        ),
    ).filter(
        MovimentacaoEstoque.produto_id == produto_id
    ).one()

    return Decimal(str(entradas)) - Decimal(str(saidas))


@distributions.route("/")
def listar():
    movimentacoes = (
        MovimentacaoEstoque.query
        .filter_by(tipo="saida")
        .order_by(
            MovimentacaoEstoque.data_movimentacao.desc(),
            MovimentacaoEstoque.id.desc(),
        )
        .all()
    )
    return render_template(
        "distribuicoes/listar.html",
        movimentacoes=movimentacoes,
    )


@distributions.route("/nova", methods=["GET", "POST"])
def nova():
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    familias = (
        FamiliaAtendida.query
        .filter_by(ativo=True)
        .order_by(FamiliaAtendida.codigo)
        .all()
    )

    if request.method == "POST":
        produto_id = request.form.get("produto_id", type=int)
        familia_id = request.form.get("familia_id", type=int)
        quantidade_texto = request.form.get("quantidade", "").strip()
        data_texto = request.form.get("data_movimentacao", "").strip()
        observacao = request.form.get("observacao", "").strip() or None

        produto = db.session.get(Produto, produto_id) if produto_id else None
        familia = (
            db.session.get(FamiliaAtendida, familia_id)
            if familia_id
            else None
        )

        if produto is None or not produto.ativo:
            flash("Selecione um produto ativo.", "erro")
            return render_template(
                "distribuicoes/nova.html",
                produtos=produtos,
                familias=familias,
            )

        if familia is None or not familia.ativo:
            flash("Selecione uma família ativa.", "erro")
            return render_template(
                "distribuicoes/nova.html",
                produtos=produtos,
                familias=familias,
            )

        try:
            quantidade = Decimal(quantidade_texto)
            if (
                not quantidade.is_finite()
                or quantidade <= 0
                or quantidade.as_tuple().exponent < -2
            ):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash(
                "Informe uma quantidade válida, maior que zero e com até duas casas decimais.",
                "erro",
            )
            return render_template(
                "distribuicoes/nova.html",
                produtos=produtos,
                familias=familias,
            )

        try:
            data_movimentacao = date.fromisoformat(data_texto)
        except ValueError:
            flash("Informe uma data válida.", "erro")
            return render_template(
                "distribuicoes/nova.html",
                produtos=produtos,
                familias=familias,
            )

        try:
            # Revalida o saldo dentro da transação.
            saldo = calcular_saldo(produto.id)

            if quantidade > saldo:
                flash(
                    f"Estoque insuficiente. Saldo disponível: {saldo} "
                    f"{produto.unidade_medida}.",
                    "erro",
                )
                return render_template(
                    "distribuicoes/nova.html",
                    produtos=produtos,
                    familias=familias,
                )

            movimentacao = MovimentacaoEstoque(
                produto_id=produto.id,
                tipo="saida",
                quantidade=quantidade,
                data_movimentacao=data_movimentacao,
                familia_id=familia.id,
                observacao=observacao,
            )
            db.session.add(movimentacao)
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            flash(
                "Não foi possível registrar a distribuição. Tente novamente.",
                "erro",
            )
            return render_template(
                "distribuicoes/nova.html",
                produtos=produtos,
                familias=familias,
            )

        flash("Distribuição registrada com sucesso!", "sucesso")
        return redirect(url_for("distributions.listar"))

    return render_template(
        "distribuicoes/nova.html",
        produtos=produtos,
        familias=familias,
    )
