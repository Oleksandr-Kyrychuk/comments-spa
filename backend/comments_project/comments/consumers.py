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

    async def disconnect(self, close_code):
        logger.info(f"Removing {self.channel_name} from group 'comments_group'")
        try:
            await self.channel_layer.group_discard("comments_group", self.channel_name)
            logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
        except Exception as e:
            logger.error(f"Failed to remove {self.channel_name} from group: {e}")


    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            "comments_group",
            {
                "type": "new_comment",
                "comment": data
            }
        )

    async def new_comment(self, event):
        try:
            logger.info(f"Sending WebSocket message: {event}")
            await self.send(text_data=json.dumps({
                'type': 'new_comment',
                'comment': event['comment']
            }))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")