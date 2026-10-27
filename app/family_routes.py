
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import FamiliaAtendida

families = Blueprint("families", __name__, url_prefix="/familias")


@families.route("/")
def listar():
    familias = FamiliaAtendida.query.order_by(
        FamiliaAtendida.codigo.asc()
    ).all()

    return render_template("familias/listar.html", familias=familias)


@families.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()

        if not codigo:
            flash("Informe o código da família.", "erro")
            return render_template("familias/nova.html")

        if len(codigo) > 20:
            flash("O código deve ter no máximo 20 caracteres.", "erro")
            return render_template("familias/nova.html")

        existente = FamiliaAtendida.query.filter(
            func.lower(FamiliaAtendida.codigo) == codigo.lower()
        ).first()

        if existente:
            flash("Já existe uma família com esse código.", "erro")
            return render_template("familias/nova.html")

        familia = FamiliaAtendida(codigo=codigo, ativo=True)

        try:
            db.session.add(familia)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Não foi possível cadastrar a família.", "erro")
            return render_template("familias/nova.html")

        flash("Família cadastrada com sucesso!", "sucesso")
        return redirect(url_for("families.listar"))

    return render_template("familias/nova.html")


@families.route("/<int:familia_id>/inativar", methods=["POST"])
def inativar(familia_id):
    familia = db.session.get(FamiliaAtendida, familia_id)

    if familia is None:
        flash("Família não encontrada.", "erro")
        return redirect(url_for("families.listar"))

    if not familia.ativo:
        flash("Esta família já está inativa.", "erro")
        return redirect(url_for("families.listar"))

    familia.ativo = False

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Não foi possível inativar a família.", "erro")
        return redirect(url_for("families.listar"))

    flash("Família inativada com sucesso.", "sucesso")
    return redirect(url_for("families.listar"))
