# import json 
# from channels.generic.websocket import AsyncWebsocketConsumer


# class OrderConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = "users"

#         await self.channel_layer.group_add(self.room_group_name,self.channel_name)
#         print("intiated")
#         await self.accept()

#     async def disconnect(self,close_code):
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("disconnecting")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         await self.channel_layer.group_discard(
#             self.room_group_name,self.channel_name
#         )    

#     async def receive(self,text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]
#         print("---------message recieved----------")
#         print(message)
#         print("calling the chatmessage function")
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat.message",
#                 "message" : message
#             })

#     async def chat_message(self, event):
#         message = event["message"]
#         print("inside chat message function")
#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message}))  

# class OrderManagementConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = "users"

#         await self.channel_layer.group_add(self.room_group_name,self.channel_name)
#         print("intiated")
#         await self.accept()

#     async def disconnect(self,close_code):
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("disconnecting")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         await self.channel_layer.group_discard(
#             self.room_group_name,self.channel_name
#         )    

#     async def receive(self,text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]
#         print("---------message recieved----------")
#         print(message)
#         print("calling the chatmessage function")
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat.message",
#                 "message" : message
#             })

#     async def chat_message(self, event):
#         message = event["message"]
#         print("inside chat message function")
#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message})) 

# class RestaurantDashboardConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = "users"

#         await self.channel_layer.group_add(self.room_group_name,self.channel_name)
#         print("intiated")
#         await self.accept()

#     async def disconnect(self,close_code):
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("disconnecting")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         print("====================================================")
#         await self.channel_layer.group_discard(
#             self.room_group_name,self.channel_name
#         )    

#     async def receive(self,text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]
#         print("---------message recieved----------")
#         print(message)
#         print("calling the chatmessage function")
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat.message",
#                 "message" : message
#             })

#     async def chat_message(self, event):
#         message = event["message"]
#         print("inside chat message function")
#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message}))
                                             