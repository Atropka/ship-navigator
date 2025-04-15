from django.db import models

class Port(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class WaterPath(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    coordinates = models.JSONField()  # Список координат для водного пути

    def __str__(self):
        return self.name if self.name else f"Water Path {self.id}"