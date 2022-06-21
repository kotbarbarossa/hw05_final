import shutil
import tempfile

from ..models import Post, Group, User, Comment
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author = self.user
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.user_authorized = User.objects.create_user(username='Morpheus')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_authorized_client_create_post(self):
        """Валидная форма создает запись, авторизированный пользователь."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Фото секретных кодов Зеона',
            'group': '',
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostCreateFormTests.user.username}'}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Фото секретных кодов Зеона',
            ).exists()
        )

    def test_guest_client_create_post(self):
        """Валидная форма создает запись, неавторизированный пользователь."""
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_author_edit_post(self):
        """Валидная форма изменяет запись, автор записи."""
        posts_count = Post.objects.count()

        Post.objects.update(
            author=self.user,
            text='Я пошел за кроликом и встретил Тринити',
            id=self.post.id
        )

        form_data = {
            'text': 'Я пошел за кроликом и встретил Тринити',
            'group': ''
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )

        self.assertTrue(
            Post.objects.filter(
                text='Я пошел за кроликом и встретил Тринити',
            ).exists()
        )

        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_client_edit_post(self):
        """Валидная форма изменяет запись, неавторизированный пользователь."""
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_client_edit_post(self):
        """Валидная форма изменяет запись, авторизированный пользователь."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_client_comment(self):
        """Валидная форма создает коммент, авторизированный пользователь."""
        form_data = {
            'text': 'Тестовый комментик',
        }
        self.authorized_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.id}'}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data.get('text'),
            ).exists()
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        comment_from_response = response.context.get('comments')[0]
        comment_from_ORM = Comment.objects.get(pk=1)
        self.assertEqual(comment_from_response, comment_from_ORM)

    def test_guest_client_create_commet(self):
        """Редирект при попытке создать невторизованный комментарий."""
        """Неавторизированный пользователь."""
        response = self.guest_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
