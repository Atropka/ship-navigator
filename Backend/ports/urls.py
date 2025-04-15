from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortViewSet, route_calculation

router = DefaultRouter()
router.register(r'ports', PortViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('calculate_route/', route_calculation, name='route_calculation'),
]
