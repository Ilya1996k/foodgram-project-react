from django.contrib.auth.models import AbstractUser
from django.db import models


class Users(AbstractUser):
    """Модель для пользователей"""
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=254,
        unique=True,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
    )
    is_active = models.BooleanField(
        verbose_name="Активация",
        default=True,)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscribers(models.Model):
    """Модель для подписчиков."""
    user = models.ForeignKey(
        Users,
        related_name="subscriptions",
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        Users,
        related_name="subscribers",
        verbose_name="Автор",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("author", "user"),
                name="\nRepeat subscription\n",
            ),
            models.CheckConstraint(
                check=~models.Q(
                    author=models.F("user")
                ),
                name="\nNo self sibscription\n"
            ),
        )

    def __str__(self):
        return self.user.username
