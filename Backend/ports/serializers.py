from rest_framework import serializers
from .models import Port

# Сериализатор для портов
class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ['id', 'name', 'latitude', 'longitude']


