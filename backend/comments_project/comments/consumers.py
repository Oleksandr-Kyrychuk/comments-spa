import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Comment
from .serializers import CommentSerializer
from asgiref.sync import sync_to_async
import bleach

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("comments_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("comments_group", self.channel_name)

    async def receive(self, text_data):
        # Опційно обробка повідомлень від клієнта
        pass

    async def new_comment(self, event):
        comment_id = event['comment_id']

        # Отримуємо об'єкт Comment асинхронно
        comment_instance = await sync_to_async(Comment.objects.get)(id=comment_id)

        # Серіалізація через sync_to_async, щоб DRF не викликав ORM у async-контексті
        data = await sync_to_async(lambda: CommentSerializer(comment_instance).data)()

        # Очищення text від небезпечного HTML
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        data['text'] = bleach.clean(data.get('text', ''), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment': data
        }))
