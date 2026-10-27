
import pytest

from app import create_app, db
from datetime import date
from decimal import Decimal

from app.models import Doacao, MovimentacaoEstoque, Produto, FamiliaAtendida


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_aplicacao_inicia(app):
    assert app is not None


def test_pagina_inicial_responde(client):
    resposta = client.get("/")
    assert resposta.status_code == 200


def test_cadastrar_produto(client, app):
    resposta = client.post(
        "/produtos/novo",
        data={
            "nome": "Arroz",
            "unidade_medida": "kg",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"cadastrado com sucesso" in resposta.data.lower()

    with app.app_context():
        produto = Produto.query.filter_by(nome="Arroz").first()
        assert produto is not None
        assert produto.unidade_medida == "kg"
        assert produto.ativo is True


def test_rejeitar_produto_duplicado(client, app):
    with app.app_context():
        db.session.add(
            Produto(nome="Arroz", unidade_medida="kg", ativo=True)
        )
        db.session.commit()

    resposta = client.post(
        "/produtos/novo",
        data={
            "nome": "arroz",
            "unidade_medida": "kg",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"ja existe um produto com esse nome" in (
        resposta.data.lower()
        .replace("á".encode(), b"a")
    )


def test_rejeitar_produto_sem_nome(client):
    resposta = client.post(
        "/produtos/novo",
        data={
            "nome": "",
            "unidade_medida": "kg",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"preencha o nome e a unidade de medida" in resposta.data.lower()


def test_cadastrar_doacao(client, app):
    with app.app_context():
        produto = Produto(nome="Feijão", unidade_medida="kg", ativo=True)
        db.session.add(produto)
        db.session.commit()
        produto_id = produto.id

    resposta = client.post(
        "/doacoes/nova",
        data={
            "produto_id": str(produto_id),
            "quantidade": "10",
            "data_doacao": date.today().isoformat(),
            "observacao": "Doação para teste",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200

    with app.app_context():
        doacao = Doacao.query.filter_by(produto_id=produto_id).first()
        assert doacao is not None
        assert doacao.quantidade == Decimal("10")

        movimentacao = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="entrada",
        ).first()

        assert movimentacao is not None
        assert movimentacao.quantidade == Decimal("10")


def test_rejeitar_doacao_com_quantidade_zero(client, app):
    with app.app_context():
        produto = Produto(nome="Arroz", unidade_medida="kg", ativo=True)
        db.session.add(produto)
        db.session.commit()
        produto_id = produto.id

    resposta = client.post(
        "/doacoes/nova",
        data={
            "produto_id": str(produto_id),
            "quantidade": "0",
            "data_doacao": date.today().isoformat(),
            "observacao": "",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"quantidade valida maior que zero" in (
        resposta.data.lower()
        .replace("á".encode(), b"a")
    )

    with app.app_context():
        assert Doacao.query.count() == 0
        assert MovimentacaoEstoque.query.count() == 0


def test_distribuir_produto_com_estoque_disponivel(client, app):
    with app.app_context():
        produto = Produto(nome="Arroz", unidade_medida="kg", ativo=True)
        familia = FamiliaAtendida(codigo="FAM-001", ativo=True)

        db.session.add_all([produto, familia])
        db.session.commit()

        produto_id = produto.id
        familia_id = familia.id

        entrada = MovimentacaoEstoque(
            produto_id=produto_id,
            tipo="entrada",
            quantidade=Decimal("10"),
            data_movimentacao=date.today(),
        )
        db.session.add(entrada)
        db.session.commit()

    resposta = client.post(
        "/distribuicoes/nova",
        data={
            "produto_id": str(produto_id),
            "familia_id": str(familia_id),
            "quantidade": "3",
            "data_movimentacao": date.today().isoformat(),
            "observacao": "Distribuição de teste",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200

    with app.app_context():
        saida = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="saida",
        ).first()

        assert saida is not None
        assert saida.quantidade == Decimal("3")


def test_rejeitar_distribuicao_acima_do_estoque(client, app):
    with app.app_context():
        produto = Produto(nome="Feijão", unidade_medida="kg", ativo=True)
        familia = FamiliaAtendida(codigo="FAM-002", ativo=True)

        db.session.add_all([produto, familia])
        db.session.commit()

        produto_id = produto.id
        familia_id = familia.id

        entrada = MovimentacaoEstoque(
            produto_id=produto_id,
            tipo="entrada",
            quantidade=Decimal("5"),
            data_movimentacao=date.today(),
        )
        db.session.add(entrada)
        db.session.commit()

    resposta = client.post(
        "/distribuicoes/nova",
        data={
            "produto_id": str(produto_id),
            "familia_id": str(familia_id),
            "quantidade": "8",
            "data_movimentacao": date.today().isoformat(),
            "observacao": "",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "estoque insuficiente" in resposta.data.decode("utf-8").lower()
    assert "saldo disponível: 5.00 kg" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        saidas = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="saida",
        ).count()

        assert saidas == 0


def test_rejeitar_distribuicao_para_familia_inativa(client, app):
    with app.app_context():
        produto = Produto(nome="Arroz", unidade_medida="kg", ativo=True)
        familia = FamiliaAtendida(codigo="FAM-003", ativo=False)

        db.session.add_all([produto, familia])
        db.session.commit()

        produto_id = produto.id
        familia_id = familia.id

        db.session.add(
            MovimentacaoEstoque(
                produto_id=produto_id,
                tipo="entrada",
                quantidade=Decimal("10"),
                data_movimentacao=date.today(),
            )
        )
        db.session.commit()

    resposta = client.post(
        "/distribuicoes/nova",
        data={
            "produto_id": str(produto_id),
            "familia_id": str(familia_id),
            "quantidade": "2",
            "data_movimentacao": date.today().isoformat(),
            "observacao": "",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "família ativa" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        saidas = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="saida",
        ).count()

        assert saidas == 0


def test_rejeitar_distribuicao_de_produto_inativo(client, app):
    with app.app_context():
        produto = Produto(nome="Feijão", unidade_medida="kg", ativo=False)
        familia = FamiliaAtendida(codigo="FAM-004", ativo=True)

        db.session.add_all([produto, familia])
        db.session.commit()

        produto_id = produto.id
        familia_id = familia.id

        db.session.add(
            MovimentacaoEstoque(
                produto_id=produto_id,
                tipo="entrada",
                quantidade=Decimal("10"),
                data_movimentacao=date.today(),
            )
        )
        db.session.commit()

    resposta = client.post(
        "/distribuicoes/nova",
        data={
            "produto_id": str(produto_id),
            "familia_id": str(familia_id),
            "quantidade": "2",
            "data_movimentacao": date.today().isoformat(),
            "observacao": "",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "produto ativo" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        saidas = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="saida",
        ).count()

        assert saidas == 0


def test_inativar_produto(client, app):
    with app.app_context():
        produto = Produto(nome="Açúcar", unidade_medida="kg", ativo=True)
        db.session.add(produto)
        db.session.commit()
        produto_id = produto.id

    resposta = client.post(
        f"/produtos/{produto_id}/inativar",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "inativado com sucesso" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        produto_atualizado = db.session.get(Produto, produto_id)

        assert produto_atualizado is not None
        assert produto_atualizado.ativo is False


def test_inativar_familia(client, app):
    with app.app_context():
        familia = FamiliaAtendida(codigo="FAM-005", ativo=True)
        db.session.add(familia)
        db.session.commit()
        familia_id = familia.id

    resposta = client.post(
        f"/familias/{familia_id}/inativar",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "inativada com sucesso" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        familia_atualizada = db.session.get(FamiliaAtendida, familia_id)

        assert familia_atualizada is not None
        assert familia_atualizada.ativo is False


def test_rejeitar_doacao_para_produto_inativo(client, app):
    with app.app_context():
        produto = Produto(nome="Macarrão", unidade_medida="kg", ativo=False)
        db.session.add(produto)
        db.session.commit()
        produto_id = produto.id

    resposta = client.post(
        "/doacoes/nova",
        data={
            "produto_id": str(produto_id),
            "quantidade": "5",
            "data_doacao": date.today().isoformat(),
            "observacao": "",
        },
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert "produto ativo" in resposta.data.decode("utf-8").lower()

    with app.app_context():
        doacoes = Doacao.query.filter_by(produto_id=produto_id).count()
        movimentacoes = MovimentacaoEstoque.query.filter_by(
            produto_id=produto_id,
            tipo="entrada",
        ).count()

        assert doacoes == 0
        assert movimentacoes == 0
