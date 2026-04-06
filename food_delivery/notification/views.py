from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes

def room(request,order_id):
    channel_layer = get_channel_layer()
    print("1.chanel-layer---- >   ",channel_layer)
    print(order_id)
    token = str(request.META.get('HTTP_AUTHORIZATION'))
    return render(request,"notification/room.html",{
        "order_id" : order_id,
        "token" : token,
    })

@api_view(('GET',))
def test(request):
    channel_layer = get_channel_layer()
    print("2.chanel-layer---- >   ",channel_layer)
    message = "message from views"
    async_to_sync(channel_layer.group_send)(
        "orders",
            {
                "type": "chat.message",
                "message": message,
                #this sends an event over channel layer
                #which will be handled by chat.message = chat_message
            }
    )
    return Response({
        "message" : "message sent"
    })