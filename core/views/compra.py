from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Compra
from core.serializers import (
    CompraCreateUpdateSerializer,
    CompraSerializer,
)


class CompraViewSet(ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return Compra.objects.none()
        if usuario.is_superuser or usuario.groups.filter(name='administradores').exists():
            return Compra.objects.all().order_by('-data_criacao', '-pk')
        return Compra.objects.filter(usuario=usuario).order_by('-data_criacao', '-pk')

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return CompraCreateUpdateSerializer
        return CompraSerializer
