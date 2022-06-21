from django.test import TestCase, Client
from posts.models import Post, Group, Comment, Follow
from django.contrib.auth import get_user_model

User = get_user_model()
character_limit: int = 15


class PostModelTest(TestCase):
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

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:character_limit]
        self.assertEqual(expected_object_name, str(post))

        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

        comment = PostModelTest.comment
        expected_object_name = comment.text
        self.assertEqual(expected_object_name, str(comment))

        follow = PostModelTest.follow
        expected_object_name = 'Morpheus подписан на Neo'
        self.assertEqual(expected_object_name, str(follow))

    def test_verbose_name_post(self):
        """verbose_name в полях Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'pub_date': 'Дата публикации',
            'text': 'Текст поста',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_group(self):
        """verbose_name в полях Group совпадает с ожидаемым."""
        self.assertEqual(PostModelTest.group._meta.verbose_name, 'group')

    def test_verbose_comment(self):
        """verbose_name в полях Comment совпадает с ожидаемым."""
        comment = PostModelTest.comment
        field_verboses = {
            'post': 'Комментарий',
            'author': 'Автор комментария',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_follow(self):
        """verbose_name в полях Follow совпадает с ожидаемым."""
        follow = PostModelTest.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

        self.assertEqual(
            PostModelTest.comment._meta.get_field(
                'text'
            ).help_text, 'Введите текст комментария')
