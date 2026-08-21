from decimal import Decimal

from django.test import TestCase

from core.models import Compra, Editora, ItensCompra, Livro, User
from core.serializers.compra import ItensCompraSerializer


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
        item = ItensCompra.objects.create(compra=compra, livro=livro, quantidade=2)

        data = ItensCompraSerializer(item).data

        self.assertEqual(data['titulo'], 'Livro Teste')
        self.assertEqual(data['editora'], 'Editora Teste')
        self.assertEqual(str(data['preco']), '39.90')
        self.assertEqual(str(data['total']), '79.80')
