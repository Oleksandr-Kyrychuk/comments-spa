# serializers.py
from rest_framework import serializers
from .models import Comment, User
import bleach
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import ValidationError
from captcha.models import CaptchaStore
import re
import json

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'homepage']

    def create(self, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'homepage': validated_data.get('homepage', '')}
        )
        return user

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)
    user_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    home_page = serializers.URLField(write_only=True, allow_blank=True)
    replies = serializers.SerializerMethodField()
    captcha_0 = serializers.CharField(write_only=True, required=False)
    captcha_1 = serializers.CharField(write_only=True, required=False)
    parent_username = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'text', 'parent', 'file', 'created_at',
            'replies', 'captcha_0', 'captcha_1', 'parent_username',
            'user_name', 'email', 'home_page'
        ]
        read_only_fields = ['created_at', 'replies', 'parent_username']
        extra_kwargs = {
            'captcha_0': {'write_only': True},
            'captcha_1': {'write_only': True},
        }

    def to_internal_value(self, data):
        # If 'user' is provided as a JSON string, parse it
        if isinstance(data.get('user'), str):
            try:
                data['user'] = json.loads(data['user'])
            except json.JSONDecodeError:
                raise serializers.ValidationError({"user": "Invalid JSON"})
        return super().to_internal_value(data)

    def validate(self, data):
        # Clean text with bleach
        ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
        ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
        data['text'] = bleach.clean(data['text'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        # Validate HTML tags
        html_pattern = r'^(?:(?!<[^>]+>\s*<\w+\b[^>]*>).)*$'
        if not re.match(html_pattern, data['text']):
            raise serializers.ValidationError({"text": "Invalid HTML: unbalanced tags"})

        # Handle empty parent
        if data.get('parent') == '':
            data['parent'] = None

        # Validate CAPTCHA
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

        # Validate file
        if 'file' in data and data['file']:
            data['file'] = self.validate_file(data['file'])

        # Create user object from user_name, email, home_page
        user_data = {
            'username': data.pop('user_name', None),
            'email': data.pop('email', None),
            'homepage': data.pop('home_page', '')
        }
        if user_data['username'] and user_data['email']:
            user_serializer = UserSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            data['user'] = user_serializer.validated_data
        else:
            raise serializers.ValidationError({"user": "Username and email are required"})

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
        user, _ = User.objects.update_or_create(
            username=user_data['username'],
            defaults={'email': user_data['email'], 'homepage': user_data.get('homepage', '')}
        )
        validated_data['user'] = user
        instance = super().create(validated_data)
        if instance.file:
            instance.file = instance.file.name
            instance.save()
        return instance

    def get_replies(self, obj):
        def serialize_replies(comment, depth=0, max_depth=5):
            if depth >= max_depth:
                return []

            request = self.context.get('request', None)
            if request and hasattr(request, 'query_params'):
                ordering = request.query_params.get('ordering', 'created_at')
            else:
                ordering = 'created_at'

            children = Comment.objects.filter(parent=comment).order_by(ordering)
            serializer = CommentSerializer(children, many=True, context=self.context)
            return serializer.data

        return serialize_replies(obj)

    def get_parent_username(self, obj):
        if obj.parent:
            return obj.parent.user.username
        return ''
