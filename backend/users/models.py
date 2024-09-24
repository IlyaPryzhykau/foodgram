from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Пользовательская модель, расширяющая стандартную модель AbstractUser.
    """
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта'
    )
    avatar = models.ImageField(
        upload_to='avatar/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    first_name = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        verbose_name='Фамилия'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
