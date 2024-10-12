from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Имя пользователя'
    )

    email = models.EmailField(
        unique=True,
        verbose_name='Адрес электронной почты'
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
        )

    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия')

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор для подписки',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = (
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscribe'
            ),
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='subscription_unique'
            )
        )

    def __str__(self):
        return f'{self.user} {self.author}'
