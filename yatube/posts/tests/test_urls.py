from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()

templates_url_names = {
    '/': 'posts/index.html',
    '/group/slug_test/': 'posts/group_list.html',
    '/profile/auth/': 'posts/profile.html',
    '/posts/1/': 'posts/post_detail.html',
    '/posts/1/edit/': 'posts/create_post.html',
    '/create/': 'posts/create_post.html',
}


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author = self.user
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.user_authorized = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for address, template in templates_url_names.items():
            if address == '/create/':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
            elif address == f'/posts/{self.post.id}/edit/':
                with self.subTest(address=address):
                    response = self.authorized_author.get(address)
                    self.assertTemplateUsed(response, template)
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
            else:
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertTemplateUsed(response, template)

    def test_urls_exists(self):
        """URL-адрес доступен."""
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexpecting_page(self):
        """Ошибка 404."""
        response = self.guest_client.get('/unexpecting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
