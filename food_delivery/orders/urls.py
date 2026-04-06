from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'new',OrderViewSet,basename='neworders')
router.register(r'cart',CartViewSet,basename='mycart')
router.register(r'reviews',ReviewViewSet,basename='reviews')

urlpatterns = [
    path("",include(router.urls)),
]
