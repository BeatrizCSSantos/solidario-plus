
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func

from app import db
from app.models import Produto

products = Blueprint("products", __name__, url_prefix="/produtos")


@products.route("/")
def listar():
    produtos = Produto.query.order_by(Produto.nome.asc()).all()

    return render_template(
        "produtos/listar.html",
        produtos=produtos
    )


@products.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        unidade_medida = request.form.get(
            "unidade_medida", ""
        ).strip()

        if not nome or not unidade_medida:
            flash("Preencha o nome e a unidade de medida.", "erro")
            return render_template("produtos/novo.html")

        produto_existente = Produto.query.filter(
            func.lower(Produto.nome) == nome.lower()
        ).first()

        if produto_existente:
            flash("Já existe um produto com esse nome.", "erro")
            return render_template("produtos/novo.html")

        produto = Produto(
            nome=nome,
            unidade_medida=unidade_medida,
            ativo=True
        )

        db.session.add(produto)
        db.session.commit()

        flash("Produto cadastrado com sucesso!", "sucesso")
        return redirect(url_for("products.listar"))

    return render_template("produtos/novo.html")


@products.route("/<int:produto_id>/inativar", methods=["POST"])
def inativar(produto_id):
    produto = db.session.get(Produto, produto_id)

    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("products.listar"))

    if not produto.ativo:
        flash("Este produto já está inativo.", "erro")
        return redirect(url_for("products.listar"))

    produto.ativo = False
    db.session.commit()

    flash("Produto inativado com sucesso.", "sucesso")
    return redirect(url_for("products.listar"))
