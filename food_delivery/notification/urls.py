from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *

urlpatterns = [
    path("order/<uuid:order_id>",room,name='room'),
    path("testmsg/",test,name="test"),
]