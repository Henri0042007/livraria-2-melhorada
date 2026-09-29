from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from core.models import Compra, Editora, ItensCompra, Livro, User
from core.serializers.compra import (
    CompraCreateUpdateSerializer,
    CompraSerializer,
    ItensCompraCreateUpdateSerializer,
    ItensCompraSerializer,
)


class ItensCompraSerializerTests(TestCase):
    def test_serializer_exposes_livro_data(self):
        user = User.objects.create_user(email='user@example.com', password='secret')
        editora = Editora.objects.create(nome='Editora Teste')
        livro = Livro.objects.create(
            titulo='Livro Teste',
            preco=Decimal('39.90'),
            editora=editora,
        )
        compra = Compra.objects.create(usuario=user)
        item = ItensCompra.objects.create(compra=compra, livro=livro, quantidade=2, preco=livro.preco)

        data = ItensCompraSerializer(item).data

        assert data['titulo'] == 'Livro Teste'
        assert data['editora'] == 'Editora Teste'
        assert str(data['preco']) == '39.90'
        assert str(data['total']) == '79.80'


class CompraSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='buyer@example.com', password='secret')
        self.livro = Livro.objects.create(
            titulo='Livro Histórico',
            preco=Decimal('39.90'),
            quantidade=5,
        )
        self.factory = APIRequestFactory()

    def test_create_uses_authenticated_user_and_preserves_price(self):
        request = self.factory.post('/api/compras/')
        request.user = self.user
        serializer = CompraCreateUpdateSerializer(
            data={'itens': [{'livro': self.livro.pk, 'quantidade': 2}]},
            context={'request': request},
        )

        assert serializer.is_valid(), serializer.errors
        compra = serializer.save()

        self.livro.preco = Decimal('59.90')
        self.livro.save(update_fields=['preco'])
        data = CompraSerializer(compra).data

        assert compra.usuario == self.user
        assert str(data['itens'][0]['preco']) == '39.90'
        assert str(data['total']) == '79.80'
        assert data['tipo_pagamento'] == 'Cartão de Crédito'
        assert data['data_criacao']
        assert data['data_atualizacao']

    def test_item_quantity_must_be_positive(self):
        serializer = ItensCompraCreateUpdateSerializer(
            data={'livro': self.livro.pk, 'quantidade': 0},
        )

        assert not serializer.is_valid()
        assert 'quantidade' in serializer.errors

    def test_item_quantity_cannot_exceed_stock(self):
        serializer = ItensCompraCreateUpdateSerializer(
            data={'livro': self.livro.pk, 'quantidade': 6},
        )

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors


class CompraAndLivroViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='owner@example.com', password='secret')
        self.other_user = User.objects.create_user(email='other@example.com', password='secret')
        self.client = APIClient()

    def test_user_sees_only_own_purchases_and_admin_group_sees_all(self):
        Compra.objects.create(usuario=self.user)
        Compra.objects.create(usuario=self.other_user)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/compras/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['usuario'] == self.user.email

        admin_group = Group.objects.create(name='administradores')
        admin_user = User.objects.create_user(email='admin@example.com', password='secret')
        admin_user.groups.add(admin_group)
        self.client.force_authenticate(user=admin_user)
        response = self.client.get('/api/compras/')
        assert response.status_code == status.HTTP_200_OK
        returned_users = {item['usuario'] for item in response.data['results']}
        expected_users = set(Compra.objects.values_list('usuario__email', flat=True))
        assert returned_users == expected_users

    def test_authenticated_user_can_create_purchase_without_model_permission(self):
        livro = Livro.objects.create(titulo='Livro para Compra', preco=Decimal('18.50'), quantidade=3)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            '/api/compras/',
            {'itens': [{'livro': livro.pk, 'quantidade': 1}]},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert 'usuario' not in response.data
        compra = Compra.objects.get(pk=response.data['id'])
        assert compra.usuario == self.user

    def test_alterar_preco_action_updates_book(self):
        superuser = User.objects.create_superuser(email='root@example.com', password='secret')
        livro = Livro.objects.create(titulo='Livro Action', preco=Decimal('10.00'), quantidade=4)
        self.client.force_authenticate(user=superuser)

        response = self.client.patch(
            f'/api/livros/{livro.pk}/alterar_preco/',
            {'preco': '25.50'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        livro.refresh_from_db()
        assert livro.preco == Decimal('25.50')
