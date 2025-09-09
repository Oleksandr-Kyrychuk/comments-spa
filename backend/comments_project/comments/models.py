from django.db import models
from django.core.validators import RegexValidator, URLValidator, EmailValidator, MaxLengthValidator
from django.utils import timezone

class User(models.Model):
    username = models.CharField(
        max_length=50, unique=True,
        validators=[RegexValidator(r'^[a-zA-Z0-9]+$', 'Only letters and digits allowed')],
        help_text='Letters and digits only (required)'
    )
    email = models.EmailField(unique=True, validators=[EmailValidator()], help_text='Valid email format (required)')
    homepage = models.URLField(blank=True, null=True, validators=[URLValidator()], help_text='Valid URL (optional)')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def get_comments(self):
        """OOP метод: усі коментарі користувача"""
        return self.comments.all()

    class Meta:
        ordering = ['username']
        db_table = 'users'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    text = models.TextField(validators=[MaxLengthValidator(5000)], help_text='Text with allowed HTML tags (<a>, <code>, <i>, <strong>)')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True, help_text='Image (JPG/GIF/PNG <=320x240) or TXT (<=100KB)')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username}: {self.text[:50]}..."

    def get_replies(self):
        """OOP метод: каскадне відображення відповідей"""
        return self.replies.order_by('-created_at').all()

    def is_root_comment(self):
        """OOP метод: чи кореневий коментар (для таблиці)"""
        return self.parent is None

    class Meta:
        ordering = ['-created_at']  # LIFO за замовчуванням
        db_table = 'comments'

class Captcha(models.Model):
    solution = models.CharField(max_length=10, validators=[RegexValidator(r'^[a-zA-Z0-9]+$', 'Letters and digits only')])
    image = models.ImageField(upload_to='captchas/')
    expires_at = models.DateTimeField()

    def is_valid(self, user_input):
        """OOP метод: перевірка CAPTCHA"""
        return self.solution.lower() == user_input.lower() and not self.is_expired()

    def is_expired(self):
        """OOP метод: перевірка терміну дії"""
        return self.expires_at < timezone.now()

    class Meta:
        db_table = 'captcha'