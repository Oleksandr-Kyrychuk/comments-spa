from django.urls import path
from .views import CommentListCreateView, PreviewView

urlpatterns = [
    path('comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('preview/', PreviewView.as_view(), name='preview'),
]