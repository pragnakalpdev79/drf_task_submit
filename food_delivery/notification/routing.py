from django.urls import re_path,path
from .consumers import *

websocket_urlpatterns = [
    path(r'ws/orders/<uuid:order_id>/',OrderConsumer.as_asgi()),
    path(r'ws/restaurant/orders/<uuid:resto_id>/',RestoConsumer.as_asgi()),
    path(r'ws/customer/<uuid:user_id>/',CustomerConsumer.as_asgi()),
    path(r'ws/driver/neworders/',DriverConsumer.as_asgi()),
    # ws://localhost/ws/orders/
]