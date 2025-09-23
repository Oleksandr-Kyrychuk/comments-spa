from rest_framework import serializers
from .models import Comment, User
import bleach
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import ValidationError
from captcha.models import CaptchaStore
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'homepage']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    replies = serializers.SerializerMethodField()
    captcha_0 = serializers.CharField(write_only=True, required=False)
    captcha_1 = serializers.CharField(write_only=True, required=False)

    def get_replies(self, obj):
        # Оптимізована рекурсія з обмеженням глибини
        def serialize_replies(comment, depth=0, max_depth=5):
            if depth >= max_depth:
                return []
            children = Comment.objects.filter(parent=comment).order_by('created_at')
            serializer = CommentSerializer(children, many=True, context=self.context)
            return serializer.data
        return serialize_replies(obj)

    def validate(self, data):
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        data['text'] = bleach.clean(data['text'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        # Валідація закритих HTML тегів
        html_pattern = r'^(?:(?!<[^>]+>\s*<\w+\b[^>]*>).)*$'
        if not re.match(html_pattern, data['text']):
            raise serializers.ValidationError({"text": "Invalid HTML: unbalanced tags"})

        if data.get('parent') == '':
            data['parent'] = None

        # Валідація CAPTCHA
        key = data.pop('captcha_0', None)
        value = data.pop('captcha_1', None)
        if key and value:
            try:
                captcha = CaptchaStore.objects.get(hashkey=key)
                if captcha.response.lower() != value.lower():
                    raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})
                captcha.delete()
            except CaptchaStore.DoesNotExist:
                raise serializers.ValidationError({"captcha": "Invalid CAPTCHA"})

        # Валідація файлу
        if 'file' in data and data['file']:
            data['file'] = self.validate_file(data['file'])

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

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={'email': user_data['email'], 'homepage': user_data.get('homepage')}
        )
        validated_data['user'] = user
        instance = super().create(validated_data)
        if instance.file:
            instance.file = instance.file.name
            instance.save()
        return instance

    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'parent', 'file', 'created_at', 'replies', 'captcha_0', 'captcha_1']
        read_only_fields = ['created_at', 'replies']
        extra_kwargs = {
            'captcha_0': {'write_only': True},
            'captcha_1': {'write_only': True},
        }