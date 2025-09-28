import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("comments_group", self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}, Group: comments_group")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("comments_group", self.channel_name)
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")

    async def new_comment(self, event):
        logger.info(f"Received event: {event}, Channel: {self.channel_name}")
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_comment',
                'comment': event['comment']
            }))
            logger.info(f"Sent WebSocket message to {self.channel_name}: {event['comment']}")
        except Exception as e:
            logger.error(f"Error sending WebSocket message to {self.channel_name}: {str(e)}")