from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache
from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Neo')
        cls.group = Group.objects.create(
            title='Исследователи Матрицы',
            slug='Matrix',
            description='Группа искателей Морфеуса',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Нужно следовать за белым кроликом',
        )
        cls.guest_client = Client()
        cls.author = cls.user
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.user_authorized = User.objects.create_user(username='Morpheus')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_authorized)

        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_authorized,
            text='Нео ты избранный!',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_authorized,
            author=cls.user,
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            f'/posts/{PostURLTests.post.id}/comment/':
            'posts/post_detail.html',
            f'/profile/{PostURLTests.user.username}/follow/':
            'posts/profile.html',
            f'/profile/{PostURLTests.user.username}/unfollow/':
            'posts/profile.html',
        }

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for address, template in PostURLTests.templates_url_names.items():
            if (
                address == '/create/'
                or address == '/follow/'
                or address == f'/posts/{PostURLTests.post.id}/comment/'

            ):
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
            elif (
                address == f'/profile/{PostURLTests.user.username}/follow/'
                or address == f'/profile/{self.user.username}/unfollow/'
            ):
                response = self.authorized_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
            elif address == f'/posts/{PostURLTests.post.id}/edit/':
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
        for address, template in PostURLTests.templates_url_names.items():
            if (
               address == f'/profile/{PostURLTests.user.username}/follow/'
               or address == f'/profile/{PostURLTests.user.username}/unfollow/'
               ):
                response = self.authorized_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
            else:
                with self.subTest(address=address):
                    response = self.authorized_author.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexpecting_page(self):
        """Ошибка 404."""
        response = self.guest_client.get('/unexpecting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
