import shutil
import tempfile              # Я вроде прочитал документацию и поправил

from django import forms     # хотя если честно, я вроде
from http import HTTPStatus  # ничего не нашёл в других файлах...
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NEW_POST = reverse('posts:post_create')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_auth = User.objects.create_user(username='test auth')
        cls.not_author = User.objects.create_user(username='Not Author')
        cls.group = Group.objects.create(
            title='Test group_title',
            slug='test_slug',
            description='Test description'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.author_auth,
            text='test post'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.author_auth)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            PostFormTests.not_author
        )

    def test_post_create(self):
        """
        Проверка создания нового поста авторизованным пользователем
        """
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        posts = Post.objects.all()
        posts.delete()
        data = {
            'text': 'Текст формы',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            NEW_POST,
            data=data,
            follow=True
        )
        posts_count = Post.objects.count()
        post = response.context['page_obj'][0]
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post.text, data['text'])
        self.assertEqual(post.group.pk, data['group'])
        self.assertEqual(post.author, self.author_auth)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=data['text'],
                id=post.pk,
                group=data['group'],
                image=data['image']
            ).exists
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': post.author}
            )
        )

    def test_new_post_correct_context(self):
        """
        Проверка корректного отображения
        Context нового поста
        """
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        post = Post.objects.create(
            group=PostFormTests.group,
            author=PostFormTests.author_auth,
            text='test post',
            image=uploaded
        )
        urls = [
            NEW_POST,
            reverse(
                'posts:post_edit', kwargs={'post_id': post.pk}
            )
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.Field,
            'image': forms.fields.ImageField
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_edit_post(self):
        """
        Проверка редактирования поста автором
        и комментирование поста авторизованынм пользователем
        """
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            author=PostFormTests.author_auth,
            text='test post',
            group=self.group
        )
        group_2 = Group.objects.create(
            title='Test group_title2',
            slug='test_slug2',
            description='Test description2'
        )
        comment = Comment.objects.create(
            text='Коммент',
            author=PostFormTests.author_auth,
            post=post
        )
        data = {
            'text': 'edit text test',
            'group': group_2.id,
            'comments': comment
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post.pk}
            ),
            data=data,
            follow=True,
        )
        post = response.context['post']
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(post.text, data['text'])
        self.assertEqual(data['group'], post.group.id)
        self.assertEqual(post.author, self.author_auth)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=data['text'],
                id=post.pk,
                group=data['group'],
                comments=data['comments']
            ).exists()
        )
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 1)

    def test_anonym_dont_create_post(self):
        """
        Проверка запрета создания поста анонимом
        """
        form_data = {
            'text': 'Text anonym',
            'group': PostFormTests.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_not_author_form(self):
        """
        Проверка запрета на редактирование
        чужого поста.
        """
        post = PostFormTests.post
        group_2 = Group.objects.create(
            title='Test group_title2',
            slug='test_slug2',
            description='Test description2'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': group_2.id
        }
        response = self.authorized_client_not_author.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                id=post.pk,
                group=form_data['group']
            ).exists()
        )

    def test_anonym_dont_create_comment(self):
        """
        Проверка запрета на комментирование анонимом
        """
        post = PostFormTests.post
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk})
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post.pk}/comment/'
        )
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.author_auth,
            'text': "Тестовый комментарий",
        }
        self.guest_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_author_can_add_comment(self):
        """
        Тест на добавление комментария авторизованным пользователем
        """
        post = self.post
        form_data = {
            'text': 'комментарий',
        }
        comments_count = Comment.objects.count()
        self.authorized_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        post.comments.filter(text='комментарий').exists()
