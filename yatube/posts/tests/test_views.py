import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from http import HTTPStatus
from posts.models import Post, Group, Comment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
import os.path

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

POSTS_LIMIT: int = 10


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            ): 'posts/create_post.html',
        }

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

    def test_pages_namespace_uses_correct_template(self):
        """Проверка использования правильного темплейта"""
        cache.clear()
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_context(self):
        """Проверка контекста и функций"""
        cache.clear()
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

        posts_list = []
        for _ in range(15):
            post = Post(
                text='Агент Смит копирует сам себя',
                author=self.user,
                group=self.group,
                image=uploaded
            )
            posts_list.append(post)
        self.post = Post.objects.bulk_create(posts_list)

        response = self.guest_client.get(reverse('posts:index'))
        Page = response.context['page_obj']
        self.assertEqual(len(list(Page.object_list)), POSTS_LIMIT)
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, 'Агент Смит копирует сам себя')
        self.assertTrue(task_image_0)

        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostPagesTests.group.slug}'}
            )
        )
        Page = response.context['page_obj']
        group = Group.objects.get(slug=f'{PostPagesTests.group.slug}')
        self.assertEqual(
            Page.object_list,
            list(group.posts.select_related('author'))[:POSTS_LIMIT]
        )
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, 'Агент Смит копирует сам себя')
        self.assertTrue(task_image_0)

        response = self.guest_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        Page = response.context['page_obj']
        author = User.objects.get(username=f'{PostPagesTests.user.username}')
        self.assertEqual(
            Page.object_list,
            list(author.author.select_related('author'))[:POSTS_LIMIT]
        )
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, 'Агент Смит копирует сам себя')
        self.assertTrue(task_image_0)

        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            )
        )
        Page = response.context['post']
        self.assertEqual(Page, Post.objects.get(pk=PostPagesTests.post.id))
        first_object = response.context['post_list'][0]
        task_text_0 = first_object.text
        task_image_0 = first_object.image
        self.assertEqual(task_text_0, 'Агент Смит копирует сам себя')
        self.assertTrue(task_image_0)

        response = self.authorized_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTests.post.id}'}
            )
        )
        Page = response.context['form']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        post = response.context['post']
        post_id = Post.objects.get(pk=f'{PostPagesTests.post.id}')
        self.assertEqual(post, post_id)

        response = self.authorized_client.get(reverse('posts:post_create'))
        Page = response.context['form']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_image_in_folder(self):
        """Проверка наличия файлв изображения в папке"""
        self.assertTrue(os.path.isfile('MEDIA/posts/small.gif'))

    def test_new_post_location_in_index(self):
        """Проверка поста на главной"""
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        Page = response.context['page_obj'][0]
        post_id = Post.objects.get(pk=f'{self.post.id}')
        self.assertEqual(Page, post_id)

    def test_post_location_in_group_list(self):
        """Проверка поста на страницы группы"""
        new_group_plus = Group.objects.create(
            title='Нашедшие Мофриуса',
            slug='Matrix_noobie',
            description='Группа новобранцев Морфиуса',
        )

        new_post_plus = Post.objects.create(
            author=self.user,
            text='Я выпил красную таблетку',
            group=new_group_plus
        )
        response = self.authorized_author.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{new_group_plus.slug}'}
            )
        )
        Page = response.context['page_obj'][0]
        post_id = Post.objects.get(pk=f'{new_post_plus.id}')
        self.assertEqual(Page, post_id)

    def test_post_location_in_profile(self):
        """Проверка поста в профайле"""
        response = self.authorized_author.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        Page = response.context['page_obj'][0]
        post_id = Post.objects.get(pk=f'{self.post.id}')
        self.assertEqual(Page, post_id)

    def test_post_location_not_in_group_list(self):
        """Проверка отсутствия поста в другой группе"""
        new_group_2 = Group.objects.create(
            title='Защитники Зеона',
            slug='Matrix_solder',
            description='Группа особождения Морфиуса',
        )
        new_post_2 = Post.objects.create(
            author=self.user,
            text='Сегодня я спас Морфиуса и взорвал вертолет!',
            group=new_group_2
        )

        new_group_3 = Group.objects.create(
            title='Избранные',
            slug='GrandMatrix',
            description='Группа для избранных',
        )

        Post.objects.create(
            author=self.user,
            text='Теперь матрица в моей власти! Я уничтожу её!',
            group=new_group_3
        )
        response = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': f'{new_group_3.slug}'})
        )
        Page = response.context['page_obj']
        post_id = Post.objects.get(pk=f'{new_post_2.id}')
        self.assertNotEqual(Page, post_id)

    def test_cache_in_index(self):
        """Проверка работы кэша на главной"""
        response_1 = self.authorized_author.get('/')
        Page_1 = response_1.content

        post = Post.objects.get(pk=f'{self.post.id}')
        post.delete()

        response_2 = self.authorized_author.get('/')
        Page_2 = response_2.content

        self.assertEqual(Page_1, Page_2)

        cache.clear()

        response_3 = self.authorized_author.get('/')
        Page_3 = response_3.content

        self.assertNotEqual(Page_1, Page_3)

    def test_create_comment(self):
        """Проверка создания коментария"""
        post = Post.objects.get(pk=PostPagesTests.post.id)
        comment = Comment.objects.create(
            post=self.post,
            author=self.user_authorized,
            text='Нео ты избранный!',
        )
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            )
        )
        Page = response.context['comments'][0]
        comment = post.comments.select_related('author')[0]
        self.assertEqual(Page, comment)

        response_guest = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            )
        )
        self.assertNotIn('form', str(response_guest.content))

    def test_follow(self):
        """Проверка подписки"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        self.assertTrue(response.context.get('following'))

        response = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        Page = response.context['page_obj']
        post_id = Post.objects.get(pk=f'{self.post.id}')
        self.assertIn(post_id, list(Page))

        hater_authorized = User.objects.create_user(username='Hater')
        authorized_hater = Client()
        authorized_hater.force_login(hater_authorized)

        response = authorized_hater.get(reverse('posts:follow_index'))
        Page = response.context['page_obj']
        post_id = Post.objects.get(pk=f'{self.post.id}')
        self.assertNotIn(post_id, list(Page))

        response = self.guest_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        self.assertFalse(response.context.get('following'))

        response = self.guest_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': f'{PostPagesTests.user.username}'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
