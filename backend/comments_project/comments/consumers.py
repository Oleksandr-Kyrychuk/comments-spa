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
        except Exception as e:
            logger.error(f"Failed to add {self.channel_name} to group: {e}")
            await self.close(code=1011, reason=f"Failed to add to group: {str(e)}")

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
            await self.close(code=1011, reason=f"Invalid JSON: {str(e)}")

    async def new_comment(self, event):
        try:
            message = event['comment']
            message_size = len(json.dumps({'type': 'new_comment', 'comment': message}).encode('utf-8'))
            logger.info(f"Sending WebSocket message to {self.channel_name}, size: {message_size} bytes")
            if message_size > 1048576:  # 1MB ліміт
                logger.error(f"Message too large for WebSocket: {message_size} bytes")
                await self.close(code=1011, reason="Message too large")
                return
            await self.send(text_data=json.dumps({
                'type': 'new_comment',
                'comment': message
            }))
            logger.info(f"Successfully sent WebSocket message to {self.channel_name}")
        except KeyError as e:
            logger.error(f"Invalid event format: {str(e)}, event: {event}")
            await self.close(code=1011, reason=f"Invalid event format: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}, event: {event}")
            await self.close(code=1011, reason=f"Send error: {str(e)}")
