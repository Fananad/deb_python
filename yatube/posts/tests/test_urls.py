from http import HTTPStatus

from django.test import Client, TestCase

# мой i-sort или i-sort на ЯП не даёт мне
# делать путь posts.models хотя настройки есть в setup.cfg
# и так в каждом тесте
from ..models import Group, Post, User


class PostURLTests(TestCase):
    """
    Создаём тестовую запись в БД
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_auth = User.objects.create_user(username='test auth')
        cls.not_author = User.objects.create_user(username='Not Author')
        cls.group = Group.objects.create(
            title='Test group_title',
            slug='test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            text='test post',
            author=cls.author_auth
        )
        cls.public_urls = [
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author_auth.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
        ]
        cls.post_edit_url = f'/posts/{cls.post.pk}/edit/'
        cls.create_url = '/create/'
        cls.private_urls = [
            (cls.create_url, 'posts/create_post.html'),
            (cls.post_edit_url, 'posts/create_post.html')
        ]
        cls.redirect_urls_for_non_authorized_user = [
            (cls.create_url, f'/auth/login/?next={cls.create_url}'),
            (cls.post_edit_url, f'/auth/login/?next={cls.post_edit_url}')
        ]

    def setUp(self):
        self.not_author = Client()
        self.not_author.force_login(PostURLTests.not_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.author_auth)

    def test_posts_urls_exists_at_desired_location(self):
        """
        Проверка страниц с доступом любому пользователю
        с корректным шаблоном.
        """
        for address, template in PostURLTests.public_urls:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_create_and_edit_exists_at_desired_location_authorized(self):
        """
        Проверка страниц для авторизованных пользователей
        с корректным шаблоном.
        """
        for adress, template in PostURLTests.private_urls:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_edit_not_available_to_not_author(self):
        """
        Страница /posts/<post_id>/edit/ перенаправит
        не автора на страницу с информацией поста.
        """
        response = self.not_author.get(
            PostURLTests.post_edit_url, follow=True
        )
        self.assertRedirects(response, f'/posts/{PostURLTests.post.pk}/')

    def test_urls_redirect_anonymous_on_login(self):
        """
        Страницы перенаправят неавторизованного пользователя
        на страницу логина.
        """
        for url, redirect in (
            PostURLTests.
            redirect_urls_for_non_authorized_user
        ):
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, redirect)


# данный тест у меня был в core/tests.py
class ViewTestClass(TestCase):
    """
    Проверка использования корректного шаблона
    при неизвестной странице
    """
    def test_error_page_404(self):
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
