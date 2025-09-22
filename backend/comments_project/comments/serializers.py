from rest_framework import serializers
from .models import Comment, User
import bleach
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import ValidationError
from captcha.models import CaptchaStore

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    # Додаємо CAPTCHA поля для валідації
    captcha_0 = serializers.CharField(write_only=True)
    captcha_1 = serializers.CharField(write_only=True)

    def get_replies(self, obj):
        return []

    # def validate(self, data):
    #     # Валідація та очищення тексту
    #     ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
    #     ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    #     data['text'] = bleach.clean(data['text'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    #
    #     # Перетворюємо пустий рядок parent на None
    #     if data.get('parent') == '':
    #         data['parent'] = None
    #
    #     # Валідація CAPTCHA
    #     key = data.get('captcha_0')
    #     value = data.get('captcha_1')
    #     if key and value:
    #         try:
    #             captcha = CaptchaStore.objects.get(hashkey=key)
    #             if captcha.response.lower() != value.lower():
    #                 raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})
    #         except CaptchaStore.DoesNotExist:
    #             raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})
    #     return data

    # тимчасово для тесту
    def validate(self, data):
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        data['text'] = bleach.clean(data['text'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        # Валідація CAPTCHA
        key = data.pop('captcha_0', None)
        value = data.pop('captcha_1', None)
        if key and value:
            try:
                captcha = CaptchaStore.objects.get(hashkey=key)
                if captcha.response.lower() != value.lower():
                    raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})
                # видаляємо використаний Captcha
                captcha.delete()
            except CaptchaStore.DoesNotExist:
                raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})
        return data

    def validate_file(self, value):
        if not value:
            return value
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
        elif value.name.lower().endswith('.txt'):
            if value.size > 100 * 1024:
                raise ValidationError("TXT file must be <= 100KB")
            return value
        else:
            raise ValidationError("Only JPG, GIF, PNG or TXT allowed")

    # def create(self, validated_data):
    #     # Видаляємо поля CAPTCHA перед створенням об'єкта
    #     validated_data.pop('captcha_0', None)
    #     validated_data.pop('captcha_1', None)
    #     return super().create(validated_data)
    def create(self, validated_data):
        return super().create(validated_data)

    class Meta:
        model = Comment
        fields = ['user_name', 'email', 'home_page', 'text', 'parent', 'file', 'created_at', 'replies', 'captcha_0', 'captcha_1']
