import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"Attempting to add {self.channel_name} to group 'comments_group'")
        try:
            await self.channel_layer.group_add("comments_group", self.channel_name)
            await self.accept()
            logger.info(f"WebSocket connected: {self.channel_name} and added to group 'comments_group'")
            # Логуємо активні канали в групі
            group_channels = await self.channel_layer.group_channels('comments_group')
            logger.info(f"Current group members: {group_channels}")
        except Exception as e:
            logger.error(f"Failed to add {self.channel_name} to group: {e}")

    async def disconnect(self, close_code):
        logger.info(f"Removing {self.channel_name} from group 'comments_group'")
        try:
            await self.channel_layer.group_discard("comments_group", self.channel_name)
            logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}, reason: {self.close_reason or 'No reason provided'}")
        except Exception as e:
            logger.error(f"Failed to remove {self.channel_name} from group: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                logger.info(f"Received ping, sent pong to {self.channel_name}")
            else:
                logger.warn(f"Unknown message received: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")

    async def comment_message(self, event):
        try:
            logger.info(f"Sending WebSocket message to {self.channel_name}: {event['message']}")
            await self.send(text_data=json.dumps({
                'type': 'new_comment',
                'comment': event['message']
            }))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")