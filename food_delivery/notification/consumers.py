from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime
import logging

logger = logging.getLogger('user')

#==============================================================================
# 1. Customer Room
class CustomerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f'customer_{self.room_name}'  
        self.user = self.scope['user']
        print(self.user)
        if not self.user.utype == 'c' and self.user.id != self.room_name:
            print("you cant access this room")
            print(f"Room Name: -  {self.room_name}")
            await self.close()
            return
        print("customer is verified and entered")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"connection started WITH {self.user} for ORDER {self.room_name} and group NAME : ---   {self.room_group_name} ")
        await self.accept()

    async def disconnect(self, close_code):
        print(f"Connection closed with code: {close_code}")
        print(f"Connection closing with {self.user}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def receive(self, text_data ):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("---------message recieved----------")
        print(message)
        print("calling the chatmessage function")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
            }
        )
    async def chat_message(self,event):
        message = event["message"]
        print("inside the chat message function")
        print(message)
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

#==============================================================================
# 2. Order Room
class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(self.scope["url_route"]["kwargs"])
        self.room_name = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f'order_{self.room_name}'
        #Get the authenticated user
        self.user = self.scope['user']
        print(self.user)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Called on connection.
        # To accept the connection and specify a chosen subprotocol.
        # A list of subprotocols specified by the connecting client
        # will be available in self.scope['subprotocols']
        await self.accept()



    async def disconnect(self, close_code):
        print(f"Connection closed with code: {close_code}")
        print(self.user)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data ):
        #========================================
        # rc1 this part receives and processes the incoming message
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("---------message recieved----------")
        print(message)
        #========================================
        # rc2 this part sends the message to room group
        print("calling the chatmessage function")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                #this sends an event over channel layer
                #which will be handled by chat.message = chat_message
            }
        )

    async def chat_message(self,event):
        message = event["message"]
        print("inside the chat message function")
        print(message)
        
        await self.send(text_data=json.dumps({"message": message}))


    async def send_notification(self,event):
        notification = event['message']

        await self.send(text_data=json.dumps({
            'notification' : notification
        }))


#==============================================================================
# Resto. Order Room
class RestoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["resto_id"]
        self.room_group_name = f'restaurant_{self.room_name}'
        self.user = self.scope['user']
        print(self.user.utype)
        if not self.user.utype == 'r':
            print("you cant access this room")
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"Connection closed with code: {close_code}")
        print(self.user)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def receive(self, text_data ):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("---------message recieved----------")
        print(message)
        print("calling the chatmessage function")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
            }
        )
    async def chat_message(self,event):
        message = event["message"]
        print("inside the chat message function")
        print(message)
        
        await self.send(text_data=json.dumps({"message": message}))



#==============================================================================
# Driver New Orders Room
class DriverConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "driver_room"
        self.room_group_name = "drivers"
        self.user = self.scope['user']
        print(self.user)
        print(self.user.utype)
        if not self.user.utype == 'd':
            print("you cant access this room")
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"Connection closed with code: {close_code}")
        print(self.user)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    async def receive(self, text_data ):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("---------message recieved----------")
        print(message)
        print("calling the chatmessage function")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
            }
        )
    async def chat_message(self,event):
        message = event["message"]
        print("inside the chat message function")
        print(message)
        
        await self.send(text_data=json.dumps({"message": message}))