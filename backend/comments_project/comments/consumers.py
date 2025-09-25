import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("comments_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("comments_group", self.channel_name)

    async def receive(self, text_data):
        # Optionally handle incoming messages from clients
        pass

    async def new_comment(self, event):
        # Forward the serialized comment data directly
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment': event['comment']
        }))