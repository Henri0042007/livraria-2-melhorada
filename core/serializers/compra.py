from django.db import transaction
from rest_framework.serializers import (
    CharField,
    CurrentUserDefault,
    DateTimeField,
    DecimalField,
    HiddenField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)

from core.models import Compra, ItensCompra
from uploader.serializers import ImageSerializer


class ItensCompraCreateUpdateSerializer(ModelSerializer):
    preco = DecimalField(max_digits=7, decimal_places=2, read_only=True)

    class Meta:
        model = ItensCompra
        fields = ('livro', 'quantidade', 'preco')

    def validate_quantidade(self, quantidade):
        if quantidade <= 0:
            raise ValidationError('A quantidade deve ser maior do que zero.')
        return quantidade

    def validate(self, item):
        if item['quantidade'] > (item['livro'].quantidade or 0):
            raise ValidationError('Quantidade de itens maior do que a quantidade em estoque.')
        return item


class ItensCompraSerializer(ModelSerializer):
    titulo = SerializerMethodField()
    editora = SerializerMethodField()
    preco = SerializerMethodField()
    capa = SerializerMethodField()
    total = SerializerMethodField()

    def get_titulo(self, instance):
        return instance.livro.titulo

    def get_editora(self, instance):
        return instance.livro.editora.nome if instance.livro.editora else None

    def get_preco(self, instance):
        return instance.preco

    def get_capa(self, instance):
        if not instance.livro.capa:
            return None
        return ImageSerializer(instance.livro.capa).data

    def get_total(self, instance):
        return instance.preco * instance.quantidade

    class Meta:
        model = ItensCompra
        fields = ('id', 'titulo', 'editora', 'quantidade', 'preco', 'total', 'capa')


class CompraCreateUpdateSerializer(ModelSerializer):
    usuario = HiddenField(default=CurrentUserDefault())
    itens = ItensCompraCreateUpdateSerializer(many=True)

    class Meta:
        model = Compra
        fields = ('id', 'usuario', 'itens')

    @transaction.atomic
    def create(self, validated_data):
        itens = validated_data.pop('itens')
        compra = Compra.objects.create(**validated_data)
        for item in itens:
            item['preco'] = item['livro'].preco
            ItensCompra.objects.create(compra=compra, **item)
        return compra

    @transaction.atomic
    def update(self, compra, validated_data):
        itens_data = validated_data.pop('itens', None)
        validated_data.pop('usuario', None)
        if itens_data is not None:
            compra.itens.all().delete()
            for item_data in itens_data:
                item_data['preco'] = item_data['livro'].preco
                ItensCompra.objects.create(compra=compra, **item_data)
        return super().update(compra, validated_data)


class ItensCompraListSerializer(ModelSerializer):
    livro = CharField(source='livro.titulo', read_only=True)

    class Meta:
        model = ItensCompra
        fields = ('quantidade', 'preco', 'livro')
        depth = 1


class CompraListSerializer(ModelSerializer):
    usuario = CharField(source='usuario.email', read_only=True)
    itens = ItensCompraListSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ('id', 'usuario', 'itens')


class CompraSerializer(ModelSerializer):
    usuario = CharField(source='usuario.email', read_only=True)
    status = CharField(source='get_status_display', read_only=True)
    data_criacao = DateTimeField(read_only=True)
    data_atualizacao = DateTimeField(read_only=True)
    tipo_pagamento = CharField(source='get_tipo_pagamento_display', read_only=True)
    itens = ItensCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = (
            'id',
            'usuario',
            'status',
            'total',
            'data_criacao',
            'data_atualizacao',
            'tipo_pagamento',
            'itens',
        )
