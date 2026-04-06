from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r"details",RestaurantViewSet,basename='restaurant')
router.register(r"rmenuitem",MenuItemViewSet,basename='menuitem')

urlpatterns = [
    path("",include(router.urls)),    
]