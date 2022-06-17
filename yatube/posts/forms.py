from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image',
        )
        help_texts = {
            'text': 'Напишите свой пост',
            'group': 'При необходимости выберите группу',
        }
        labels = {
            "text": ("Текст поста"),
            "group": ('Группа'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'text',
        )
        help_texts = {
            'text': 'Напишите свой комментарий',
        }
        labels = {
            "text": ("Текст комментария"),
        }
