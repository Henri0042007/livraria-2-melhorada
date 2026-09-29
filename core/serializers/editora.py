from rest_framework.serializers import ModelSerializer

from core.models import Editora


class EditoraSerializer(ModelSerializer):
    def validate_email(self, email):
        return email.lower() if email else email

    class Meta:
        model = Editora
        fields = '__all__'
