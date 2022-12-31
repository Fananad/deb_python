from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Расскажите, что у Вас нового? :)'
        )
        self.fields['group'].empty_label = (
            'Выбор группы остаётся за Вами!'
        )


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Введите текст комментария'
        )
