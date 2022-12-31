from django.test import TestCase

from ..models import Group, Post, User

AMOUNT_CHAR_POST: int = 15


class PostModelTest(TestCase):
    """Создаём тестовую запись в БД"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group_title',
            slug='test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test post',
        )

    def test_models_have_correct_object_names(self):
        """Проверка, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_result = {
            str(post): post.text[:AMOUNT_CHAR_POST],
            str(group): group.title,
        }
        for value, expected in expected_result.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name(self):
        """
        Проверка, что у моделей есть verbose_name
        """
        post = PostModelTest.post
        field_verboses = (
            ['text', 'Текст поста'],
            ['pub_date', 'Дата создания'],
            ['author', 'Автор'],
            ['group', 'Сообщество']
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """
        Проверка, что у моделей есть help_texts
        """
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите что нибудь содержательное',
            'group': 'Здесь можно выбрать группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
