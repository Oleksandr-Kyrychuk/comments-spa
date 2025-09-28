import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

logger = logging.getLogger(__name__)

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("comments_group", self.channel_name)
        logger.info(f"Added to comments_group: {self.channel_name} at {datetime.now()}")
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name} at {datetime.now()}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("comments_group", self.channel_name)
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code} at {datetime.now()}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.info(f"Received WebSocket message: {data} at {datetime.now()}")
        await self.channel_layer.group_send(
            "comments_group",
            {
                "type": "new_comment",
                "comment": data
            }
        )
        logger.info(f"Sent to group comments_group: {data} at {datetime.now()}")

    async def new_comment(self, event):
        try:
            logger.info(f"Sending WebSocket message to {self.channel_name}: {event['comment']} at {datetime.now()}")
            await self.send(text_data=json.dumps({
                'type': 'new_comment',
                'comment': event['comment']
            }))
        except Exception as e:
            logger.error(f"Error sending WebSocket message to {self.channel_name}: {str(e)}")