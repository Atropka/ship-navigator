from django.contrib import admin
from .models import Port

@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')  # Отображение столбцов
    search_fields = ('name',)  # Поиск по названию порта
