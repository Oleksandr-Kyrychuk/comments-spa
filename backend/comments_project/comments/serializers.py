from rest_framework import serializers
from captcha.serializers import CaptchaModelSerializer  # Вбудований серіалізатор
from .models import Comment
import bleach
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import ValidationError

class CommentSerializer(CaptchaModelSerializer):
    def validate(self, data):
        # CAPTCHA автоматично валідується через CaptchaModelSerializer
        # Очищення HTML-тегів для захисту від XSS
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        data['text'] = bleach.clean(data['text'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return data

    def validate_file(self, value):
        if not value:
            return value
        # Валідація зображень
        if value.name.lower().endswith(('.jpg', '.jpeg', '.gif', '.png')):
            img = Image.open(value)
            if img.format not in ['JPEG', 'GIF', 'PNG']:
                raise ValidationError("Only JPG, GIF, PNG allowed")
            if img.size[0] > 320 or img.size[1] > 240:
                img.thumbnail((320, 240))
                output = BytesIO()
                img.save(output, format=img.format)
                value = ContentFile(output.getvalue(), value.name)
            return value
        # Валідація текстових файлів
        elif value.name.lower().endswith('.txt'):
            if value.size > 100 * 1024:  # 100KB
                raise ValidationError("TXT file must be <= 100KB")
            return value
        else:
            raise ValidationError("Only JPG, GIF, PNG or TXT allowed")

    class Meta:
        model = Comment
        fields = ['user_name', 'email', 'home_page', 'text', 'parent', 'file', 'created_at', 'captcha_hashkey', 'captcha_code']