
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Produto, Doacao, MovimentacaoEstoque

donations = Blueprint("donations", __name__, url_prefix="/doacoes")


@donations.route("/")
def listar():
    doacoes = Doacao.query.order_by(Doacao.data_doacao.desc(), Doacao.id.desc()).all()
    return render_template("doacoes/listar.html", doacoes=doacoes)


@donations.route("/nova", methods=["GET", "POST"])
def nova():
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome.asc()).all()

    if request.method == "POST":
        produto_id = request.form.get("produto_id", type=int)
        quantidade_texto = request.form.get("quantidade", "").strip()
        data_texto = request.form.get("data_doacao", "").strip()
        observacao = request.form.get("observacao", "").strip() or None

        produto = db.session.get(Produto, produto_id) if produto_id else None

        if produto is None or not produto.ativo:
            flash("Selecione um produto ativo.", "erro")
            return render_template("doacoes/nova.html", produtos=produtos)

        try:
            quantidade = Decimal(quantidade_texto)
            if not quantidade.is_finite() or quantidade <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            flash("Informe uma quantidade válida maior que zero.", "erro")
            return render_template("doacoes/nova.html", produtos=produtos)

        try:
            data_doacao = date.fromisoformat(data_texto)
        except ValueError:
            flash("Informe uma data válida.", "erro")
            return render_template("doacoes/nova.html", produtos=produtos)

        doacao = Doacao(
            produto_id=produto.id,
            quantidade=quantidade,
            data_doacao=data_doacao,
            observacao=observacao,
        )

        movimentacao = MovimentacaoEstoque(
            produto_id=produto.id,
            tipo="entrada",
            quantidade=quantidade,
            data_movimentacao=data_doacao,
            observacao=f"Doação #{doacao.id}" if doacao.id else observacao,
            doacao=doacao,
        )

        try:
            db.session.add(doacao)
            db.session.add(movimentacao)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível registrar a doação. Tente novamente.", "erro")
            return render_template("doacoes/nova.html", produtos=produtos)

        flash("Doação registrada com sucesso!", "sucesso")
        return redirect(url_for("donations.listar"))

    return render_template("doacoes/nova.html", produtos=produtos)
