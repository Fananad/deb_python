import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    """
    Создаём тестовую запись в БД
    с созданием тестовой группы
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_auth = User.objects.create_user(username='test_auth')
        cls.follower_user = User.objects.create_user(username='test_follower')
        cls.group = Group.objects.create(
            title='Test group_title',
            slug='test_slug',
            description='Test description',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.author_auth,
            text='test post',
            image=cls.uploaded
        )
        cls.form = PostForm()
        cls.page_index = reverse('posts:index')
        cls.page_group_list = reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}
        )
        cls.page_profile = reverse(
            'posts:profile', kwargs={'username': cls.author_auth}
        )
        cls.page_post_detail = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk}
        )
        cls.page_post_create = reverse('posts:post_create')
        cls.page_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk}
        )
        cls.urls_list = [
            (cls.page_index, 'posts/index.html'),
            (cls.page_group_list, 'posts/group_list.html'),
            (cls.page_profile, 'posts/profile.html'),
            (cls.page_post_detail, 'posts/post_detail.html'),
            (cls.page_post_create, 'posts/create_post.html'),
            (cls.page_post_edit, 'posts/create_post.html')
        ]
        cls.pages_with_paginator = [
            (cls.page_index),
            (cls.page_profile),
            (cls.page_group_list),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.author_auth)
        self.follower_client = Client()
        self.follower_client.force_login(PostViewsTests.follower_user)
        cache.clear()

    def asserts(self, first_obj):
        self.assertEqual(first_obj.author, PostViewsTests.author_auth)
        self.assertEqual(first_obj.group, PostViewsTests.group)
        self.assertEqual(first_obj.pk, PostViewsTests.post.pk)

    def test_pages_correct_template(self):
        """
        URL-адрес получает нужный шаблон.
        """
        for reverse_name, template in PostViewsTests.urls_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_profile_correct_context(self):
        """
        Шаблон profile создан с правильным Context.
        """
        response = self.authorized_client.get(PostViewsTests.page_profile)
        first_obj = response.context['page_obj'][0]
        self.asserts(first_obj)
        self.assertEqual(
            response.context['post'].id, PostViewsTests.post.pk
        )
        self.assertEqual(
            response.context['post'].image, PostViewsTests.post.image
        )
        self.assertEqual(
            response.context['post'].comments, PostViewsTests.post.comments
        )
        self.assertEqual(
            response.context['author'], PostViewsTests.author_auth
        )

    def test_page_group_list_correct_context(self):
        """
        Шаблон group_list создан с правильным Context.
        """
        response = self.authorized_client.get(PostViewsTests.page_group_list)
        first_obj = response.context['page_obj'][0]
        self.asserts(first_obj)
        self.assertEqual(
            response.context['group'], PostViewsTests.group
        )

    def test_page_post_detail_correct_context(self):
        """
        Шаблон post_detail создан с правильным Context.
        """

        response = self.authorized_client.get(PostViewsTests.page_post_detail)
        self.assertEqual(
            response.context['post'].id, PostViewsTests.post.pk
        )
        self.assertEqual(
            response.context['post'].image, PostViewsTests.post.image
        )
        self.assertEqual(
            response.context['post'].comments, PostViewsTests.post.comments
        )
        self.assertEqual(response.context['post'], PostViewsTests.post)

    def test_post_included_in_another_group(self):
        """
        Проверяем, что пост не попадёт не в свою группу
        """
        self.group_2 = Group.objects.create(
            title='Test group_title2',
            slug='test_slug2',
            description='Test description2',
        )
        self.post_2 = Post.objects.create(
            group=self.group_2,
            author=PostViewsTests.author_auth,
            text='test post2'
        )
        response = self.authorized_client.get(PostViewsTests.page_group_list)
        response_2 = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug2'})
        )
        self.assertEqual(
            response.context['page_obj'][0].group, PostViewsTests.post.group
        )
        self.assertEqual(
            response_2.context['page_obj'][0].group, self.post_2.group
        )

    def test_first_page_contains_ten_records(self):
        """
        Проверка кол-ва постов на странице.
        """
        self.posts = [(Post(
            author=PostViewsTests.author_auth,
            text=f'Test post {i}',
            group=PostViewsTests.group
        ))
            for i in range(13)
        ]
        Post.objects.bulk_create(self.posts)
        page_postfixurl_posts = [(1, 10), (2, 4)]
        for page_paginator, posts in page_postfixurl_posts:
            for page in PostViewsTests.pages_with_paginator:
                with self.subTest(page=page):
                    response = self.client.get(page, {'page': page_paginator})
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_post_edit_page_show_correct_context(self):
        """
        Шаблон create_post для post_edt сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(PostViewsTests.page_post_edit)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['post'], PostViewsTests.post)
        self.assertEqual(response.context['is_edit'], True)

    def test_cache_index(self):
        """
        Проверка хранения и очищения кэша для index.
        """
        first_response = self.authorized_client.get(PostViewsTests.page_index)
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second_response = self.authorized_client.get(PostViewsTests.page_index)
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(PostViewsTests.page_index)
        self.assertNotEqual(first_response.content, third_response.content)

    def test_authorized_user_can_follow(self):
        """
        Авторизованный пользователь может подписаться на автора
        и отписаться.
        """
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewsTests.author_auth.username})
        )
        follow_count = Follow.objects.all().count()
        self.assertEqual(follow_count, 1)
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostViewsTests.author_auth.username})
        )
        unfollow_count = Follow.objects.all().count()
        self.assertEqual(unfollow_count, 0)

    def test_new_post_appears_in_the_subscribers(self):
        """
        Новый пост появляется у подписчиков автора поста
        и отсутвует у тех кто не подписан на автора."""
        self.new_post = Post.objects.create(
            group=PostViewsTests.group,
            author=PostViewsTests.author_auth,
            text='Написал новый пост'
        )
        Follow.objects.create(
            user=PostViewsTests.follower_user,
            author=PostViewsTests.author_auth
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['page_obj'][0].text, self.new_post.text
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(
            response, self.new_post.text
        )

    def test_authorized_user_can_comment(self):
        """
        Авторизованный пользователь может комментировать посты
        """
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            author=PostViewsTests.author_auth,
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
            author=PostViewsTests.author_auth,
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
