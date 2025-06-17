from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortViewSet, route_calculation, get_water_graph

router = DefaultRouter()
router.register(r'ports', PortViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('calculate_route/', route_calculation, name='route_calculation'),
    path('water_graph/', get_water_graph, name='get_water_graph'),
]
